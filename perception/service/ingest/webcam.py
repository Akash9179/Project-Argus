"""
WebcamAdapter — Captures frames from USB/UVC cameras (built-in webcam, external USB cameras).

URI format: "0" or "1" (device index) or "/dev/video0" (Linux device path)
"""

import asyncio
import cv2
import numpy as np
import uuid

from service.ingest.base import SourceAdapter


class WebcamAdapter(SourceAdapter):
    """Adapter for USB/UVC cameras via OpenCV."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cap: cv2.VideoCapture | None = None
        self._device_index = self._parse_device(self.uri)

    @property
    def protocol(self) -> str:
        return "usb"

    def _parse_device(self, uri: str) -> int:
        """Parse URI to device index. '0', '1', '/dev/video0' etc."""
        uri = uri.strip()
        if uri.startswith("/dev/video"):
            try:
                return int(uri.replace("/dev/video", ""))
            except ValueError:
                return 0
        try:
            return int(uri)
        except ValueError:
            return 0

    async def _connect(self) -> bool:
        # OpenCV VideoCapture is blocking, run in thread
        loop = asyncio.get_event_loop()
        self._cap = await loop.run_in_executor(
            None, cv2.VideoCapture, self._device_index
        )
        if not self._cap.isOpened():
            self._cap = None
            return False

        # Try to set resolution if specified
        # (OpenCV respects these as hints, camera may ignore)
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
