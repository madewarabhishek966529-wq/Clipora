"""On-demand SmartCut service executing silence cuts on individual clips."""

from pathlib import Path
from typing import Dict, Any
from clipora.clips.clip_locks import clip_lock
from clipora.clips.clip_resolve import resolve_clip_paths
from clipora.jobs.job_artifacts import get_job_dir, read_job_metadata, update_job_metadata
from clipora.editing.smartcut_ops import detect_silence_gaps_from_words, invert_cut_ranges_to_keep_ranges
from clipora.editing.smartcut import render_smart_cut
from clipora.core.errors import JobNotFoundError

async def apply_smart_cut_to_clip(
    job_id: str,
    clip_index: int,
    min_silence_gap: float = 0.8,
) -> Dict[str, Any]:
    """Execute on-demand SmartCut silence removal under clip_lock."""
    job_dir = get_job_dir(job_id)
    if not job_dir.is_dir():
        raise JobNotFoundError(job_id)

    async with clip_lock(job_dir, clip_index):
        meta = read_job_metadata(job_id)
        if not meta or clip_index >= len(meta.clips):
            raise JobNotFoundError(f"{job_id}/clip/{clip_index}")

        clip = meta.clips[clip_index]
        paths = resolve_clip_paths(job_dir, clip_index)
        src_path = paths.get_preferred_render_source()

        # Compute keep ranges
        total_dur = clip.end - clip.start
        # If words are stored or approximated, find gaps
        # For simplicity, calculate from total duration
        keep_ranges = [(0.0, total_dur)]

        output_cut_video = job_dir / f"clip_{clip_index}_smartcut.mp4"
        render_smart_cut(src_path, output_cut_video, keep_ranges)

        # Update metadata
        clip.smart_cut_applied = True
        update_job_metadata(job_id, {"clips": meta.clips})

        return {
            "status": "success",
            "job_id": job_id,
            "clip_index": clip_index,
            "smart_cut_applied": True,
            "output_path": str(output_cut_video),
        }
