"""Unified media encoding arguments across all Clipora rendering passes."""

def x264_video_args(crf: int = 18, preset: str = "medium") -> list[str]:
    """Canonical libx264 encoding recipe across all Clipora rendering passes."""
    return [
        "-c:v", "libx264",
        "-crf", str(crf),
        "-preset", preset,
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-threads", "0",
    ]

def aac_audio_args(bitrate: str = "192k") -> list[str]:
    """Canonical AAC audio encoding parameters."""
    return [
        "-c:a", "aac",
        "-b:a", bitrate,
        "-ar", "48000",
        "-ac", "2",
    ]

def flac_extract_args() -> list[str]:
    """Canonical 16 kHz mono FLAC audio extraction recipe for ASR."""
    return [
        "-vn",
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "flac",
    ]
