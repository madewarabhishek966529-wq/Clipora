"""SmartCut orchestrator: Auto-Editor & FFmpeg filter graph silence removal."""

import threading
from pathlib import Path
from typing import List, Tuple, Dict, Any
from clipora.media.encode import x264_video_args, aac_audio_args
from clipora.media.ffmpeg_exec import run_ffmpeg
from clipora.editing.smartcut_ops import (
    detect_silence_gaps_from_words,
    find_filler_word_ranges,
    invert_cut_ranges_to_keep_ranges,
)
from clipora.storage.atomic import atomic_write_json

# Threading lock guarding smartcut execution inside worker threads
_clip_lock = threading.Lock()

def render_smart_cut(
    input_video: Path | str,
    output_video: Path | str,
    keep_ranges: List[Tuple[float, float]],
) -> Path:
    """Render cut video by concatenating keep_ranges using FFmpeg filter complex."""
    in_p = Path(input_video).resolve()
    out_p = Path(output_video).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)

    if not keep_ranges:
        return in_p

    # If only 1 range spanning the whole video, copy or symlink
    if len(keep_ranges) == 1 and keep_ranges[0][0] <= 0.05:
        # Single range, simple trim
        s, e = keep_ranges[0]
        args = [
            "-y",
            "-ss", f"{s:.3f}",
            "-to", f"{e:.3f}",
            "-i", str(in_p),
            *x264_video_args(crf=18, preset="fast"),
            *aac_audio_args(),
            str(out_p),
        ]
        run_ffmpeg(args)
        return out_p

    filter_chunks = []
    concat_inputs = []
    for idx, (start, end) in enumerate(keep_ranges):
        filter_chunks.append(f"[0:v]trim=start={start:.3f}:end={end:.3f},setpts=PTS-STARTPTS[v{idx}]")
        filter_chunks.append(f"[0:a]atrim=start={start:.3f}:end={end:.3f},asetpts=PTS-STARTPTS[a{idx}]")
        concat_inputs.append(f"[v{idx}][a{idx}]")

    num_parts = len(keep_ranges)
    filter_complex = ";".join(filter_chunks) + f";{''.join(concat_inputs)}concat=n={num_parts}:v=1:a=1[outv][outa]"

    args = [
        "-y",
        "-i", str(in_p),
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "[outa]",
        *x264_video_args(crf=18, preset="fast"),
        *aac_audio_args(),
        str(out_p),
    ]

    with _clip_lock:
        run_ffmpeg(args)

    return out_p
