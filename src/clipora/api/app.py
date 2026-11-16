"""Main FastAPI gateway, lifespan manager, and API endpoints."""

import os
import shutil
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from clipora.core.errors import CliporaError, ValidationError, SSRFError, JobNotFoundError
from clipora.api.schemas import (
    CreateJobRequest,
    BatchCreateJobRequest,
    PublishClipRequest,
    SmartCutRequest,
    ReframeClipRequest,
    EditAIRequest,
    AddMonitorRequest,
)
from clipora.api.security import rate_limit_dependency, assert_safe_path
from clipora.api.config_routes import router as config_router
from clipora.storage.config_store import get_config_store
from clipora.storage.atomic import atomic_write_bytes
from clipora.jobs.job_submission import get_job_queue
from clipora.jobs.job_journal import get_job_journal
from clipora.jobs.job_artifacts import get_job_dir, read_job_metadata
from clipora.jobs.job_results import get_job_summary
from clipora.jobs.job_control import pause_job, resume_job, cancel_job
from clipora.clips.smartcut_service import apply_smart_cut_to_clip
from clipora.clips.reframe_service import reframe_clip_on_demand
from clipora.publishing.publish_service import publish_clip_to_social
from clipora.monitoring.live_monitor import get_live_monitor_registry
from clipora.editing.clip_edit_ai import parse_natural_language_edit_instructions

OUTPUT_DIR = Path("output")
UPLOADS_DIR = Path("uploads")
FONTS_DIR = Path("data/fonts")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: recover journal and launch background services
    journal = get_job_journal()
    requeue_list = journal.recover_on_startup()
    queue = get_job_queue()
    config = get_config_store().get_config()
    queue.start(max_concurrent=config.max_concurrent_jobs)

    for job_entry in requeue_list:
        p = job_entry.get("payload", {})
        await queue.submit_job(
            source_url=p.get("source_url"),
            input_file=p.get("input_file"),
            reframe_mode=p.get("reframe_mode", "auto"),
            custom_instructions=p.get("custom_instructions"),
            transcription_provider=p.get("transcription_provider"),
            job_id=job_entry["job_id"],
        )

    monitor_reg = get_live_monitor_registry()
    monitor_reg.start()

    yield

    # Shutdown: clean termination of background tasks
    await queue.stop()
    await monitor_reg.stop()

app = FastAPI(
    title="Clipora Video Pipeline Engine",
    description="Autonomous AI video clipping, reframing, and publishing engine",
    version="0.1.0",
    lifespan=lifespan,
)

# Exception handlers
@app.exception_handler(CliporaError)
async def clipora_exception_handler(request, exc: CliporaError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "details": exc.details},
    )

# Configure CORS
config = get_config_store().get_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Configuration Router
app.include_router(config_router)

# =============================================================================
# JOB SUBMISSION & CONTROL ENDPOINTS
# =============================================================================

@app.post("/api/jobs", dependencies=[Depends(rate_limit_dependency)])
async def create_job(req: CreateJobRequest):
    """Submit a single video URL or upload for clipping."""
    queue = get_job_queue()
    meta = await queue.submit_job(
        source_url=req.source_url,
        input_file=req.input_file,
        reframe_mode=req.reframe_mode,
        custom_instructions=req.custom_instructions,
        transcription_provider=req.transcription_provider,
    )
    return {"status": "queued", "job_id": meta.job_id, "metadata": meta.model_dump()}

@app.post("/api/jobs/batch", dependencies=[Depends(rate_limit_dependency)])
async def create_batch_jobs(req: BatchCreateJobRequest):
    """Intake multiple video URLs into the processing queue."""
    if not req.urls:
        raise ValidationError("URLs list cannot be empty.")
    queue = get_job_queue()
    submitted = []
    for url in req.urls:
        meta = await queue.submit_job(
            source_url=url,
            reframe_mode=req.reframe_mode,
            custom_instructions=req.custom_instructions,
            transcription_provider=req.transcription_provider,
        )
        submitted.append({"job_id": meta.job_id, "source_url": url})
    return {"status": "queued", "count": len(submitted), "jobs": submitted}

@app.get("/api/jobs")
def list_jobs():
    """List all active and recent jobs from the filesystem and journal."""
    journal = get_job_journal()
    active_jobs = {j["job_id"]: j for j in journal.list_active_jobs()}

    # Scan output directory for past completed/failed runs
    all_jobs = []
    if OUTPUT_DIR.is_dir():
        for job_dir in OUTPUT_DIR.iterdir():
            if job_dir.is_dir() and not job_dir.name.startswith("."):
                summary = get_job_summary(job_dir.name)
                if summary:
                    all_jobs.append(summary)

    # Sort descending by updated_at / created_at
    all_jobs.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return {"jobs": all_jobs, "active_count": len(active_jobs)}

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    """Retrieve full job telemetry, progress, logs, and clips."""
    summary = get_job_summary(job_id)
    if not summary:
        raise JobNotFoundError(job_id)

    log_file = get_job_dir(job_id) / "pipeline.log"
    recent_logs = ""
    if log_file.is_file():
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                recent_logs = "".join(lines[-200:])  # Last 200 lines
        except Exception:
            pass

    summary["logs"] = recent_logs
    return summary

