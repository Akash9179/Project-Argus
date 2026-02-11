from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Server
    perception_host: str = "0.0.0.0"
    perception_port: int = 8100

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Backend API (to fetch source configs)
    backend_url: str = "http://localhost:8000"

    # Defaults
    default_target_fps: int = 10
    max_sources: int = 10
    frame_queue_size: int = 30  # frames buffered per source

    # YOLO (Layer 2 — not used yet)
    yolo_model: str = "yolo26s.pt"
    yolo_device: str = "mps"
    yolo_confidence: float = 0.5

    model_config = {"env_file": "../.env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
