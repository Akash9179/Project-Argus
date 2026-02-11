"""
MJPEGAdapter — Captures frames from HTTP MJPEG streams.

URI format: "http://192.168.1.100:8080/mjpeg" or "http://cam:8080/video.mjpg"

Many budget cameras and some phone apps (IP Webcam for Android)
expose MJPEG over HTTP. OpenCV handles this natively.
"""

import asyncio
import cv2
import numpy as np

from service.ingest.base import SourceAdapter


class MJPEGAdapter(SourceAdapter):
    """Adapter for HTTP MJPEG streams."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cap: cv2.VideoCapture | None = None

    @property
    def protocol(self) -> str:
        return "mjpeg"

    async def _connect(self) -> bool:
        loop = asyncio.get_event_loop()
        self._cap = await loop.run_in_executor(None, cv2.VideoCapture, self.uri)

        if not self._cap.isOpened():
            self._cap = None
            return False

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
