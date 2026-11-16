"""Pillow-rendered hook overlay banners with animated entry."""

from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

def render_hook_banner_image(
    text: str,
    output_png_path: Path | str,
    canvas_w: int = 1080,
    banner_w: int = 920,
    font_size: int = 56,
    bg_rgba: Tuple[int, int, int, int] = (0, 0, 0, 200),
    text_color: str = "#FFFFFF",
    font_path: Optional[Path | str] = None,
) -> Path:
    """Render a high-impact hook title banner card onto a transparent PNG canvas."""
    out_p = Path(output_png_path).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)

    # Load font
    font = None
    if font_path and Path(font_path).is_file():
        try:
            font = ImageFont.truetype(str(font_path), font_size)
        except Exception:
            pass
    if font is None:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

    # Word wrapping
    words = text.strip().split()
    lines = []
    current_line = []

    # Create dummy draw to measure text
    dummy_img = Image.new("RGBA", (1, 1))
    draw_test = ImageDraw.Draw(dummy_img)

    for w in words:
        test_line = " ".join(current_line + [w])
        bbox = draw_test.textbbox((0, 0), test_line, font=font)
        line_w = bbox[2] - bbox[0]
        if line_w <= (banner_w - 60):  # 30px padding on each side
            current_line.append(w)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [w]
    if current_line:
        lines.append(" ".join(current_line))

    # Calculate banner dimensions
    line_height = int(font_size * 1.3)
    banner_h = (len(lines) * line_height) + 40  # 20px top/bottom padding

    # Create transparent full-width image
    img = Image.new("RGBA", (canvas_w, banner_h + 20), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw rounded rectangle in center
    left = (canvas_w - banner_w) // 2
    top = 10
    right = left + banner_w
    bottom = top + banner_h

    draw.rounded_rectangle([left, top, right, bottom], radius=24, fill=bg_rgba)

    # Draw centered text lines
    y = top + 20
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (canvas_w - text_w) // 2
        draw.text((x, y), line, font=font, fill=text_color)
        y += line_height

    img.save(out_p, "PNG")
    return out_p

def get_hook_overlay_filter(
    banner_png_path: Path | str,
    y_pos: int = 180,
    fade_duration: float = 0.4,
    show_duration: float = 4.5,
) -> str:
    """Generate FFmpeg overlay filter graph snippet with fade-in and fade-out animation."""
    p_str = str(Path(banner_png_path).resolve()).replace("\\", "/")
    # Overlay with fade expression
    # Display between t=0.2 and t=show_duration
    enable_expr = f"between(t,0.2,{show_duration})"
    return f"overlay=0:{y_pos}:enable='{enable_expr}'"
