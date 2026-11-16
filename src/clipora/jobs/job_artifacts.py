"""Job metadata management with thread-safe file locks and atomic commits."""

import threading
from pathlib import Path
from typing import Any, Dict, Optional
from clipora.core.clip_schema import JobMetadata, JobStatus
from clipora.storage.atomic import atomic_write_json, read_json_safe

# Innermost threading lock guarding reads/writes to metadata.json
_METADATA_LOCK = threading.Lock()

OUTPUT_ROOT = Path("output")

def get_job_dir(job_id: str) -> Path:
    """Return the output directory path for a specific job."""
    return OUTPUT_ROOT / job_id

def get_metadata_path(job_id: str) -> Path:
    """Return the metadata.json path for a specific job."""
    return get_job_dir(job_id) / f"{job_id}_metadata.json"

def read_job_metadata(job_id: str) -> Optional[JobMetadata]:
    """Safely read and validate JobMetadata from disk under _METADATA_LOCK."""
    path = get_metadata_path(job_id)
    with _METADATA_LOCK:
        if not path.is_file():
            return None
        data = read_json_safe(path)
        if not data or not isinstance(data, dict):
            return None
        try:
            return JobMetadata.model_validate(data)
        except Exception:
            return None

def write_job_metadata(metadata: JobMetadata) -> None:
    """Safely write JobMetadata to disk atomically under _METADATA_LOCK."""
    path = get_metadata_path(metadata.job_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _METADATA_LOCK:
        atomic_write_json(path, metadata.model_dump())

def update_job_metadata(job_id: str, updates: Dict[str, Any]) -> Optional[JobMetadata]:
    """Apply partial updates to existing job metadata atomically under _METADATA_LOCK."""
    path = get_metadata_path(job_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _METADATA_LOCK:
        current_data = read_json_safe(path) if path.is_file() else None
        if not current_data:
            return None
        current_data.update(updates)
        updated_meta = JobMetadata.model_validate(current_data)
        atomic_write_json(path, updated_meta.model_dump())
        return updated_meta
