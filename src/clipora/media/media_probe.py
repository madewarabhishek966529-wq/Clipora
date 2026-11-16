"""Media probing utilities using ffprobe JSON outputs."""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from clipora.core.errors import JobExecutionError
from clipora.media.ffmpeg_exec import run_ffprobe

class MediaInfo:
    def __init__(self, raw: Dict[str, Any]):
        self.raw = raw
        format_info = raw.get("format", {})
        self.duration: float = float(format_info.get("duration", 0.0))
        self.size_bytes: int = int(format_info.get("size", 0))
        self.bit_rate: int = int(format_info.get("bit_rate", 0))

        # Extract video stream info
        self.has_video = False
        self.width: int = 0
        self.height: int = 0
        self.fps: float = 0.0
        self.video_codec: str = ""

        for stream in raw.get("streams", []):
            if stream.get("codec_type") == "video" and not self.has_video:
                self.has_video = True
                self.width = int(stream.get("width", 0))
                self.height = int(stream.get("height", 0))
                self.video_codec = stream.get("codec_name", "")
                r_frame_rate = stream.get("r_frame_rate", "30/1")
                try:
                    num, den = r_frame_rate.split("/")
                    self.fps = float(num) / float(den) if float(den) != 0 else 30.0
                except (ValueError, ZeroDivisionError):
                    self.fps = 30.0

        # Extract audio stream info
        self.has_audio = False
        self.sample_rate: int = 0
        self.channels: int = 0
        for stream in raw.get("streams", []):
            if stream.get("codec_type") == "audio" and not self.has_audio:
                self.has_audio = True
                self.sample_rate = int(stream.get("sample_rate", 0))
                self.channels = int(stream.get("channels", 0))

    @property
    def is_landscape(self) -> bool:
        return self.width > self.height

    @property
    def is_vertical(self) -> bool:
        return self.height > self.width

def probe_media(file_path: str | Path) -> MediaInfo:
    """Probe media file and return structured MediaInfo object."""
    p = Path(file_path)
    if not p.is_file():
        raise JobExecutionError(f"Media file does not exist: {file_path}")

    args = [
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(p),
    ]

    stdout = run_ffprobe(args)
    try:
        data = json.loads(stdout)
        return MediaInfo(data)
    except json.JSONDecodeError as e:
        raise JobExecutionError(f"Failed to parse ffprobe JSON output: {e}") from e