@app.post("/api/jobs/{job_id}/pause")
def pause_job_route(job_id: str):
    """Suspend execution of an in-flight job's subprocess."""
    success = pause_job(job_id)
    return {"status": "paused" if success else "failed", "job_id": job_id}

@app.post("/api/jobs/{job_id}/resume")
def resume_job_route(job_id: str):
    """Resume execution of a suspended job's subprocess."""
    success = resume_job(job_id)
    return {"status": "resumed" if success else "failed", "job_id": job_id}

@app.post("/api/jobs/{job_id}/cancel")
def cancel_job_route(job_id: str):
    """Cancel execution and terminate process tree."""
    success = cancel_job(job_id)
    return {"status": "cancelled" if success else "failed", "job_id": job_id}

@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str):
    """Purge job directory and files permanently from disk."""
    cancel_job(job_id)
    job_dir = get_job_dir(job_id)
    if job_dir.is_dir():
        shutil.rmtree(job_dir, ignore_errors=True)
    return {"status": "deleted", "job_id": job_id}

@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload a raw local video file into uploads/ storage."""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "video.mp4").suffix or ".mp4"
    file_id = f"upload_{uuid.uuid4().hex[:12]}{ext}"
    dest_path = UPLOADS_DIR / file_id

    content = await file.read()
    atomic_write_bytes(dest_path, content)
    return {
        "status": "success",
        "input_file": str(dest_path.resolve()),
        "filename": file.filename,
        "size_bytes": len(content),
    }

# =============================================================================
# PER-CLIP EDITING & PUBLISHING ENDPOINTS
# =============================================================================

@app.post("/api/clips/{job_id}/{clip_index}/smartcut")
async def trigger_smartcut(job_id: str, clip_index: int, req: SmartCutRequest):
    """Trigger on-demand SmartCut silence removal for clip."""
    return await apply_smart_cut_to_clip(job_id, clip_index, req.min_silence_gap)

@app.post("/api/clips/{job_id}/{clip_index}/reframe")
async def trigger_reframe(job_id: str, clip_index: int, req: ReframeClipRequest):
    """Trigger on-demand reframing pass for clip."""
    return await reframe_clip_on_demand(job_id, clip_index, req.reframe_mode)

@app.post("/api/clips/{job_id}/{clip_index}/publish")
async def trigger_publish(job_id: str, clip_index: int, req: PublishClipRequest):
    """Publish or schedule clip to social channels via Zernio."""
    return await publish_clip_to_social(
        job_id=job_id,
        clip_index=clip_index,
        platforms=req.platforms,
        schedule_mode=req.schedule_mode,
        manual_scheduled_for=req.manual_scheduled_for,
        caption=req.caption,
    )

@app.post("/api/clips/{job_id}/{clip_index}/edit-ai")
def trigger_edit_ai(job_id: str, clip_index: int, req: EditAIRequest):
    """Parse natural language editing instruction into cut time ranges."""
    meta = read_job_metadata(job_id)
    if not meta or clip_index >= len(meta.clips):
        raise JobNotFoundError(f"{job_id}/clip/{clip_index}")

    clip = meta.clips[clip_index]
    dur = clip.end - clip.start
    drop_ranges = parse_natural_language_edit_instructions(req.instruction, dur)
    return {
        "instruction": req.instruction,
        "clip_duration": dur,
        "drop_ranges": drop_ranges,
    }

# =============================================================================
# LIVE MONITOR ENDPOINTS
# =============================================================================

@app.get("/api/monitors")
def list_monitors_route():
    """List all registered channel monitors."""
    reg = get_live_monitor_registry()
    return {"monitors": reg.list_monitors()}

@app.post("/api/monitors")
def add_monitor_route(req: AddMonitorRequest):
    """Add new channel monitor for 24/7 autonomous monitoring."""
    reg = get_live_monitor_registry()
    entry = reg.add_monitor(
        platform=req.platform,
        channel_id=req.channel_id,
        enabled=req.enabled,
        prelive_skip_minutes=req.prelive_skip_minutes,
        segment_slice_minutes=req.segment_slice_minutes,
        min_viral_score=req.min_viral_score,
        auto_publish=req.auto_publish,
    )
    return {"status": "created", "monitor": entry}

@app.delete("/api/monitors/{monitor_id}")
def delete_monitor_route(monitor_id: str):
    """Remove a channel monitor."""
    reg = get_live_monitor_registry()
    success = reg.remove_monitor(monitor_id)
    return {"status": "deleted" if success else "not_found", "monitor_id": monitor_id}

# =============================================================================
# STATIC SAFE MEDIA SERVING
# =============================================================================

@app.get("/videos/{job_id}/{filename}")
def serve_video(job_id: str, filename: str):
    """Safely stream rendered video files without directory traversals."""
    target_path = assert_safe_path(Path(job_id) / filename, OUTPUT_DIR)
    if not target_path.is_file():
        raise HTTPException(status_code=404, detail="Video file not found.")
    return FileResponse(target_path, media_type="video/mp4")

@app.get("/thumbnails/{job_id}/{filename}")
def serve_thumbnail(job_id: str, filename: str):
    """Safely serve thumbnail image files."""
    target_path = assert_safe_path(Path(job_id) / filename, OUTPUT_DIR)
    if not target_path.is_file():
        raise HTTPException(status_code=404, detail="Thumbnail not found.")
    return FileResponse(target_path, media_type="image/jpeg")
