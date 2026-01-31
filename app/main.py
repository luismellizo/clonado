from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import os
import json
from app.tasks import clone_site_task
from celery.result import AsyncResult

app = FastAPI(
    title="Web Cloner Elite API",
    description="Professional web cloning and analysis tool",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class CloneRequest(BaseModel):
    url: str
    mode: str = "clone"  # clone | analyze_only


# Endpoints
@app.post("/api/clone")
async def start_clone(request: CloneRequest):
    """Start a cloning job."""
    job_id = str(uuid.uuid4())
    task = clone_site_task.delay(request.url, job_id)
    return {
        "job_id": job_id,
        "task_id": task.id,
        "message": "Cloning started"
    }


@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    """Get status of a cloning task."""
    task_result = AsyncResult(task_id)
    
    result = {
        "task_id": task_id,
        "status": task_result.status,
        "result": None,
        "analysis": None
    }
    
    if task_result.status == 'SUCCESS':
        task_data = task_result.result
        result["result"] = task_data.get("zip_path") if isinstance(task_data, dict) else task_data
        result["analysis"] = task_data.get("analysis") if isinstance(task_data, dict) else None
    elif task_result.status == 'PROGRESS':
        result["result"] = task_result.result
    elif task_result.status == 'FAILURE':
        result["result"] = str(task_result.result)
    
    return JSONResponse(result)


@app.get("/api/analysis/{job_id}")
async def get_analysis(job_id: str):
    """Get analysis data for a completed job."""
    analysis_path = f"/app/downloads/{job_id}/analysis.json"
    
    if not os.path.exists(analysis_path):
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    try:
        with open(analysis_path, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        return JSONResponse(analysis_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading analysis: {str(e)}")


@app.get("/api/download/{job_id}")
async def download_file(job_id: str):
    """Download the cloned site as a ZIP file."""
    file_path = f"/app/downloads/{job_id}.zip"
    
    if os.path.exists(file_path):
        return FileResponse(
            file_path,
            filename=f"cloned_site_{job_id}.zip",
            media_type="application/zip"
        )
    
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}


# Serve Frontend
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
