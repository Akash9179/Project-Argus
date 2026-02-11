# Project Argus — Multi-Domain Autonomous Intelligence Platform

**Argus C2** is a vendor-neutral command & control platform that unifies air, land, and water surveillance into a single intelligence system.

## Architecture

```
Layer 1: INGEST     → Camera/sensor ingestion (vendor-neutral adapters)
Layer 2: PERCEIVE   → Three-tier AI (YOLO26s → YOLOE-26 → Cosmos Reason 2)
Layer 3: NORMALIZE  → Ontology engine (unified semantic schema)
Layer 4: STORE      → Vector DB + Knowledge Graph + Memory
Layer 5: DECIDE     → LLM planner / policy brain
Layer 6: ACT        → Alerts, Q&A, summarization, autonomous action
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| **Backend API** | 8000 | REST API, WebSocket, business logic |
| **Perception** | 8100 | Camera ingestion, MJPEG streaming, AI pipeline |
| **Frontend** | 5173 | React dashboard (Vite dev server) |
| **PostgreSQL** | 5432 | Persistent storage |
| **Redis** | 6379 | Pub/sub, caching, real-time state |

## Quick Start

See `docs/SETUP.md` for full setup instructions.

```bash
# Start infrastructure
docker compose up -d

# Backend API
cd backend && pip install -e . && uvicorn app.main:app --port 8000 --reload

# Perception Service
cd perception && pip install -e . && uvicorn service.main:app --port 8100 --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Status

🔨 **Layer 1 (Ingest)** — In progress
