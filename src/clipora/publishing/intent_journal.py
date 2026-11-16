"""Durable publish intent journal enforcing idempotency across social media posts."""

import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from clipora.storage.atomic import atomic_write_json, read_json_safe

INTENT_JOURNAL_PATH = Path("data/publish_intents.json")
_INTENT_LOCK = threading.Lock()

class PublishStatus:
    PENDING = "pending"
    UPLOADING = "uploading"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class IntentJournal:
    """Persistent ledger tracking social publishing intents and idempotency keys."""

    def __init__(self, journal_path: Path | str = INTENT_JOURNAL_PATH):
        self.journal_path = Path(journal_path)

    def _load(self) -> Dict[str, Any]:
        return read_json_safe(self.journal_path, default={"intents": {}})

    def _save(self, data: Dict[str, Any]) -> None:
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(self.journal_path, data)

    def record_intent(
        self,
        intent_id: str,
        idempotency_key: str,
        job_id: str,
        clip_index: int,
        platforms: List[str],
        scheduled_for: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Atomically record a PENDING publishing intent before network execution."""
        with _INTENT_LOCK:
            data = self._load()
            entry = {
                "intent_id": intent_id,
                "idempotency_key": idempotency_key,
                "job_id": job_id,
                "clip_index": clip_index,
                "platforms": platforms,
                "scheduled_for": scheduled_for,
                "status": PublishStatus.PENDING,
                "post_id": None,
                "error": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            data.setdefault("intents", {})[intent_id] = entry
            self._save(data)
            return entry

    def update_intent(
        self,
        intent_id: str,
        status: Optional[str] = None,
        post_id: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Atomically transition intent status upon provider confirmation or failure."""
        with _INTENT_LOCK:
            data = self._load()
            entry = data.get("intents", {}).get(intent_id)
            if not entry:
                return None
            if status is not None:
                entry["status"] = status
            if post_id is not None:
                entry["post_id"] = post_id
            if error is not None:
                entry["error"] = error
            entry["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save(data)
            return entry

    def get_intent(self, intent_id: str) -> Optional[Dict[str, Any]]:
        with _INTENT_LOCK:
            return self._load().get("intents", {}).get(intent_id)

    def list_intents(self) -> List[Dict[str, Any]]:
        with _INTENT_LOCK:
            return list(self._load().get("intents", {}).values())

_global_intent_journal = IntentJournal()

def get_intent_journal() -> IntentJournal:
    return _global_intent_journal
