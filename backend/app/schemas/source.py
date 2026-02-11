import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.source import SourceType, SourceDomain, SourceState


# ─── Location ───────────────────────────────────────────

class SourceLocation(BaseModel):
    lat: float | None = None
    lon: float | None = None
    facility_x: float | None = Field(None, ge=0, le=100, description="X position on map (0-100%)")
    facility_y: float | None = Field(None, ge=0, le=100, description="Y position on map (0-100%)")
    fov_angle: float | None = Field(None, ge=0, lt=360, description="FOV direction in degrees")
    fov_width: float | None = Field(None, ge=1, le=180, description="FOV cone width in degrees")


# ─── Create / Update ────────────────────────────────────

class SourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["Entry Gate"])
    type: SourceType
    uri: str = Field(..., min_length=1, max_length=500, examples=["rtsp://192.168.1.100/stream1"])
    enabled: bool = True

    # Capture
    target_fps: int = Field(10, ge=1, le=60)
    resolution_w: int | None = Field(None, ge=1)
    resolution_h: int | None = Field(None, ge=1)

    # Connection
    reconnect_attempts: int = Field(-1, ge=-1)
    reconnect_delay_s: float = Field(5.0, ge=0.5, le=60.0)
    timeout_s: float = Field(10.0, ge=1.0, le=60.0)

    # Credentials
    username: str | None = None
    password: str | None = None

    # Spatial
    location: SourceLocation | None = None

    # Domain
    domain: SourceDomain = SourceDomain.LAND
    zone_id: uuid.UUID | None = None

    # Hardware
    vendor: str | None = None
    model: str | None = None


class SourceUpdate(BaseModel):
    """All fields optional for PATCH updates."""
    name: str | None = Field(None, min_length=1, max_length=100)
    type: SourceType | None = None
    uri: str | None = Field(None, min_length=1, max_length=500)
    enabled: bool | None = None
    target_fps: int | None = Field(None, ge=1, le=60)
    resolution_w: int | None = None
    resolution_h: int | None = None
    reconnect_attempts: int | None = Field(None, ge=-1)
    reconnect_delay_s: float | None = Field(None, ge=0.5, le=60.0)
    timeout_s: float | None = Field(None, ge=1.0, le=60.0)
    username: str | None = None
    password: str | None = None
    location: SourceLocation | None = None
    domain: SourceDomain | None = None
    zone_id: uuid.UUID | None = None
    vendor: str | None = None
    model: str | None = None


# ─── Response ────────────────────────────────────────────

class SourceResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: SourceType
    uri: str
    enabled: bool

    target_fps: int
    native_fps: int | None
    resolution_w: int | None
    resolution_h: int | None

    reconnect_attempts: int
    reconnect_delay_s: float
    timeout_s: float

    username: str | None
    # password intentionally excluded from response

    location: SourceLocation | None
    domain: SourceDomain
    zone_id: uuid.UUID | None

    vendor: str | None
    model: str | None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Status (real-time, from perception service) ────────

class SourceStatusResponse(BaseModel):
    source_id: uuid.UUID
    state: SourceState
    fps_current: float = 0.0
    fps_target: float = 10.0
    frames_total: int = 0
    frames_dropped: int = 0
    last_frame_at: datetime | None = None
    uptime_s: float = 0.0
    error: str | None = None
    reconnect_count: int = 0
    latency_ms: float = 0.0


# ─── List response ──────────────────────────────────────

class SourceListResponse(BaseModel):
    sources: list[SourceResponse]
    total: int
