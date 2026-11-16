"""Creator attribution banner rasterizer."""

from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

def render_attribution_banner(
    channel_handle: str,
    platform: str,
    output_path: Path | str,
    canvas_w: int = 1080,
    font_size: int = 36,
    bg_rgba: Tuple[int, int, int, int] = (15, 23, 42, 220), # Dark slate pill
    text_color: str = "#FFFFFF",
) -> Path:
    """Render a sleek attribution badge pill displaying creator handle and platform."""
    out_p = Path(output_path).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)

    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    display_text = f"{platform.upper()} • @{channel_handle.lstrip('@')}"

    dummy_img = Image.new("RGBA", (1, 1))
    draw_test = ImageDraw.Draw(dummy_img)
    bbox = draw_test.textbbox((0, 0), display_text, font=font)
    text_w = bbox[2] - bbox[0]
    pill_w = text_w + 60
    pill_h = font_size + 24

    img = Image.new("RGBA", (canvas_w, pill_h + 20), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    left = (canvas_w - pill_w) // 2
    top = 10
    right = left + pill_w
    bottom = top + pill_h

    draw.rounded_rectangle([left, top, right, bottom], radius=pill_h // 2, fill=bg_rgba)
    text_x = left + 30
    text_y = top + 12
    draw.text((text_x, text_y), display_text, font=font, fill=text_color)

    img.save(out_p, "PNG")
    return out_p
