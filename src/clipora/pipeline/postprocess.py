"""Audio extraction, slice cutting, loudness normalization, and thumbnail extraction."""

from pathlib import Path
from typing import Optional
from clipora.media.encode import flac_extract_args, x264_video_args, aac_audio_args
from clipora.media.ffmpeg_exec import run_ffmpeg

def extract_flac_audio(video_path: Path | str, output_flac_path: Path | str) -> Path:
    """Extract 16 kHz mono FLAC audio from video for ASR."""
    out_p = Path(output_flac_path).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)

    args = [
        "-y",
        "-i", str(Path(video_path).resolve()),
        *flac_extract_args(),
        str(out_p),
    ]
    run_ffmpeg(args)
    return out_p

def cut_clip_slice(
    source_video: Path | str,
    output_slice: Path | str,
    start: float,
    end: float,
    fade_duration: float = 0.03,
) -> Path:
    """Cut an accurate video slice with anti-pop audio fades."""
    out_p = Path(output_slice).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)
    duration = max(0.1, end - start)

    # Audio fade filter
    audio_filter = f"afade=t=in:st=0:d={fade_duration},afade=t=out:st={duration - fade_duration:.3f}:d={fade_duration}"

    args = [
        "-y",
        "-ss", f"{start:.3f}",
        "-t", f"{duration:.3f}",
        "-i", str(Path(source_video).resolve()),
        *x264_video_args(crf=18, preset="fast"),
        "-af", audio_filter,
        *aac_audio_args(),
        str(out_p),
    ]
    run_ffmpeg(args)
    return out_p

def extract_thumbnail(
    video_path: Path | str,
    output_thumb_path: Path | str,
    timestamp: Optional[float] = None,
) -> Path:
    """Extract a representative JPEG thumbnail frame from video."""
    out_p = Path(output_thumb_path).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)

    ss_args = ["-ss", f"{timestamp:.3f}"] if timestamp is not None else ["-ss", "1.0"]

    args = [
        "-y",
        *ss_args,
        "-i", str(Path(video_path).resolve()),
        "-vframes", "1",
        "-q:v", "2",
        str(out_p),
    ]
    run_ffmpeg(args)
    return out_p

def apply_ebu_r128_loudnorm(
    input_video: Path | str,
    output_video: Path | str,
    target_i: float = -14.0,
    target_tp: float = -1.5,
    target_lra: float = 11.0,
) -> Path:
    """Normalize audio loudness to social video streaming target standard (EBU R128)."""
    out_p = Path(output_video).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)

    filter_str = f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}"
    args = [
        "-y",
        "-i", str(Path(input_video).resolve()),
        "-c:v", "copy",
        "-af", filter_str,
        *aac_audio_args(),
        str(out_p),
    ]
    run_ffmpeg(args)
    return out_p
