"""Pipeline runtime checkpoints and attempt tracking."""

import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional
from clipora.storage.atomic import atomic_write_json, read_json_safe

_RUNTIME_LOCK = threading.Lock()

class RuntimeCheckpoint:
    """Manages .runtime.json checkpoints per job."""

    def __init__(self, job_dir: Path | str):
        self.job_dir = Path(job_dir)
        self.checkpoint_path = self.job_dir / ".runtime.json"

    def read(self) -> Dict[str, Any]:
        with _RUNTIME_LOCK:
            return read_json_safe(self.checkpoint_path, default={})

    def update_phase(self, phase: str, payload: Optional[Dict[str, Any]] = None) -> None:
        with _RUNTIME_LOCK:
            self.job_dir.mkdir(parents=True, exist_ok=True)
            data = read_json_safe(self.checkpoint_path, default={})
            data["last_phase"] = phase
            completed = data.get("completed_phases", [])
            if phase not in completed:
                completed.append(phase)
            data["completed_phases"] = completed
            if payload:
                data.setdefault("phase_data", {})[phase] = payload
            atomic_write_json(self.checkpoint_path, data)

    def is_phase_completed(self, phase: str) -> bool:
        with _RUNTIME_LOCK:
            data = read_json_safe(self.checkpoint_path, default={})
            return phase in data.get("completed_phases", [])

    def get_phase_data(self, phase: str) -> Optional[Dict[str, Any]]:
        with _RUNTIME_LOCK:
            data = read_json_safe(self.checkpoint_path, default={})
            return data.get("phase_data", {}).get(phase)
