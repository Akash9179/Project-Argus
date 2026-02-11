import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, Float, Enum as SAEnum, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import enum


class SourceType(str, enum.Enum):
    RTSP = "rtsp"
    ONVIF = "onvif"
    USB = "usb"
    FILE = "file"
    MJPEG = "mjpeg"
    SCREEN = "screen"


class SourceDomain(str, enum.Enum):
    AIR = "air"
    LAND = "land"
    WATER = "water"


class SourceState(str, enum.Enum):
    CONNECTING = "connecting"
    ONLINE = "online"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    ERROR = "error"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[SourceType] = mapped_column(SAEnum(SourceType), nullable=False)
    uri: Mapped[str] = mapped_column(String(500), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Capture settings
    target_fps: Mapped[int] = mapped_column(Integer, default=10)
    native_fps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resolution_w: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resolution_h: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Connection
    reconnect_attempts: Mapped[int] = mapped_column(Integer, default=-1)  # -1 = infinite
    reconnect_delay_s: Mapped[float] = mapped_column(Float, default=5.0)
    timeout_s: Mapped[float] = mapped_column(Float, default=10.0)

    # Credentials (encrypted in production)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    password: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Spatial context
    location: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Expected shape: {lat, lon, facility_x, facility_y, fov_angle, fov_width}

    # Domain
    domain: Mapped[SourceDomain] = mapped_column(
        SAEnum(SourceDomain), default=SourceDomain.LAND
    )
    zone_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Hardware info
    vendor: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Source {self.name} ({self.type.value}:{self.uri})>"
