from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "Argus C2 Backend"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://argus:argus_dev_2026@localhost:5432/argus"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # Perception service
    perception_url: str = "http://localhost:8100"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = {"env_file": "../.env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
