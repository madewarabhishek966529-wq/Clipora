"""Conservative preflight disk space and resource estimator."""

import os
import shutil
from pathlib import Path
from clipora.core.errors import ValidationError

# Safety multipliers
ESTIMATED_BYTES_PER_SECOND_VIDEO = 2_500_000 // 8   # ~2.5 Mbps 1080p video (~312 KB/s)
ESTIMATED_BYTES_PER_SECOND_AUDIO = 32_000           # 16kHz 16-bit mono FLAC (~32 KB/s)
ESTIMATED_BYTES_PER_CLIP = 35_000_000               # ~35 MB per 45s vertical short
MIN_DISK_HEADROOM_BYTES = 1_500_000_000             # 1.5 GB minimum headroom

def check_disk_space(target_path: Path | str, required_bytes: int) -> bool:
    """Return True if target volume has at least required_bytes free."""
    p = Path(target_path).resolve()
    target_dir = p if p.is_dir() else p.parent
    usage = shutil.disk_usage(target_dir)
    return usage.free >= required_bytes

def estimate_required_disk_bytes(duration_seconds: float, expected_clips: int = 10) -> int:
    """Calculate conservative upper-bound disk requirement for a processing run."""
    source_bytes = int(duration_seconds * ESTIMATED_BYTES_PER_SECOND_VIDEO)
    audio_bytes = int(duration_seconds * ESTIMATED_BYTES_PER_SECOND_AUDIO)
    clips_bytes = expected_clips * ESTIMATED_BYTES_PER_CLIP
    scratch_bytes = 500_000_000  # 500 MB temporary buffers
    return source_bytes + audio_bytes + clips_bytes + scratch_bytes + MIN_DISK_HEADROOM_BYTES

def run_preflight_check(target_dir: Path | str, duration_seconds: float, max_duration_sec: float = 14400.0) -> None:
    """Validate video duration and disk headroom before pipeline execution.
    
    Raises:
        ValidationError if constraints are violated.
    """
    if duration_seconds < 15.0:
        raise ValidationError(f"Video duration ({duration_seconds:.1f}s) is too short for clipping (minimum 15s).")

    if duration_seconds > max_duration_sec:
        raise ValidationError(
            f"Video duration ({duration_seconds:.1f}s) exceeds maximum allowed duration ({max_duration_sec:.1f}s)."
        )

    needed_bytes = estimate_required_disk_bytes(duration_seconds)
    if not check_disk_space(target_dir, needed_bytes):
        free = shutil.disk_usage(target_dir).free
        raise ValidationError(
            f"Insufficient disk space. Needed ~{needed_bytes / 1e9:.2f} GB, available: {free / 1e9:.2f} GB."
        )
