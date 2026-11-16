"""yt-dlp multi-client downloader with fallback clients and cookie support."""

import os
from pathlib import Path
from typing import Dict, Any, Tuple
import yt_dlp
from clipora.core.errors import JobExecutionError
from clipora.core.netutil import validate_url_ssrf_safe

COOKIE_PATH = Path("data/cookies.txt")

PLAYER_CLIENT_CHAINS = [
    ["default"],
    ["tv", "tv_embedded"],
    ["web_safari"],
]

def download_video(
    url: str,
    output_dir: Path | str,
    target_filename: str = "source.mp4",
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

    last_error: Exception | None = None

    for client_list in PLAYER_CLIENT_CHAINS:
        ydl_opts: Dict[str, Any] = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": out_tmpl,
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "overwrites": True,
        }

        # Apply Netscape cookies if available
        if COOKIE_PATH.is_file() and COOKIE_PATH.stat().st_size > 0:
            ydl_opts["cookiefile"] = str(COOKIE_PATH.resolve())

        # Configure player clients if non-default
        if client_list != ["default"]:
            ydl_opts["extractor_args"] = {
                "youtube": {
                    "player_client": client_list,
                }
            }

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
            continue

    raise JobExecutionError(
        f"Failed to download video from URL across all client fallback chains: {last_error}",
        details={"url": url, "error": str(last_error)},
    )
