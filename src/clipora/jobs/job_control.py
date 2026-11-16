"""Subprocess lifecycle controller: pause, resume, cancel, and process tree termination."""

import os
import signal
import psutil
from typing import Optional
from clipora.core.errors import JobNotFoundError
from clipora.core.clip_schema import JobStatus
from clipora.jobs.job_journal import get_job_journal
from clipora.jobs.job_artifacts import update_job_metadata

def terminate_process_tree(pid: int, timeout: float = 3.0) -> None:
    """Recursively terminate an entire process tree given its root PID."""
    try:
        parent = psutil.Process(pid)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return

    children = parent.children(recursive=True)
    # Attempt graceful SIGTERM
    for child in children:
        try:
            child.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    try:
        parent.terminate()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

    # Wait for termination
    _, alive = psutil.wait_procs(children + [parent], timeout=timeout)
    # Force SIGKILL on remaining survivors
    for p in alive:
        try:
            p.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

def pause_job(job_id: str) -> bool:
    """Suspend execution of a running job's process tree."""
    journal = get_job_journal()
    entry = journal.get_job(job_id)
    if not entry:
        raise JobNotFoundError(job_id)

    pid = entry.get("pid")
    if not pid:
        return False

    try:
        proc = psutil.Process(pid)
        for child in proc.children(recursive=True):
            try:
                child.suspend()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        proc.suspend()
        journal.update_job(job_id, status=JobStatus.PAUSED.value)
        update_job_metadata(job_id, {"status": JobStatus.PAUSED})
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

def resume_job(job_id: str) -> bool:
    """Resume execution of a suspended job's process tree."""
    journal = get_job_journal()
    entry = journal.get_job(job_id)
    if not entry:
        raise JobNotFoundError(job_id)

    pid = entry.get("pid")
    if not pid:
        return False

    try:
        proc = psutil.Process(pid)
        proc.resume()
        for child in proc.children(recursive=True):
            try:
                child.resume()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        journal.update_job(job_id, status=entry.get("phase", JobStatus.ANALYZING.value))
        update_job_metadata(job_id, {"status": JobStatus.ANALYZING})
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

def cancel_job(job_id: str) -> bool:
    """Terminate running subprocess, mark job as cancelled, and clean up journal."""
    journal = get_job_journal()
    entry = journal.get_job(job_id)
    if not entry:
        return False

    pid = entry.get("pid")
    if pid:
        terminate_process_tree(pid)

    journal.update_job(job_id, status=JobStatus.CANCELLED.value)
    update_job_metadata(job_id, {"status": JobStatus.CANCELLED, "error_message": "Cancelled by user."})
    journal.remove_job(job_id)
    return True
