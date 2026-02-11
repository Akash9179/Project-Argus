"""
SourceAdapter — Abstract base class for all camera/sensor ingestion.

This is the vendor-neutral abstraction layer. Every camera protocol
(RTSP, USB, MJPEG, file, etc.) implements this interface. Layer 2
never sees protocol details — it only receives Frame objects.

The adapter handles:
  - Connection lifecycle (connect, disconnect, reconnect)
  - Frame capture at target FPS
  - Health monitoring and status reporting
  - Graceful degradation on errors
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import asyncio
import time
import uuid
import logging

from service.models import Frame, CaptureMeta, SourceStatus, SourceState

logger = logging.getLogger("argus.ingest")


class SourceAdapter(ABC):
    """
    Base class for all camera/sensor adapters.

    Subclasses must implement:
      - _connect()    : Establish connection to the source
      - _read_frame() : Capture a single raw frame
      - _disconnect()  : Clean up resources
      - protocol       : String identifying the protocol (e.g., "rtsp", "usb")
    """

    def __init__(
        self,
        source_id: uuid.UUID,
        name: str,
        uri: str,
        target_fps: int = 10,
        reconnect_attempts: int = -1,  # -1 = infinite
        reconnect_delay_s: float = 5.0,
        timeout_s: float = 10.0,
    ):
        self.source_id = source_id
        self.name = name
        self.uri = uri
        self.target_fps = target_fps
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_delay_s = reconnect_delay_s
        self.timeout_s = timeout_s

        # State
        self._connected = False
        self._running = False
        self._sequence = 0
        self._connect_time: float | None = None

        # Metrics
        self._frames_total = 0
        self._frames_dropped = 0
        self._reconnect_count = 0
        self._last_frame_time: float | None = None
        self._fps_samples: list[float] = []
        self._last_error: str | None = None

    @property
    @abstractmethod
    def protocol(self) -> str:
        """Protocol identifier (e.g., 'rtsp', 'usb', 'file')."""
        ...

    @abstractmethod
    async def _connect(self) -> bool:
        """
        Establish connection to the source.
        Returns True on success, False on failure.
        Should set any internal capture objects.
        """
        ...

    @abstractmethod
    async def _read_frame(self) -> tuple[bool, "np.ndarray | None"]:
        """
        Read a single frame from the source.
        Returns (success: bool, image: numpy array or None).
        Image should be BGR uint8 format.
        """
        ...

    @abstractmethod
    async def _disconnect(self) -> None:
        """Release all resources for this source."""
        ...

    # ─── Public API ──────────────────────────────────────

    async def connect(self) -> bool:
        """Connect to the source with error handling."""
        try:
            logger.info(f"[{self.name}] Connecting to {self.uri}")
            success = await self._connect()
            if success:
                self._connected = True
                self._connect_time = time.monotonic()
                self._last_error = None
                logger.info(f"[{self.name}] Connected successfully")
            else:
                self._last_error = "Connection failed"
                logger.warning(f"[{self.name}] Connection failed")
            return success
        except Exception as e:
            self._connected = False
            self._last_error = str(e)
            logger.error(f"[{self.name}] Connection error: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect and clean up."""
        self._running = False
        self._connected = False
        try:
            await self._disconnect()
            logger.info(f"[{self.name}] Disconnected")
        except Exception as e:
            logger.error(f"[{self.name}] Disconnect error: {e}")

    async def read(self) -> Frame | None:
        """
        Read one frame, wrapped in the Frame dataclass.
        Returns None if read fails.
        """
        if not self._connected:
            return None

        t0 = time.monotonic()

        try:
            success, image = await self._read_frame()
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"[{self.name}] Read error: {e}")
            return None

        if not success or image is None:
            self._frames_dropped += 1
            return None

        elapsed_ms = (time.monotonic() - t0) * 1000
        now = time.monotonic()

        # FPS tracking
        if self._last_frame_time:
            dt = now - self._last_frame_time
            if dt > 0:
                self._fps_samples.append(1.0 / dt)
                if len(self._fps_samples) > 30:
                    self._fps_samples.pop(0)
        self._last_frame_time = now

        self._sequence += 1
        self._frames_total += 1

        h, w = image.shape[:2]
        channels = image.shape[2] if len(image.shape) > 2 else 1

        return Frame(
            source_id=self.source_id,
            sequence=self._sequence,
            timestamp=datetime.now(timezone.utc),
            image=image,
            width=w,
            height=h,
            channels=channels,
            capture_meta=CaptureMeta(
                protocol=self.protocol,
                latency_ms=elapsed_ms,
                dropped_frames=self._frames_dropped,
                fps_measured=self.current_fps,
            ),
        )

    async def run(self, frame_queue: asyncio.Queue) -> None:
        """
        Main capture loop. Reads frames at target_fps and puts them on the queue.
        Handles reconnection on failure.
        """
        self._running = True
        frame_interval = 1.0 / self.target_fps

        while self._running:
            # Connect if needed
            if not self._connected:
                success = await self._reconnect()
                if not success:
                    break  # exhausted reconnect attempts

            # Capture frame
            t0 = time.monotonic()
            frame = await self.read()

            if frame is not None:
                try:
                    # Non-blocking put — drop frame if queue full
                    frame_queue.put_nowait(frame)
                except asyncio.QueueFull:
                    self._frames_dropped += 1
            else:
                # Read failed — might need reconnect
                if not self._connected:
                    continue

            # Throttle to target FPS
            elapsed = time.monotonic() - t0
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

    async def _reconnect(self) -> bool:
        """Attempt to reconnect with backoff."""
        attempts = 0
        while self._running:
            if self.reconnect_attempts >= 0 and attempts >= self.reconnect_attempts:
                logger.error(f"[{self.name}] Exhausted {self.reconnect_attempts} reconnect attempts")
                return False

            attempts += 1
            self._reconnect_count += 1
            logger.info(f"[{self.name}] Reconnecting (attempt {attempts})...")

            if await self.connect():
                return True

            await asyncio.sleep(self.reconnect_delay_s)

        return False

    # ─── Properties ──────────────────────────────────────

    @property
    def current_fps(self) -> float:
        if not self._fps_samples:
            return 0.0
        return sum(self._fps_samples) / len(self._fps_samples)

    @property
    def status(self) -> SourceStatus:
        if not self._connected:
            state = SourceState.ERROR if self._last_error else SourceState.OFFLINE
        elif self.current_fps < self.target_fps * 0.5:
            state = SourceState.DEGRADED
        else:
            state = SourceState.ONLINE

        uptime = 0.0
        if self._connect_time:
            uptime = time.monotonic() - self._connect_time

        return SourceStatus(
            source_id=self.source_id,
            state=state,
            fps_current=self.current_fps,
            fps_target=float(self.target_fps),
            frames_total=self._frames_total,
            frames_dropped=self._frames_dropped,
            last_frame_at=datetime.now(timezone.utc) if self._last_frame_time else None,
            uptime_s=uptime,
            error=self._last_error,
            reconnect_count=self._reconnect_count,
            latency_ms=(time.monotonic() - self._last_frame_time) * 1000
            if self._last_frame_time
            else 0.0,
        )
