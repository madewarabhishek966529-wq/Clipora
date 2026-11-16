"""Color grading preset filter matrices for FFmpeg."""

from typing import Dict

GRADE_PRESETS: Dict[str, str] = {
    "warm_cinematic": "eq=contrast=1.12:brightness=0.02:saturation=1.25,colorbalance=rs=0.08:gs=0.02:bs=-0.06",
    "cool_crisp": "eq=contrast=1.15:brightness=0.01:saturation=1.10,colorbalance=rs=-0.04:gs=0.01:bs=0.08",
    "neutral_punch": "eq=contrast=1.18:brightness=0.00:saturation=1.15",
    "vivid_pop": "eq=contrast=1.20:brightness=0.03:saturation=1.40",
}

def get_grade_filter(preset_name: str) -> str:
    """Return FFmpeg video filter expression for the specified grading preset."""
    return GRADE_PRESETS.get(preset_name, GRADE_PRESETS["warm_cinematic"])
