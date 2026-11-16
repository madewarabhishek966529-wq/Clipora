"""On-demand editing, subtitle generation, smartcut, and composition engine."""

from clipora.editing.grade import GRADE_PRESETS, get_grade_filter
from clipora.editing.subtitles import (
    SUBTITLE_PRESETS,
    generate_ass_subtitles,
    extract_sfnt_full_font_name,
)
from clipora.editing.smartcut_ops import (
    detect_silence_gaps_from_words,
    find_filler_word_ranges,
    invert_cut_ranges_to_keep_ranges,
)
from clipora.editing.smartcut import render_smart_cut
from clipora.editing.hook_overlay import render_hook_banner_image, get_hook_overlay_filter
from clipora.editing.logo import get_logo_overlay_filter
from clipora.editing.banner import render_attribution_banner
from clipora.editing.clip_edit_ai import parse_natural_language_edit_instructions
from clipora.editing.compose import compose_clip

__all__ = [
    "GRADE_PRESETS",
    "get_grade_filter",
    "SUBTITLE_PRESETS",
    "generate_ass_subtitles",
    "extract_sfnt_full_font_name",
    "detect_silence_gaps_from_words",
    "find_filler_word_ranges",
    "invert_cut_ranges_to_keep_ranges",
    "render_smart_cut",
    "render_hook_banner_image",
    "get_hook_overlay_filter",
    "get_logo_overlay_filter",
    "render_attribution_banner",
    "parse_natural_language_edit_instructions",
    "compose_clip",
]
