"""
FileAdapter — Plays back video files as if they were live camera feeds.

URI format: "/path/to/video.mp4" or "path/to/video.avi"
Supports: MP4, AVI, MKV, MOV, WEBM

Features:
  - Loops by default (for continuous demo)
  - Respects target_fps for playback speed
  - Can serve pre-recorded surveillance footage as realistic demo data
"""

import asyncio
import cv2
import numpy as np
import os

from service.ingest.base import SourceAdapter


class FileAdapter(SourceAdapter):
    """Adapter for video file playback."""

    def __init__(self, loop_playback: bool = True, **kwargs):
        super().__init__(**kwargs)
        self._cap: cv2.VideoCapture | None = None
        self._loop = loop_playback
        self._file_fps: float | None = None
        self._total_frames: int = 0

    @property
    def protocol(self) -> str:
        return "file"

    async def _connect(self) -> bool:
        if not os.path.isfile(self.uri):
            self._last_error = f"File not found: {self.uri}"
            return False

        loop = asyncio.get_event_loop()
        self._cap = await loop.run_in_executor(None, cv2.VideoCapture, self.uri)

        if not self._cap.isOpened():
            self._cap = None
            return False

        self._file_fps = self._cap.get(cv2.CAP_PROP_FPS)
        self._total_frames = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))

        return True

    async def _read_frame(self) -> tuple[bool, np.ndarray | None]:
        if self._cap is None:
            return False, None

        loop = asyncio.get_event_loop()
        ret, frame = await loop.run_in_executor(None, self._cap.read)

        if not ret or frame is None:
            if self._loop:
                # Seek back to start
                self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = await loop.run_in_executor(None, self._cap.read)
                if not ret:
                    self._connected = False
                    return False, None
                return True, frame
            else:
                self._connected = False
                return False, None

        return True, frame

    async def _disconnect(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
