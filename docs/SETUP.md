# Argus C2 — Mac Setup Guide (M4 Pro)

## Prerequisites

Before starting, you need these installed on your Mac:

1. **Homebrew** (macOS package manager)
2. **Python 3.11+** (you likely already have this)
3. **Node.js 20+** (for frontend)
4. **Docker Desktop** (for PostgreSQL + Redis)
5. **Git** (comes with Xcode CLI tools)

---

## Step 0: Install Prerequisites (if missing)

Open Terminal and run each line:

```bash
# Check what you already have
python3 --version     # Need 3.11+
node --version        # Need 20+
docker --version      # Need Docker Desktop
git --version         # Need git

# Install Homebrew (if you don't have it)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11+ (if needed)
brew install python@3.12

# Install Node.js (if needed)
brew install node

# Install Docker Desktop — download from:
# https://www.docker.com/products/docker-desktop/
# Open it once installed and let it start.

# Install uv (fast Python package manager, optional but recommended)
brew install uv
```

---

## Step 1: Clone Your Repo

```bash
cd ~
git clone https://github.com/Akash9179/Project-Argus.git
cd Project-Argus
```

If the repo already exists locally, just `cd` into it.

---

## Step 2: Copy All Project Files

All the files I created need to go into your repo. You have two options:

**Option A: Download from this chat**
I'll provide a zip/tar of all files. Extract into your Project-Argus folder.

**Option B: Push from a fresh init (if repo is empty)**
If your repo is empty or you want a clean start:
```bash
cd ~/Project-Argus
# Files should already be here after clone
# If starting fresh, copy the files I created into this folder structure
```

---

## Step 3: Create Environment File

```bash
cd ~/Project-Argus
cp .env.example .env
```

This creates your local `.env` with database passwords and service URLs.
The defaults work as-is for development.

---

## Step 4: Start PostgreSQL + Redis

```bash
# Make sure Docker Desktop is running (check the whale icon in menu bar)
cd ~/Project-Argus
docker compose up -d
```

You should see:
```
✔ Container argus-postgres  Started
✔ Container argus-redis     Started
```

Verify they're running:
```bash
docker compose ps
```

Both should show "running" status.

---

## Step 5: Set Up Backend API

```bash
cd ~/Project-Argus/backend

# Create a Python virtual environment
python3 -m venv .venv

# Activate it (you'll see (.venv) in your prompt)
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run the backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
==================================================
  ARGUS C2 — Backend API
==================================================
  ✓ Database initialized
  ✓ Server running on 0.0.0.0:8000
==================================================
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Test it:** Open a NEW terminal tab and run:
```bash
curl http://localhost:8000/health
```

Should return: `{"status":"ok","service":"argus-backend"}`

**Keep this terminal running.** Open a new tab for the next step.

---

## Step 6: Set Up Perception Service

Open a NEW terminal tab:

```bash
cd ~/Project-Argus/perception

# Create a separate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies (without AI for now — just camera ingestion)
pip install -e .

# Install OpenCV (this can take a minute)
pip install opencv-python

# Run the perception service
uvicorn service.main:app --host 0.0.0.0 --port 8100 --reload
```

You should see:
```
==================================================
  ARGUS C2 — Perception Service
==================================================
  ✓ Frame distributor started
  ✓ Server on 0.0.0.0:8100
==================================================
```

**Test it:** In another terminal:
```bash
curl http://localhost:8100/health
```

Should return: `{"status":"ok","service":"argus-perception","sources_total":0,"sources_online":0}`

---

## Step 7: Test Camera Ingestion (The Big Moment)

This is where you see your webcam feed through the Argus pipeline.

Open another terminal and run:

```bash
# Start your webcam as a source
curl -X POST http://localhost:8100/sources/start \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "00000000-0000-0000-0000-000000000001",
    "name": "Built-in Webcam",
    "source_type": "usb",
    "uri": "0",
    "target_fps": 10
  }'
