"""Asynchronous runner executing jobs inside isolated OS subprocesses."""

import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from clipora.core.clip_schema import JobStatus
from clipora.core.errors import SubprocessCrashError
from clipora.jobs.job_artifacts import get_job_dir, update_job_metadata
from clipora.jobs.job_journal import get_job_journal

async def run_pipeline_subprocess(job_id: str) -> int:
    """Spawn the pipeline orchestrator in a dedicated OS subprocess."""
    journal = get_job_journal()
    job_dir = get_job_dir(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)
    log_path = job_dir / "pipeline.log"

    cmd = [
        sys.executable,
        "-m",
        "clipora.pipeline.orchestrator",
        "--job-id",
        job_id,
    ]

    journal.update_job(job_id, status=JobStatus.DOWNLOADING.value, phase="download")
    update_job_metadata(
        job_id,
        {
            "status": JobStatus.DOWNLOADING,
            "current_phase": "download",
            "progress_percent": 5.0,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"=== Clipora Pipeline Worker Started for Job #{job_id} ===\n")
        log_file.flush()

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=log_file,
            stderr=asyncio.subprocess.STDOUT,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )

        journal.update_job(job_id, pid=proc.pid)

        returncode = await proc.wait()

    if returncode == 0:
        journal.update_job(job_id, status=JobStatus.COMPLETED.value)
        update_job_metadata(
            job_id,
            {
                "status": JobStatus.COMPLETED,
                "current_phase": "completed",
                "progress_percent": 100.0,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        journal.remove_job(job_id)
        return returncode
    else:
        # Check if job was cancelled
        current = journal.get_job(job_id)
        if current and current.get("status") == JobStatus.CANCELLED.value:
            return returncode

        err_msg = f"Pipeline process exited with code {returncode}."
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as lf:
                error_lines = [l.strip() for l in lf.readlines() if "ERROR" in l or "Error:" in l]
                if error_lines:
                    err_msg = error_lines[-1]
        except Exception:
            pass

        journal.update_job(job_id, status=JobStatus.FAILED.value, error=err_msg)
        update_job_metadata(
            job_id,
            {
                "status": JobStatus.FAILED,
                "error_message": err_msg,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        raise SubprocessCrashError(job_id, returncode, details={"log_path": str(log_path)})
