"""Atomic FFmpeg & FFprobe runner with timeout and error diagnostics."""

import os
import shutil
import subprocess
from typing import List, Tuple
from clipora.core.errors import JobExecutionError

def find_executable(name: str) -> str:
    """Locate binary on PATH or via common environment variables or imageio_ffmpeg."""
    custom = os.getenv(f"{name.upper()}_PATH")
    if custom and os.path.isfile(custom):
        return custom
    found = shutil.which(name)
    if found:
        return found
    if name == "ffmpeg":
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except (ImportError, Exception):
            pass
    return name

def run_ffmpeg(args: List[str], timeout: float | None = 600.0) -> subprocess.CompletedProcess[str]:
    """Execute FFmpeg command synchronously with watchdog timeout."""
    ffmpeg_bin = find_executable("ffmpeg")
    full_cmd = [ffmpeg_bin] + args
    try:
        res = subprocess.run(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
        if res.returncode != 0:
            err_msg = res.stderr[-1000:] if res.stderr else "Unknown FFmpeg error"
            raise JobExecutionError(
                f"FFmpeg command failed with return code {res.returncode}: {err_msg}",
                exit_code=res.returncode,
                details={"cmd": full_cmd, "stderr": res.stderr},
            )
        return res
    except FileNotFoundError as e:
        raise JobExecutionError(f"FFmpeg binary not found on system PATH: {e}") from e
    except subprocess.TimeoutExpired as e:
        raise JobExecutionError(f"FFmpeg command timed out after {timeout} seconds.", details={"cmd": full_cmd}) from e

def run_ffprobe(args: List[str], timeout: float = 30.0) -> str:
    """Execute FFprobe command and return stdout as string."""
    ffprobe_bin = find_executable("ffprobe")
    full_cmd = [ffprobe_bin] + args
    try:
        res = subprocess.run(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
        if res.returncode != 0:
            raise JobExecutionError(
                f"FFprobe command failed with return code {res.returncode}",
                exit_code=res.returncode,
                details={"stderr": res.stderr},
            )
        return res.stdout
    except FileNotFoundError as e:
        raise JobExecutionError(f"FFprobe binary not found on system PATH: {e}") from e
    except subprocess.TimeoutExpired as e:
        raise JobExecutionError(f"FFprobe command timed out after {timeout} seconds.") from e
