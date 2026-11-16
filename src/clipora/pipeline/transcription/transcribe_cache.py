"""7-day SHA-256 keyed transcript disk cache."""

import hashlib
import time
from pathlib import Path
from typing import Any, Dict, Optional
from clipora.storage.atomic import atomic_write_json, read_json_safe

CACHE_DIR = Path("data/cache")
CACHE_TTL_SECONDS = 7 * 86400  # 7 days

def get_cache_key(source_identifier: str) -> str:
    """Compute SHA-256 hash for cache key."""
    return hashlib.sha256(source_identifier.strip().encode("utf-8")).hexdigest()

def get_cached_transcript(source_identifier: str) -> Optional[Dict[str, Any]]:
    """Retrieve cached transcript if present and not expired."""
    key = get_cache_key(source_identifier)
    cache_path = CACHE_DIR / f"{key}.json"
    if not cache_path.is_file():
        return None

    entry = read_json_safe(cache_path)
    if not entry or not isinstance(entry, dict):
        return None

    cached_at = entry.get("cached_at", 0)
    if time.time() - cached_at > CACHE_TTL_SECONDS:
        try:
            cache_path.unlink()
        except OSError:
            pass
        return None

    return entry.get("data")

def save_cached_transcript(source_identifier: str, data: Dict[str, Any]) -> None:
    """Store transcript in disk cache with timestamp."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = get_cache_key(source_identifier)
    cache_path = CACHE_DIR / f"{key}.json"
    entry = {
        "cached_at": time.time(),
        "source": source_identifier,
        "data": data,
    }
    atomic_write_json(cache_path, entry)
