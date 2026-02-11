"""
RTSPAdapter — Captures frames from RTSP streams (IP cameras).

URI format: "rtsp://user:pass@192.168.1.100:554/stream1"

This is the most common protocol for enterprise security cameras.
Hikvision, Dahua, Axis, Bosch, and most other vendors expose RTSP.

Uses OpenCV with FFMPEG backend. For production, GStreamer would be
preferred for better reconnection handling and hardware decode.
"""

import asyncio
import cv2
import numpy as np
import os

from service.ingest.base import SourceAdapter


class RTSPAdapter(SourceAdapter):
    """Adapter for RTSP IP camera streams."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cap: cv2.VideoCapture | None = None

    @property
    def protocol(self) -> str:
        return "rtsp"

    def _build_uri(self) -> str:
        """Build RTSP URI, injecting credentials if provided separately."""
        uri = self.uri
        # If credentials are provided separately and not already in URI
        if self.username and "://" in uri and "@" not in uri:
            # rtsp://host:port/path → rtsp://user:pass@host:port/path
            scheme, rest = uri.split("://", 1)
            cred = self.username
            if hasattr(self, 'password') and self.password:
                cred += f":{self.password}"
            uri = f"{scheme}://{cred}@{rest}"
        return uri

    async def _connect(self) -> bool:
        uri = self._build_uri()

        # Set FFMPEG options for lower latency
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
            "rtsp_transport;tcp|fflags;nobuffer|flags;low_delay"
        )

        loop = asyncio.get_event_loop()
        self._cap = await loop.run_in_executor(
            None, lambda: cv2.VideoCapture(uri, cv2.CAP_FFMPEG)
        )

        if not self._cap.isOpened():
            self._cap = None
            return False

        # Set buffer size to 1 for lowest latency
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        return True

    async def _read_frame(self) -> tuple[bool, np.ndarray | None]:
        if self._cap is None:
            return False, None

        loop = asyncio.get_event_loop()
        ret, frame = await loop.run_in_executor(None, self._cap.read)

        if not ret or frame is None:
            self._connected = False
            return False, None

        return True, frame

    async def _disconnect(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
