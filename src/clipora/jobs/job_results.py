"""Job results, clip summaries, and command builders."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from clipora.core.clip_schema import JobMetadata, ViralClip
from clipora.jobs.job_artifacts import read_job_metadata, get_job_dir

LANGUAGE_MAP = {
    "en": "English",
    "it": "Italian",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "pt": "Portuguese",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
}

def format_timestamp_display(seconds: float) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    total_sec = int(seconds)
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    secs = total_sec % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def get_job_summary(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve high-level summary of job artifacts and candidate clips."""
    meta = read_job_metadata(job_id)
    if not meta:
        return None

    job_dir = get_job_dir(job_id)
    clips_summary = []
    for idx, clip in enumerate(meta.clips):
        clip_path = job_dir / f"clip_{idx}.mp4"
        thumb_path = job_dir / f"clip_{idx}_thumb.jpg"
        clips_summary.append({
            "index": idx,
            "start": clip.start,
            "end": clip.end,
            "duration": round(clip.end - clip.start, 2),
            "start_formatted": format_timestamp_display(clip.start),
            "end_formatted": format_timestamp_display(clip.end),
            "viral_score": clip.viral_score,
            "viral_reason": clip.viral_reason,
            "viral_hook_text": clip.viral_hook_text,
            "video_title": clip.video_title_for_youtube_short,
            "exists_on_disk": clip_path.is_file(),
            "has_thumbnail": thumb_path.is_file(),
        })

    return {
        "job_id": meta.job_id,
        "status": meta.status.value,
        "progress_percent": meta.progress_percent,
        "current_phase": meta.current_phase,
        "source_url": meta.source_url,
        "video_title": meta.video_title,
        "video_duration": meta.video_duration,
        "created_at": meta.created_at,
        "updated_at": meta.updated_at,
        "completed_at": meta.completed_at,
        "error_message": meta.error_message,
        "clip_count": len(clips_summary),
        "clips": clips_summary,
    }
