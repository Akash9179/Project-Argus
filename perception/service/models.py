"""
Core data models for the perception pipeline.

Frame: The unit of data flowing from Layer 1 (Ingest) to Layer 2 (Perceive).
SourceStatus: Health/state of each camera source.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import numpy as np
import uuid


class SourceState(str, Enum):
    CONNECTING = "connecting"
    ONLINE = "online"
    DEGRADED = "degraded"     # connected but dropping frames / high latency
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class CaptureMeta:
    """Metadata about how the frame was captured."""
    protocol: str             # rtsp, usb, file, mjpeg, screen
    codec: str | None = None  # h264, h265, mjpeg
    latency_ms: float = 0.0   # capture-to-Frame creation time
    dropped_frames: int = 0   # frames skipped since last Frame
    fps_measured: float = 0.0  # actual FPS being achieved


@dataclass
class Frame:
    """
    The fundamental unit flowing between Layer 1 and Layer 2.

    Layer 2 never knows or cares what camera protocol produced this.
    It just gets pixels, a timestamp, and metadata.
    """
    source_id: uuid.UUID
    sequence: int              # monotonic counter per source
    timestamp: datetime        # capture time, UTC
    image: np.ndarray          # raw pixels, BGR, uint8, shape (H, W, 3)
    width: int
    height: int
    channels: int = 3
    capture_meta: CaptureMeta = field(default_factory=lambda: CaptureMeta(protocol="unknown"))

    @property
    def shape(self) -> tuple[int, int, int]:
        return (self.height, self.width, self.channels)


@dataclass
class SourceStatus:
    """Real-time health status of a source adapter."""
    source_id: uuid.UUID
    state: SourceState = SourceState.OFFLINE
    fps_current: float = 0.0
    fps_target: float = 10.0
    frames_total: int = 0
    frames_dropped: int = 0
    last_frame_at: datetime | None = None
    uptime_s: float = 0.0
    error: str | None = None
    reconnect_count: int = 0
    latency_ms: float = 0.0

    def to_dict(self) -> dict:
        """Serialize for Redis / WebSocket / API."""
        return {
            "source_id": str(self.source_id),
            "state": self.state.value,
            "fps_current": round(self.fps_current, 1),
            "fps_target": self.fps_target,
            "frames_total": self.frames_total,
            "frames_dropped": self.frames_dropped,
            "last_frame_at": self.last_frame_at.isoformat() if self.last_frame_at else None,
            "uptime_s": round(self.uptime_s, 1),
            "error": self.error,
            "reconnect_count": self.reconnect_count,
            "latency_ms": round(self.latency_ms, 1),
        }
