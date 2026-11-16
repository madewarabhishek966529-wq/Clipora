"""Path resolution and artifact locator for individual clips."""

from pathlib import Path
from typing import Optional
from clipora.jobs.job_artifacts import get_job_dir

class ClipPaths:
    """Convenience container for all physical asset paths belonging to a clip."""

    def __init__(self, job_dir: Path, clip_index: int):
        self.job_dir = Path(job_dir).resolve()
        self.clip_index = clip_index

        self.source_slice = self.job_dir / f"source_{clip_index}.mp4"
        self.vertical_video = self.job_dir / f"vertical_{clip_index}.mp4"
        self.final_composed = self.job_dir / f"clip_{clip_index}.mp4"
        self.thumbnail = self.job_dir / f"clip_{clip_index}_thumb.jpg"
        self.ass_subtitles = self.job_dir / f"clip_{clip_index}.ass"
        self.srt_subtitles = self.job_dir / f"clip_{clip_index}.srt"
        self.smartcut_json = self.job_dir / f"clip_{clip_index}_smartcut.json"
        self.hook_image = self.job_dir / f"clip_{clip_index}_hook.png"
        self.source_audio = self.job_dir / f"clip_{clip_index}_audio.flac"

    def get_preferred_render_source(self) -> Path:
        """Return the highest fidelity source video available for dynamic on-demand compose."""
        if self.vertical_video.is_file():
            return self.vertical_video
        if self.source_slice.is_file():
            return self.source_slice
        if self.final_composed.is_file():
            return self.final_composed
        return self.source_slice

def resolve_clip_paths(job_id_or_dir: str | Path, clip_index: int) -> ClipPaths:
    """Resolve standard clip artifact paths given a job ID or output directory."""
    p = Path(job_id_or_dir)
    if not p.is_dir() and not str(p).startswith("/") and not (len(str(p)) > 1 and str(p)[1] == ":"):
        job_dir = get_job_dir(str(job_id_or_dir))
    else:
        job_dir = p
    return ClipPaths(job_dir, clip_index)
