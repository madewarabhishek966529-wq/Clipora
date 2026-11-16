"""Brand logo watermark overlay positioning and opacity filters."""

from pathlib import Path
from typing import Dict, Tuple

# Scale presets: width in pixels for 1080x1920 canvas
LOGO_SCALES: Dict[str, int] = {
    "S": 120,
    "M": 180,
    "L": 260,
}

def get_logo_overlay_filter(
    logo_path: Path | str,
    position: str = "top-right",
    scale_size: str = "M",
    opacity: float = 0.85,
    margin_px: int = 40,
) -> Tuple[str, str]:
    """Return (logo_filter_prep, overlay_expression) for FFmpeg complex filter."""
    norm_path = str(Path(logo_path).resolve()).replace("\\", "/")
    target_w = LOGO_SCALES.get(scale_size.upper(), 180)

    # Scale logo and adjust opacity (alpha)
    prep_filter = f"format=rgba,colorchannelmixer=aa={opacity:.2f},scale={target_w}:-1"

    # Coordinate mapping:
    # W, H = main video dimensions, w, h = overlay dimensions
    pos = position.lower()
    if pos == "top-left":
        overlay_coord = f"{margin_px}:{margin_px}"
    elif pos == "top-right":
        overlay_coord = f"W-w-{margin_px}:{margin_px}"
    elif pos == "bottom-left":
        overlay_coord = f"{margin_px}:H-h-{margin_px}"
    elif pos == "bottom-right":
        overlay_coord = f"W-w-{margin_px}:H-h-{margin_px}"
    elif pos == "center-top":
        overlay_coord = f"(W-w)/2:{margin_px}"
    elif pos == "center-bottom":
        overlay_coord = f"(W-w)/2:H-h-{margin_px}"
    else:
        overlay_coord = f"W-w-{margin_px}:{margin_px}"

    return prep_filter, overlay_coord
