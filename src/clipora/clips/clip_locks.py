"""Re-entrant per-clip asyncio locks enforcing strict lock ordering hierarchy."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Dict, Tuple

_CLIP_LOCKS: Dict[Tuple[str, int], asyncio.Lock] = {}
_REGISTRY_LOCK = asyncio.Lock()

async def _get_or_create_lock(job_key: str, clip_index: int) -> asyncio.Lock:
    key = (job_key, clip_index)
    async with _REGISTRY_LOCK:
        if key not in _CLIP_LOCKS:
            _CLIP_LOCKS[key] = asyncio.Lock()
        return _CLIP_LOCKS[key]

@asynccontextmanager
async def clip_lock(job_dir: str | Path, clip_index: int) -> AsyncIterator[None]:
    """Outermost asyncio lock guarding all mutating operations on a specific physical clip."""
    job_key = str(Path(job_dir).resolve())
    lock = await _get_or_create_lock(job_key, clip_index)
    async with lock:
        yield
