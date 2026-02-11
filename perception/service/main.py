"""
Argus C2 — Perception Service

This service handles:
  - Layer 1 (Ingest): Camera/sensor source management and frame capture
  - Layer 2 (Perceive): AI inference pipeline (YOLO26s, etc.) — future
  - MJPEG streaming: Serves live video feeds to the frontend
  - Status reporting: Source health via WebSocket

Runs as a separate process from the Backend API.
Communicates via Redis pub/sub and shared PostgreSQL.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import cv2
import json
import logging
import uuid

from service.config import get_settings
from service.ingest.manager import SourceManager

# ─── Logging ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-20s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("argus.perception")

# ─── Global State ────────────────────────────────────────

settings = get_settings()
source_manager = SourceManager(frame_queue_size=settings.frame_queue_size)

# Store latest frame per source for MJPEG streaming
latest_frames: dict[uuid.UUID, bytes] = {}  # source_id → JPEG bytes

# Task that reads from frame queue and updates latest_frames
frame_distributor_task: asyncio.Task | None = None


async def frame_distributor():
    """
    Reads frames from the unified queue and:
    1. Stores latest JPEG for MJPEG streaming
    2. (Future) Feeds frames to Layer 2 AI pipeline
    """
    logger.info("Frame distributor started")
    while True:
        try:
            frame = await source_manager.frame_queue.get()

            # Encode frame as JPEG for MJPEG streaming
            _, jpeg = cv2.imencode(
                ".jpg", frame.image, [cv2.IMWRITE_JPEG_QUALITY, 80]
            )
            latest_frames[frame.source_id] = jpeg.tobytes()

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Frame distributor error: {e}")
            await asyncio.sleep(0.01)


# ─── App Lifecycle ───────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global frame_distributor_task

    print("=" * 50)
    print("  ARGUS C2 — Perception Service")
    print("=" * 50)

    # Start frame distributor
    frame_distributor_task = asyncio.create_task(frame_distributor())
    print("  ✓ Frame distributor started")
    print(f"  ✓ Server on {settings.perception_host}:{settings.perception_port}")
    print("=" * 50)

    yield

    # Shutdown
    logger.info("Shutting down perception service...")
    await source_manager.stop_all()
    if frame_distributor_task:
        frame_distributor_task.cancel()
        try:
            await frame_distributor_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Argus C2 Perception Service",
    description="Camera ingestion, MJPEG streaming, AI pipeline",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permissive for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Schemas ─────────────────────────────────────────────

class AddSourceRequest(BaseModel):
    source_id: uuid.UUID
    name: str
    source_type: str | None = None  # auto-detect if None
    uri: str
    target_fps: int = 10
    reconnect_attempts: int = -1
    reconnect_delay_s: float = 5.0
    timeout_s: float = 10.0


class SourceStatusBrief(BaseModel):
    source_id: str
    name: str
    state: str
    fps: float
    frames: int
    error: str | None


# ─── Source Management ───────────────────────────────────

@app.post("/sources/start")
async def start_source(req: AddSourceRequest):
    """Add and start capturing from a source."""
    success = await source_manager.add_source(
        source_id=req.source_id,
        name=req.name,
        source_type=req.source_type,
        uri=req.uri,
        target_fps=req.target_fps,
        reconnect_attempts=req.reconnect_attempts,
        reconnect_delay_s=req.reconnect_delay_s,
        timeout_s=req.timeout_s,
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to start source")
    return {"status": "started", "source_id": str(req.source_id)}


@app.post("/sources/{source_id}/stop")
async def stop_source(source_id: uuid.UUID):
    """Stop and remove a source."""
    success = await source_manager.remove_source(source_id)
    if not success:
        raise HTTPException(status_code=404, detail="Source not found")
    # Clean up cached frame
    latest_frames.pop(source_id, None)
    return {"status": "stopped", "source_id": str(source_id)}


@app.get("/sources/status")
async def all_source_status():
    """Get status of all active sources."""
    statuses = source_manager.get_all_status()
    return {
        "total": source_manager.source_count,
        "online": source_manager.online_count,
        "sources": {str(sid): s.to_dict() for sid, s in statuses.items()},
    }


@app.get("/sources/{source_id}/status")
async def source_status(source_id: uuid.UUID):
    """Get status of a specific source."""
    status = source_manager.get_status(source_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return status.to_dict()


# ─── MJPEG Streaming ────────────────────────────────────

async def mjpeg_generator(source_id: uuid.UUID):
    """Generate MJPEG stream from latest frames."""
    target_interval = 1.0 / 15  # 15 FPS for stream output

    while True:
        jpeg_bytes = latest_frames.get(source_id)
        if jpeg_bytes:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + jpeg_bytes + b"\r\n"
            )
        await asyncio.sleep(target_interval)


@app.get("/stream/{source_id}")
async def video_stream(source_id: uuid.UUID):
    """
    MJPEG video stream for a source.

    Usage in browser/frontend:
      <img src="http://localhost:8100/stream/{source_id}" />

    This is the simplest way to get live video into any web UI.
    No WebSocket complexity, works in any <img> tag.
    """
    if source_id not in source_manager._adapters:
        raise HTTPException(status_code=404, detail="Source not found or not started")

    return StreamingResponse(
        mjpeg_generator(source_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


# ─── Status WebSocket ───────────────────────────────────

@app.websocket("/ws/status")
async def status_websocket(websocket: WebSocket):
    """
    WebSocket that pushes source status updates every 2 seconds.
    Frontend connects here for real-time health indicators.
    """
    await websocket.accept()
    logger.info("Status WebSocket connected")

    try:
        while True:
            statuses = source_manager.get_all_status()
            payload = {
                "type": "source_status",
                "total": source_manager.source_count,
                "online": source_manager.online_count,
                "sources": {str(sid): s.to_dict() for sid, s in statuses.items()},
            }
            await websocket.send_json(payload)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        logger.info("Status WebSocket disconnected")
    except Exception as e:
        logger.error(f"Status WebSocket error: {e}")


# ─── Health ──────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "argus-perception",
        "sources_total": source_manager.source_count,
        "sources_online": source_manager.online_count,
    }
