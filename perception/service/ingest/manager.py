"""
SourceManager — Orchestrates all camera source adapters.

Responsibilities:
  - Creates appropriate adapter based on source type/URI
  - Manages adapter lifecycle (start, stop, reconnect)
  - Provides unified frame queue for Layer 2
  - Reports status for all sources
  - Supports hot-add and hot-remove of sources
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from service.models import Frame, SourceStatus, SourceState
from service.ingest.base import SourceAdapter
from service.ingest.webcam import WebcamAdapter
from service.ingest.file import FileAdapter
from service.ingest.rtsp import RTSPAdapter
from service.ingest.mjpeg import MJPEGAdapter
from service.config import get_settings

logger = logging.getLogger("argus.ingest")

# Map source types to adapter classes
ADAPTER_MAP: dict[str, type[SourceAdapter]] = {
    "usb": WebcamAdapter,
    "file": FileAdapter,
    "rtsp": RTSPAdapter,
    "mjpeg": MJPEGAdapter,
    "onvif": RTSPAdapter,  # ONVIF discovery wraps RTSP under the hood
}


def detect_source_type(uri: str) -> str:
    """Auto-detect source type from URI."""
    uri_lower = uri.strip().lower()

    if uri_lower.startswith("rtsp://"):
        return "rtsp"
    elif uri_lower.startswith("http://") or uri_lower.startswith("https://"):
        # Check if it looks like an MJPEG stream
        if any(ext in uri_lower for ext in [".mjpg", ".mjpeg", "mjpeg", "/video"]):
            return "mjpeg"
        return "mjpeg"  # Default HTTP to MJPEG
    elif uri_lower.isdigit() or uri_lower.startswith("/dev/video"):
        return "usb"
    elif any(uri_lower.endswith(ext) for ext in [".mp4", ".avi", ".mkv", ".mov", ".webm"]):
        return "file"
    else:
        # Try as file path
        return "file"


class SourceManager:
    """Manages all camera source adapters and provides a unified frame queue."""

    def __init__(self, frame_queue_size: int = 30):
        settings = get_settings()
        self._adapters: dict[uuid.UUID, SourceAdapter] = {}
        self._tasks: dict[uuid.UUID, asyncio.Task] = {}
        self._frame_queue = asyncio.Queue(maxsize=frame_queue_size)
        self._running = False

    @property
    def frame_queue(self) -> asyncio.Queue:
        """The unified frame queue that Layer 2 consumes from."""
        return self._frame_queue

    def _create_adapter(
        self,
        source_id: uuid.UUID,
        name: str,
        source_type: str,
        uri: str,
        target_fps: int = 10,
        reconnect_attempts: int = -1,
        reconnect_delay_s: float = 5.0,
        timeout_s: float = 10.0,
        **kwargs,
    ) -> SourceAdapter:
        """Create the appropriate adapter for a source type."""
        adapter_cls = ADAPTER_MAP.get(source_type)
        if adapter_cls is None:
            raise ValueError(f"Unsupported source type: {source_type}")

        return adapter_cls(
            source_id=source_id,
            name=name,
            uri=uri,
            target_fps=target_fps,
            reconnect_attempts=reconnect_attempts,
            reconnect_delay_s=reconnect_delay_s,
            timeout_s=timeout_s,
            **kwargs,
        )

    async def add_source(
        self,
        source_id: uuid.UUID,
        name: str,
        source_type: str | None,
        uri: str,
        target_fps: int = 10,
        reconnect_attempts: int = -1,
        reconnect_delay_s: float = 5.0,
        timeout_s: float = 10.0,
    ) -> bool:
        """
        Add and start a new source. Hot-pluggable — can be called while running.
        If source_type is None, auto-detects from URI.
        """
        if source_id in self._adapters:
            logger.warning(f"Source {source_id} already exists, removing first")
            await self.remove_source(source_id)

        if source_type is None:
            source_type = detect_source_type(uri)
            logger.info(f"Auto-detected source type: {source_type} for URI: {uri}")

        try:
            adapter = self._create_adapter(
                source_id=source_id,
                name=name,
                source_type=source_type,
                uri=uri,
                target_fps=target_fps,
                reconnect_attempts=reconnect_attempts,
                reconnect_delay_s=reconnect_delay_s,
                timeout_s=timeout_s,
            )
        except ValueError as e:
            logger.error(f"Failed to create adapter: {e}")
            return False

        self._adapters[source_id] = adapter

        # Start capture task
        task = asyncio.create_task(
            adapter.run(self._frame_queue),
            name=f"source-{name}",
        )
        self._tasks[source_id] = task

        logger.info(f"Added source: {name} ({source_type}:{uri})")
        return True

    async def remove_source(self, source_id: uuid.UUID) -> bool:
        """Stop and remove a source. Hot-removable."""
        adapter = self._adapters.pop(source_id, None)
        task = self._tasks.pop(source_id, None)

        if adapter is None:
            return False

        await adapter.disconnect()
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        logger.info(f"Removed source: {adapter.name}")
        return True

    def get_status(self, source_id: uuid.UUID) -> SourceStatus | None:
        """Get current status of a specific source."""
        adapter = self._adapters.get(source_id)
        return adapter.status if adapter else None

    def get_all_status(self) -> dict[uuid.UUID, SourceStatus]:
        """Get status of all sources."""
        return {sid: adapter.status for sid, adapter in self._adapters.items()}

    @property
    def source_count(self) -> int:
        return len(self._adapters)

    @property
    def online_count(self) -> int:
        return sum(
            1
            for a in self._adapters.values()
            if a.status.state in (SourceState.ONLINE, SourceState.DEGRADED)
        )

    async def stop_all(self) -> None:
        """Stop all sources gracefully."""
        logger.info("Stopping all sources...")
        source_ids = list(self._adapters.keys())
        for sid in source_ids:
            await self.remove_source(sid)
        logger.info("All sources stopped")
