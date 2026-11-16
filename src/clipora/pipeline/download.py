"""yt-dlp multi-client downloader with fallback clients and cookie support."""

import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, Callable
import yt_dlp
from clipora.core.errors import JobExecutionError
from clipora.core.netutil import validate_url_ssrf_safe
from clipora.media.ffmpeg_exec import find_executable

COOKIE_PATH = Path("data/cookies.txt")

# Client fallback chains prioritized to bypass YouTube 429 bot-block challenges
PLAYER_CLIENT_CHAINS = [
    ["android", "ios", "mweb"],
    ["android"],
    ["ios"],
    ["mweb"],
    ["default"],
]

def download_video(
    url: str,
    output_dir: Path | str,
    target_filename: str = "source.mp4",
    progress_callback: Optional[Callable[[float], None]] = None,
) -> Tuple[Path, Dict[str, Any]]:
    """Download video from URL using yt-dlp with player client fallback and SSRF safety re-check.
    
    Returns:
        (downloaded_file_path, video_metadata_dict)
    """
    # 1. Authoritative pre-execution SSRF re-check
    validate_url_ssrf_safe(url)

    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    final_output_path = out_dir / target_filename
    out_tmpl = str(out_dir / "source.%(ext)s")

    ffmpeg_bin = find_executable("ffmpeg")

    def ytdl_progress_hook(d):
        if d.get("status") == "downloading":
            p_str = d.get("_percent_str", "").strip()
            s_str = d.get("_speed_str", "").strip()
            eta_str = d.get("_eta_str", "").strip()
            print(f"[DOWNLOAD] {p_str} at {s_str} ETA {eta_str}", flush=True)
            if progress_callback:
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes") or 0
                fraction = (downloaded / total) if total > 0 else 0.5
                progress_callback(5.0 + fraction * 20.0)
        elif d.get("status") == "finished":
            print("[DOWNLOAD] 100% Download finished. Merging audio/video streams with FFmpeg...", flush=True)
            if progress_callback:
                progress_callback(25.0)

    last_error: Exception | None = None

    for client_list in PLAYER_CLIENT_CHAINS:
        ydl_opts: Dict[str, Any] = {
            # Prefer <=1080p for fast downloading and social shorts repurposing
            "format": "best[height<=1080]/bestvideo[height<=1080]+bestaudio/best",
            "outtmpl": out_tmpl,
            "merge_output_format": "mp4",
            "noplaylist": True,
            "overwrites": True,
            "ffmpeg_location": ffmpeg_bin,
            "progress_hooks": [ytdl_progress_hook],
            "extractor_args": {
                "youtube": {
                    "player_client": client_list,
                }
            },
        }

        # Apply Netscape cookies if available
        if COOKIE_PATH.is_file() and COOKIE_PATH.stat().st_size > 0:
            ydl_opts["cookiefile"] = str(COOKIE_PATH.resolve())

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                # Find output mp4
                if final_output_path.is_file():
                    return final_output_path, info
                # If merged under another extension, check files in directory
                for candidate in out_dir.glob("source.*"):
                    if candidate.is_file() and candidate.suffix.lower() in (".mp4", ".mkv", ".webm"):
                        return candidate, info
        except Exception as e:
            last_error = e
            print(f"[DOWNLOAD] Client fallback '{client_list}' encountered error: {e}. Switching to next client...", flush=True)
            continue

    raise JobExecutionError(
        f"Failed to download video from URL across all client fallback chains: {last_error}",
        details={"url": url, "error": str(last_error)},
    )
