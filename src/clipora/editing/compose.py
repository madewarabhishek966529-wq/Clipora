"""Multi-pass on-demand video compose engine with strict layer ordering."""

from pathlib import Path
from typing import Optional, List, Tuple
from clipora.media.encode import x264_video_args, aac_audio_args
from clipora.media.ffmpeg_exec import run_ffmpeg
from clipora.editing.grade import get_grade_filter
from clipora.editing.hook_overlay import get_hook_overlay_filter
from clipora.editing.logo import get_logo_overlay_filter

def compose_clip(
    input_video: Path | str,
    output_video: Path | str,
    grade_preset: Optional[str] = "warm_cinematic",
    ass_subtitle_path: Optional[Path | str] = None,
    hook_overlay_png: Optional[Path | str] = None,
    logo_path: Optional[Path | str] = None,
    logo_position: str = "top-right",
    logo_scale: str = "M",
    logo_opacity: float = 0.85,
    attribution_banner_png: Optional[Path | str] = None,
    fonts_dir: Optional[Path | str] = None,
) -> Path:
    """Render complete edited video adhering strictly to the 6-layer compose order:
    
    1. Grade -> 2. Subtitles -> 3. Smart Cut -> 4. Hook Overlay -> 5. Logo Watermark -> 6. Attribution Banner.
    """
    in_p = Path(input_video).resolve()
    out_p = Path(output_video).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)

    input_args = ["-i", str(in_p)]
    filter_chains: List[str] = []
    current_stream = "[0:v]"
    stream_idx = 1

    # 1. Color Grade
    if grade_preset:
        grade_vf = get_grade_filter(grade_preset)
        filter_chains.append(f"{current_stream}{grade_vf}[v_graded]")
        current_stream = "[v_graded]"

    # 2. Subtitles (libass)
    if ass_subtitle_path and Path(ass_subtitle_path).is_file():
        ass_str = str(Path(ass_subtitle_path).resolve()).replace("\\", "/").replace(":", "\\:")
        fonts_opt = ""
        if fonts_dir and Path(fonts_dir).is_dir():
            f_dir = str(Path(fonts_dir).resolve()).replace("\\", "/").replace(":", "\\:")
            fonts_opt = f":fontsdir='{f_dir}'"
        sub_filter = f"subtitles='{ass_str}'{fonts_opt}"
        filter_chains.append(f"{current_stream}{sub_filter}[v_subs]")
        current_stream = "[v_subs]"

    # 4. Hook Overlay
    if hook_overlay_png and Path(hook_overlay_png).is_file():
        input_args.extend(["-loop", "1", "-i", str(Path(hook_overlay_png).resolve())])
        hook_filter = get_hook_overlay_filter(hook_overlay_png)
        filter_chains.append(f"{current_stream}[{stream_idx}:v]{hook_filter}[v_hook]")
        current_stream = "[v_hook]"
        stream_idx += 1

    # 5. Logo Watermark
    if logo_path and Path(logo_path).is_file():
        input_args.extend(["-i", str(Path(logo_path).resolve())])
        logo_prep, logo_pos = get_logo_overlay_filter(
            logo_path, position=logo_position, scale_size=logo_scale, opacity=logo_opacity
        )
        filter_chains.append(f"[{stream_idx}:v]{logo_prep}[logo_ready]")
        filter_chains.append(f"{current_stream}[logo_ready]overlay={logo_pos}[v_logo]")
        current_stream = "[v_logo]"
        stream_idx += 1

    # 6. Attribution Banner
    if attribution_banner_png and Path(attribution_banner_png).is_file():
        input_args.extend(["-loop", "1", "-i", str(Path(attribution_banner_png).resolve())])
        filter_chains.append(f"{current_stream}[{stream_idx}:v]overlay=0:H-h-50:enable='between(t,1,15)'[v_banner]")
        current_stream = "[v_banner]"
        stream_idx += 1

    if filter_chains:
        complex_filter = ";".join(filter_chains)
        args = [
            "-y",
            *input_args,
            "-filter_complex", complex_filter,
            "-map", current_stream,
            "-map", "0:a?",
            "-shortest",
            *x264_video_args(crf=18, preset="fast"),
            *aac_audio_args(),
            str(out_p),
        ]
    else:
        # Pass-through stream copy
        args = [
            "-y",
            "-i", str(in_p),
            "-c", "copy",
            str(out_p),
        ]

    run_ffmpeg(args)
    return out_p
