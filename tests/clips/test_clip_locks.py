"""Unit tests for asyncio per-clip locks."""

import asyncio
import pytest
from clipora.clips.clip_locks import clip_lock

@pytest.mark.asyncio
async def test_clip_locks_serializes_same_clip(tmp_path):
    job_dir = tmp_path / "job_123"
    job_dir.mkdir()
    clip_index = 0

    execution_order = []

    async def worker(worker_id: int, delay: float):
        async with clip_lock(job_dir, clip_index):
            execution_order.append(f"start_{worker_id}")
            await asyncio.sleep(delay)
            execution_order.append(f"end_{worker_id}")

    # Launch two workers competing for same clip
    await asyncio.gather(
        worker(1, 0.05),
        worker(2, 0.01),
    )

    # They must run serialized, not interleaved
    assert execution_order == ["start_1", "end_1", "start_2", "end_2"] or \
           execution_order == ["start_2", "end_2", "start_1", "end_1"]
