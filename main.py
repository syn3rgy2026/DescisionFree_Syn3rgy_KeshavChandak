"""
main.py
-------
FastAPI entry point for the Synergy Agent system.
Provides a web interface and API endpoints for running tasks.
"""

import os
import sys
import asyncio
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from agent.core_agent import run_agent

# Create FastAPI app
app = FastAPI(title="Synergy Agent API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure required directories exist
os.makedirs("ui", exist_ok=True)
os.makedirs("output", exist_ok=True)

# Mount static folder for UI assets (.css, .js)
app.mount("/static", StaticFiles(directory="ui"), name="static")

# Global variables for tracking task status 
# (Simple array since it's a single user IDE experience)
current_status = []

def ui_step_callback(step_log):
    """
    Intercepts the Agent's thought process step logs, and appends them
    to the global status buffer for the UI to poll.
    """
    step_num = getattr(step_log, 'step_number', '?')
    model_output = getattr(step_log, 'model_output', None)
    tool_calls = getattr(step_log, 'tool_calls', [])
    err = getattr(step_log, 'error', None)
    
    if err:
        current_status.append(f"[Step {step_num}] Error: {str(err)[:50]}...")
    elif tool_calls:
        for tc in tool_calls:
            name = getattr(tc, 'name', str(tc))
            current_status.append(f"[Step {step_num}] Using tool: {name}")
    elif model_output:
        current_status.append(f"[Step {step_num}] Thinking & analyzing context...")
    else:
        current_status.append(f"[Step {step_num}] Processing...")

@app.get("/")
def read_index():
    with open("ui/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/status")
def get_status():
    return JSONResponse({"logs": current_status})

@app.post("/run-task")
async def handle_run_task(
    task: str = Form(...), 
    files: Optional[List[UploadFile]] = File(None)
):
    global current_status
    current_status = []
    current_status.append("Task received, analyzing...")
    
    task_text = task
    saved_files = []
    
    if files:
        for file in files:
            if file.filename:
                file_path = os.path.join("output", file.filename)
                with open(file_path, "wb") as f:
                    f.write(await file.read())
                saved_files.append(file_path)
        
        if saved_files:
            task_text += f"\n\n[USER ATTACHED FILES: {', '.join(saved_files)}. Please analyze or modify them to fulfill the prompt.]"

    # Run agent in background thread to avoid blocking the async event loop for polling
    try:
        result = await asyncio.to_thread(run_agent, task_text, ui_step_callback)
        success = True
    except Exception as e:
        result = f"Error during agent execution: {str(e)}"
        success = False
        
    return JSONResponse({
        "response": str(result),
        "success": success
    })

if __name__ == "__main__":
    print("="*60)
    print(" 🚀 Synergy Agent Backend Ready ")
    print(" 💻 Web UI listening on: http://127.0.0.1:8000")
    print("="*60)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, log_level="info")
