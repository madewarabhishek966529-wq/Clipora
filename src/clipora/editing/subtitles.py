"""ASS karaoke subtitle generator with 6 style presets and SFNT font discovery."""

import struct
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from clipora.pipeline.transcription.diarization import TranscriptWord

# 6 Professional Animated ASS Karaoke Presets
SUBTITLE_PRESETS: Dict[str, Dict[str, str]] = {
    "hormozi_bold": {
        "Fontname": "Montserrat",
        "Fontsize": "72",
        "PrimaryColour": "&H0000FFFF",  # Vivid Yellow
        "SecondaryColour": "&H00FFFFFF",# Highlight White
        "OutlineColour": "&H00000000",  # Jet Black Outline
        "BackColour": "&H80000000",
        "Bold": "-1",
        "Outline": "4",
        "Shadow": "2",
        "Alignment": "2",               # Bottom-Center
        "MarginV": "420",
    },
    "classic_white": {
        "Fontname": "Arial",
        "Fontsize": "64",
        "PrimaryColour": "&H00FFFFFF",  # Pure White
        "SecondaryColour": "&H0000FFFF",
        "OutlineColour": "&H00000000",
        "BackColour": "&H00000000",
        "Bold": "-1",
        "Outline": "3",
        "Shadow": "1",
        "Alignment": "2",
        "MarginV": "380",
    },
    "neon_cyan": {
        "Fontname": "Arial Black",
        "Fontsize": "68",
        "PrimaryColour": "&H00FFFF00",  # Electric Cyan (&HAABBGGRR)
        "SecondaryColour": "&H00FFFFFF",
        "OutlineColour": "&H00000000",
        "BackColour": "&H00000000",
        "Bold": "-1",
        "Outline": "4",
        "Shadow": "3",
        "Alignment": "2",
        "MarginV": "400",
    },
    "red_punch": {
        "Fontname": "Impact",
        "Fontsize": "74",
        "PrimaryColour": "&H000000FF",  # Bright Red
        "SecondaryColour": "&H00FFFFFF",
        "OutlineColour": "&H00FFFFFF",  # White outline
        "BackColour": "&H00000000",
        "Bold": "-1",
        "Outline": "4",
        "Shadow": "2",
        "Alignment": "2",
        "MarginV": "420",
    },
    "minimal_dark": {
        "Fontname": "Arial",
        "Fontsize": "58",
        "PrimaryColour": "&H00E0E0E0",
        "SecondaryColour": "&H00FFFFFF",
        "OutlineColour": "&H00202020",
        "BackColour": "&H60000000",
        "Bold": "0",
        "Outline": "2",
        "Shadow": "0",
        "Alignment": "2",
        "MarginV": "360",
    },
    "pastel_pop": {
        "Fontname": "Arial",
        "Fontsize": "66",
        "PrimaryColour": "&H00D478FF",  # Pastel Pink
        "SecondaryColour": "&H00FFFF80",
        "OutlineColour": "&H00402040",
        "BackColour": "&H00000000",
        "Bold": "-1",
        "Outline": "3",
        "Shadow": "2",
        "Alignment": "2",
        "MarginV": "390",
    },
}

def extract_sfnt_full_font_name(font_path: Path | str) -> Optional[str]:
    """Parse TrueType/OpenType SFNT table to extract font Name ID 4 (Full Name)."""
    p = Path(font_path)
    if not p.is_file():
        return None
    try:
        with open(p, "rb") as f:
            header = f.read(12)
            if len(header) < 12:
                return None
            num_tables = struct.unpack(">H", header[4:6])[0]
            name_table_offset = None
            for _ in range(num_tables):
                entry = f.read(16)
                if len(entry) < 16:
                    break
                tag, check_sum, offset, length = struct.unpack(">4sIII", entry)
                if tag == b"name":
                    name_table_offset = offset
                    break

            if name_table_offset is None:
                return None

            f.seek(name_table_offset)
            name_header = f.read(6)
            if len(name_header) < 6:
                return None
            format_num, count, string_offset = struct.unpack(">HHH", name_header)
            storage_offset = name_table_offset + string_offset

            for _ in range(count):
                rec = f.read(12)
                if len(rec) < 12:
                    break
                platform_id, enc_id, lang_id, name_id, length, offset = struct.unpack(">HHHHHH", rec)
                if name_id == 4:  # Full font name
                    curr = f.tell()
                    f.seek(storage_offset + offset)
                    raw_bytes = f.read(length)
                    f.seek(curr)
                    # Decode UTF-16BE or ASCII
                    try:
                        return raw_bytes.decode("utf-16-be").strip()
                    except UnicodeDecodeError:
                        return raw_bytes.decode("utf-8", errors="ignore").strip()
    except Exception:
        pass
    return None

def format_ass_time(seconds: float) -> str:
    """Format seconds into ASS timestamp: H:MM:SS.cc"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def generate_ass_subtitles(
    words: List[TranscriptWord],
    output_path: Path | str,
    preset_name: str = "hormozi_bold",
    words_per_line: int = 4,
    clip_start_offset: float = 0.0,
) -> Path:
    """Generate an Advanced SubStation Alpha (.ass) file with word-level karaoke tags."""
    out_p = Path(output_path).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)

    style = SUBTITLE_PRESETS.get(preset_name, SUBTITLE_PRESETS["hormozi_bold"])

    lines: List[str] = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,{style['Fontname']},{style['Fontsize']},{style['PrimaryColour']},{style['SecondaryColour']},{style['OutlineColour']},{style['BackColour']},{style['Bold']},0,0,0,100,100,0,0,1,{style['Outline']},{style['Shadow']},{style['Alignment']},50,50,{style['MarginV']},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    # Group words into bursts of words_per_line
    filtered_words = [
        w for w in words
        if w.end > clip_start_offset
    ]

    for i in range(0, len(filtered_words), words_per_line):
        burst = filtered_words[i : i + words_per_line]
        if not burst:
            continue

        line_start = max(0.0, burst[0].start - clip_start_offset)
        line_end = max(line_start + 0.1, burst[-1].end - clip_start_offset)

        # Build karaoke tags: {\k<duration_in_centiseconds>}Word
        k_text_parts = []
        for w in burst:
            dur_cs = int(round((w.end - w.start) * 100))
            dur_cs = max(1, dur_cs)
            w_text = w.punctuated_word or w.word
            k_text_parts.append(f"{{\\k{dur_cs}}}{w_text}")

        event_text = " ".join(k_text_parts)
        start_str = format_ass_time(line_start)
        end_str = format_ass_time(line_end)
        lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{event_text}")

    content = "\n".join(lines) + "\n"
    out_p.write_text(content, encoding="utf-8")
    return out_p
