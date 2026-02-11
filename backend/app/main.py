from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.api.sources import router as sources_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    print("=" * 50)
    print("  ARGUS C2 — Backend API")
    print("=" * 50)
    await init_db()
    print("  ✓ Database initialized")
    print(f"  ✓ Server running on {settings.backend_host}:{settings.backend_port}")
    print("=" * 50)
    yield
    # Shutdown
    print("  Argus Backend shutting down...")


app = FastAPI(
    title="Argus C2 API",
    description="Multi-Domain Autonomous Intelligence Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(sources_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "argus-backend"}
