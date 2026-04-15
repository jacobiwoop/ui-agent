import os
import uuid
import json
import logging
import asyncio
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from datetime import datetime

# Import orchestrator logic
from orchestrator import run_full_pipeline

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Raw Logic AI - Orchestrator")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development, allow all. Change this for prod.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
EXPORT_DIR = "exports"
SESSION_DIR = "sessions"
DESIGN_DIR = "/home/aiko/Documents/agent-cli/design"

# Ensure directories exist
os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(SESSION_DIR, exist_ok=True)

# Mount static designs (optional, we'll serve them via routes for more control)
app.mount("/design", StaticFiles(directory=DESIGN_DIR), name="design")

# Active sessions memory (for real-time updates)
active_sessions = {}

class GenerationRequest(BaseModel):
    url: str
    user_id: str = "default_user"

class GenerationStatus(BaseModel):
    session_id: str
    status: str
    progress: int
    logs: List[str]
    result_url: Optional[str] = None

# Routes
@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    with open(os.path.join(DESIGN_DIR, "dashboard.html"), "r") as f:
        return f.read()

@app.get("/generate", response_class=HTMLResponse)
async def get_generation_page():
    with open(os.path.join(DESIGN_DIR, "genration.html"), "r") as f:
        return f.read()

@app.get("/products", response_class=HTMLResponse)
async def get_products_page():
    with open(os.path.join(DESIGN_DIR, "produit.html"), "r") as f:
        return f.read()

@app.post("/api/generate")
async def start_generation(request: GenerationRequest, background_tasks: BackgroundTasks):
    session_id = str(uuid.uuid4())
    logger.info(f"Starting generation for session {session_id} - URL: {request.url}")
    
    # Initialize session state
    active_sessions[session_id] = {
        "status": "starting",
        "progress": 0,
        "logs": ["Initialisation du pipeline multi-agents..."],
        "url": request.url
    }
    
    # Launch in background
    background_tasks.add_task(orchestrate_session, session_id, request.url)
    
    return {"session_id": session_id}

@app.get("/api/status/{session_id}")
async def get_status(session_id: str):
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return active_sessions[session_id]

async def orchestrate_session(session_id: str, url: str):
    """Bridge between FastAPI and the existing orchestrator logic."""
    try:
        def log_to_session(msg):
            active_sessions[session_id]["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
            logger.info(f"Session {session_id}: {msg}")

        # Start the pipeline
        log_to_session("Lancement du pipeline multi-agents...")
        active_sessions[session_id]["status"] = "processing"
        active_sessions[session_id]["progress"] = 5
        
        # Run the pipeline (blocking call in thread to avoid blocking event loop)
        loop = asyncio.get_event_loop()
        result_path = await loop.run_in_executor(
            None, 
            run_full_pipeline, 
            url, 
            "qwen3.5:cloud", 
            session_id
        )

        if result_path and os.path.exists(result_path):
            active_sessions[session_id]["status"] = "completed"
            active_sessions[session_id]["progress"] = 100
            active_sessions[session_id]["result_url"] = f"/{result_path}"
            log_to_session("Génération réussie !")
        else:
            raise Exception("L'orchestrateur n'a pas produit de fichier final.")
            
    except Exception as e:
        logger.error(f"Error in session {session_id}: {str(e)}")
        active_sessions[session_id]["status"] = "failed"
        active_sessions[session_id]["logs"].append(f"ERREUR : {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
