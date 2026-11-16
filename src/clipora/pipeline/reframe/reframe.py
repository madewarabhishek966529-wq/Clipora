"""9:16 Vertical reframing render orchestrator."""

from pathlib import Path
from typing import Optional, List
import logging
from clipora.media.encode import x264_video_args, aac_audio_args
from clipora.media.ffmpeg_exec import run_ffmpeg
from clipora.media.media_probe import probe_media
from clipora.pipeline.reframe.reframe_ops import compute_9_16_crop_dimensions, collapse_scene_targets, clamp_crop_x
from clipora.pipeline.reframe.scene_detection import detect_scenes

logger = logging.getLogger("clipora.reframe")

def reframe_video_to_vertical(
    input_video: Path | str,
    output_video: Path | str,
    mode: str = "auto",
    static_auto: bool = True,
) -> Path:
    """Render 9:16 vertical short from landscape source video."""
    in_p = Path(input_video).resolve()
    out_p = Path(output_video).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)

    info = probe_media(in_p)
    source_w = info.width or 1920
    source_h = info.height or 1080

    crop_w, crop_h = compute_9_16_crop_dimensions(source_w, source_h)

    if mode == "disabled":
        # Letterbox landscape video into 1080x1920 vertical canvas
        vf = "scale=1080:-2,pad=1080:1920:0:(oh-ih)/2:black"
    else:
        # Tripod Auto framing: detect shot cuts and lock camera crop
        scenes = detect_scenes(in_p)
        if not scenes:
            scenes = [(0.0, info.duration)]

        # Calculate crop coordinates
        crop_x = clamp_crop_x(source_w / 2.0, crop_w, source_w)
        vf = f"crop={crop_w}:{crop_h}:{crop_x}:0,scale=1080:1920"

    args = [
        "-y",
        "-i", str(in_p),
        "-vf", vf,
        *x264_video_args(crf=18, preset="fast"),
        *aac_audio_args(),
        str(out_p),
    ]

    run_ffmpeg(args)
    return out_p
