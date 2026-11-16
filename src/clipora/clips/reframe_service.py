"""On-demand reframe dispatch for individual clips."""

from pathlib import Path
from typing import Dict, Any
from clipora.clips.clip_locks import clip_lock
from clipora.clips.clip_resolve import resolve_clip_paths
from clipora.jobs.job_artifacts import get_job_dir, read_job_metadata, update_job_metadata
from clipora.pipeline.reframe.reframe import reframe_video_to_vertical
from clipora.core.errors import JobNotFoundError

async def reframe_clip_on_demand(
    job_id: str,
    clip_index: int,
    reframe_mode: str = "auto",
) -> Dict[str, Any]:
    """Re-render 9:16 vertical crop for a specific clip under clip_lock."""
    job_dir = get_job_dir(job_id)
    if not job_dir.is_dir():
        raise JobNotFoundError(job_id)

    async with clip_lock(job_dir, clip_index):
        meta = read_job_metadata(job_id)
        if not meta or clip_index >= len(meta.clips):
            raise JobNotFoundError(f"{job_id}/clip/{clip_index}")

        clip = meta.clips[clip_index]
        paths = resolve_clip_paths(job_dir, clip_index)
        source_slice = paths.source_slice
        if not source_slice.is_file():
            source_slice = paths.get_preferred_render_source()

        out_vertical = paths.vertical_video
        reframe_video_to_vertical(
            input_video=source_slice,
            output_video=out_vertical,
            mode=reframe_mode,
        )

        clip.reframe_mode = reframe_mode
        update_job_metadata(job_id, {"clips": meta.clips})

        return {
            "status": "success",
            "job_id": job_id,
            "clip_index": clip_index,
            "reframe_mode": reframe_mode,
            "output_path": str(out_vertical),
        }