```

Should return: `{"status":"started","source_id":"00000000-0000-0000-0000-000000000001"}`

**Your Mac will ask for camera permission — click Allow.**

Now open your browser and go to:

```
http://localhost:8100/stream/00000000-0000-0000-0000-000000000001
```

**You should see your webcam feed live in the browser.**

That image is flowing through:
`Webcam → WebcamAdapter → Frame → SourceManager → frame_queue → frame_distributor → MJPEG → Browser`

Check source status:
```bash
curl http://localhost:8100/sources/status | python3 -m json.tool
```

---

## Step 8: Add a Video File Source (Optional)

Download any test video (or use one you have):

```bash
# Create a data directory
mkdir -p ~/Project-Argus/data/recordings

# Download a sample surveillance video (small, free)
# Or just use any .mp4 file you have on your Mac
# Copy it to: ~/Project-Argus/data/recordings/test.mp4
```

Then add it as a source:

```bash
curl -X POST http://localhost:8100/sources/start \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "00000000-0000-0000-0000-000000000002",
    "name": "Gate Camera (Replay)",
    "source_type": "file",
    "uri": "/Users/YOUR_USERNAME/Project-Argus/data/recordings/test.mp4",
    "target_fps": 10
  }'
```

Replace `YOUR_USERNAME` with your actual Mac username.

View it at: `http://localhost:8100/stream/00000000-0000-0000-0000-000000000002`

---

## Step 9: Test Backend CRUD

In another terminal:

```bash
# Create a source in the backend database
curl -X POST http://localhost:8000/api/v1/sources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Entry Gate",
    "type": "usb",
    "uri": "0",
    "domain": "land",
    "target_fps": 10,
    "location": {
      "facility_x": 50,
      "facility_y": 30,
      "fov_angle": 180,
      "fov_width": 90
    }
  }'

# List all sources
curl http://localhost:8000/api/v1/sources | python3 -m json.tool
```

---

## VS Code Workspace Setup

```bash
# Open the workspace file in VS Code
cd ~/Project-Argus
code argus.code-workspace
```

This opens VS Code with four panels in the sidebar:
- 🔧 Backend API
- 👁️ Perception Service
- 🖥️ Frontend
- 📁 Project Root

**Install recommended extensions** when VS Code prompts you (Python, Ruff, Prettier, Docker).

---

## Daily Workflow

Every time you start working:

```bash
# Terminal 1: Start infrastructure
cd ~/Project-Argus && docker compose up -d

# Terminal 2: Backend API
cd ~/Project-Argus/backend && source .venv/bin/activate && uvicorn app.main:app --port 8000 --reload

# Terminal 3: Perception Service
cd ~/Project-Argus/perception && source .venv/bin/activate && uvicorn service.main:app --port 8100 --reload

# Terminal 4: Frontend (once we build it)
cd ~/Project-Argus/frontend && npm run dev
```

Or open VS Code → each folder has its own terminal.

---

## Troubleshooting

**"Docker is not running"**
→ Open Docker Desktop from Applications. Wait for the whale icon to stop animating.

**"Port already in use"**
→ Kill the old process: `lsof -i :8000` then `kill -9 <PID>`

**"Camera permission denied"**
→ System Settings → Privacy & Security → Camera → Allow Terminal/VS Code

**"No module named 'service'"**
→ Make sure you're in the right directory and venv is activated:
   `cd ~/Project-Argus/perception && source .venv/bin/activate`

**"psycopg / asyncpg error"**
→ `brew install postgresql` (installs client libraries needed by asyncpg)

**"cv2 not found"**
→ `pip install opencv-python` in the perception venv

---

## What's Running Where

```
┌──────────────────────────────────────────────┐
│  Your Mac (M4 Pro)                           │
│                                              │
│  Docker:                                     │
│    ├── PostgreSQL  :5432                     │
│    └── Redis       :6379                     │
│                                              │
│  Python (venv 1):                            │
│    └── Backend API :8000  (FastAPI)          │
│                                              │
│  Python (venv 2):                            │
│    └── Perception  :8100  (FastAPI+OpenCV)   │
│                                              │
│  Node (later):                               │
│    └── Frontend    :5173  (Vite+React)       │
│                                              │
│  Browser:                                    │
│    └── http://localhost:5173                  │
│        ├── REST → :8000 (sources, zones)     │
│        ├── MJPEG → :8100/stream/{id}         │
│        └── WS → :8100/ws/status              │
└──────────────────────────────────────────────┘
```
