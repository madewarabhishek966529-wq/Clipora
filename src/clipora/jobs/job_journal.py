"""Durable job journal for startup recovery and active run tracking."""

import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from clipora.core.clip_schema import JobStatus
from clipora.storage.atomic import atomic_write_json, read_json_safe
from clipora.jobs.job_artifacts import read_job_metadata, update_job_metadata

JOURNAL_PATH = Path("data/jobs_journal.json")
_JOURNAL_LOCK = threading.Lock()

class JobJournal:
    """Thread-safe persistent journal tracking active and queued jobs."""

    def __init__(self, journal_path: Path | str = JOURNAL_PATH):
        self.journal_path = Path(journal_path)

    def _load(self) -> Dict[str, Any]:
        return read_json_safe(self.journal_path, default={"jobs": {}})

    def _save(self, data: Dict[str, Any]) -> None:
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(self.journal_path, data)

    def record_job(self, job_id: str, payload: Dict[str, Any]) -> None:
        """Register a new job in the journal."""
        with _JOURNAL_LOCK:
            data = self._load()
            jobs = data.setdefault("jobs", {})
            jobs[job_id] = {
                "job_id": job_id,
                "status": JobStatus.QUEUED.value,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "payload": payload,
                "pid": None,
            }
            self._save(data)

    def update_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        pid: Optional[int] = None,
        error: Optional[str] = None,
        phase: Optional[str] = None,
    ) -> None:
        """Atomically update a job's status in the journal."""
        with _JOURNAL_LOCK:
            data = self._load()
            job = data.get("jobs", {}).get(job_id)
            if not job:
                return
            if status is not None:
                job["status"] = status
            if pid is not None:
                job["pid"] = pid
            if error is not None:
                job["error"] = error
            if phase is not None:
                job["phase"] = phase
            job["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save(data)

    def remove_job(self, job_id: str) -> None:
        """Remove a terminal job from the active journal."""
        with _JOURNAL_LOCK:
            data = self._load()
            if "jobs" in data and job_id in data["jobs"]:
                del data["jobs"][job_id]
                self._save(data)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with _JOURNAL_LOCK:
            data = self._load()
            return data.get("jobs", {}).get(job_id)

    def list_active_jobs(self) -> List[Dict[str, Any]]:
        with _JOURNAL_LOCK:
            data = self._load()
            return list(data.get("jobs", {}).values())

    def recover_on_startup(self) -> List[Dict[str, Any]]:
        """Scan journal on boot, re-queue queued jobs, and mark dead in-flight jobs as failed."""
        with _JOURNAL_LOCK:
            data = self._load()
            jobs = data.get("jobs", {})
            recovered_for_requeue: List[Dict[str, Any]] = []

            for job_id, entry in list(jobs.items()):
                st = entry.get("status")
                if st == JobStatus.QUEUED.value:
                    recovered_for_requeue.append(entry)
                elif st in (
                    JobStatus.DOWNLOADING.value,
                    JobStatus.TRANSCRIBING.value,
                    JobStatus.ANALYZING.value,
                    JobStatus.REFRAMING.value,
                    JobStatus.POSTPROCESSING.value,
                ):
                    # Active job was interrupted by server crash/shutdown
                    entry["status"] = JobStatus.FAILED.value
                    entry["error"] = "Interrupted by host restart or server crash."
                    entry["updated_at"] = datetime.now(timezone.utc).isoformat()
                    # Also update disk metadata if present
                    update_job_metadata(
                        job_id,
                        {
                            "status": JobStatus.FAILED,
                            "error_message": "Interrupted by host restart or server crash.",
                        },
                    )
                elif st in (JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value):
                    # Completed or terminated, can be purged from active journal
                    pass

            self._save(data)
            return recovered_for_requeue

_global_journal = JobJournal()

def get_job_journal() -> JobJournal:
    return _global_journal
