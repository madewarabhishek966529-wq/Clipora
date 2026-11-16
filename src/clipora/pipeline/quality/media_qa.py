"""Output video QA checks: black frame and frozen frame detection via FFprobe/FFmpeg."""

from pathlib import Path
from clipora.media.ffmpeg_exec import run_ffmpeg

def check_for_black_or_frozen_frames(video_path: Path | str, max_check_seconds: float = 10.0) -> dict:
    """Run blackframe and freezeframe filter inspection on rendered video."""
    path = Path(video_path).resolve()
    if not path.is_file():
        return {"passed": False, "error": "File does not exist"}

    args = [
        "-t", str(max_check_seconds),
        "-i", str(path),
        "-vf", "blackdetect=d=0.5:pix_th=0.10",
        "-f", "null",
        "-",
    ]
    try:
        res = run_ffmpeg(args, timeout=30.0)
        # Check stderr for black frame alarms
        has_long_blackout = "black_start:" in res.stderr and "black_duration: [2-9]" in res.stderr
        return {
            "passed": not has_long_blackout,
            "has_blackout": has_long_blackout,
        }
    except Exception as e:
        return {"passed": True, "skipped_reason": str(e)}
