"""Pure Python 9:16 vertical crop math, Tripod Mode scene collapse, and 1-Euro filter."""

import math
from typing import List, Tuple, Dict, Any, Optional

def compute_9_16_crop_dimensions(source_w: int, source_h: int) -> Tuple[int, int]:
    """Calculate the dimensions of a 9:16 vertical crop box for a given source frame."""
    target_aspect = 9.0 / 16.0
    crop_h = source_h
    crop_w = int(round(crop_h * target_aspect))

    # If crop_w exceeds source_w (e.g. source is already narrower than 9:16), fit by width
    if crop_w > source_w:
        crop_w = source_w
        crop_h = int(round(crop_w / target_aspect))

    # Ensure even dimensions for video codecs
    if crop_w % 2 != 0:
        crop_w -= 1
    if crop_h % 2 != 0:
        crop_h -= 1

    return crop_w, crop_h

def clamp_crop_x(center_x: float, crop_w: int, source_w: int) -> int:
    """Clamp the crop box center so the 9:16 box never extends outside the frame boundaries."""
    half_w = crop_w / 2.0
    min_x = half_w
    max_x = source_w - half_w

    clamped_center = max(min_x, min(max_x, center_x))
    top_left_x = int(round(clamped_center - half_w))
    return max(0, min(source_w - crop_w, top_left_x))

def classify_shot_type(
    face_counts: List[int],
    face_centers_x: List[float],
    source_w: int,
) -> str:
    """Classify scene shot type from distributed sample frames.
    
    Returns: 'TRACK' (single static speaker), 'WIDE' (multiple faces or wide movement), or 'GENERAL'
    """
    if not face_counts or max(face_counts) == 0:
        return "GENERAL"

    # If 2 or more faces detected across frames -> WIDE
    if max(face_counts) >= 2:
        return "WIDE"

    # If single face moves > 12% of frame width -> WIDE
    if face_centers_x and len(face_centers_x) > 1:
        spread = max(face_centers_x) - min(face_centers_x)
        if spread > (0.12 * source_w):
            return "WIDE"

    return "TRACK"

def collapse_scene_targets(
    detections: List[Dict[str, Any]],
    source_w: int,
    source_h: int,
) -> int:
    """Collapse all frame-level detections across a scene into a single fixed Tripod coordinate.
    
    The camera never moves within a shot (Tripod Mode).
    Returns: top_left_x coordinate of the static 9:16 crop window.
    """
    crop_w, crop_h = compute_9_16_crop_dimensions(source_w, source_h)
    default_center_x = source_w / 2.0

    if not detections:
        return clamp_crop_x(default_center_x, crop_w, source_w)

    valid_centers = [d["center_x"] for d in detections if d.get("center_x") is not None]
    if not valid_centers:
        return clamp_crop_x(default_center_x, crop_w, source_w)

    # Use median center for robust noise rejection
    valid_centers.sort()
    mid = len(valid_centers) // 2
    if len(valid_centers) % 2 == 0:
        median_x = (valid_centers[mid - 1] + valid_centers[mid]) / 2.0
    else:
        median_x = valid_centers[mid]

    return clamp_crop_x(median_x, crop_w, source_w)

class OneEuroFilter:
    """Adaptive 1-Euro filter for smooth real-time camera tracking with velocity clamping."""

    def __init__(self, t0: float, x0: float, dx0: float = 0.0, min_cutoff: float = 1.0, beta: float = 0.007, d_cutoff: float = 1.0):
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self.x_prev = float(x0)
        self.dx_prev = float(dx0)
        self.t_prev = float(t0)

    def _smoothing_factor(self, te: float, cutoff: float) -> float:
        r = 2.0 * math.pi * cutoff * te
        return r / (r + 1.0)

    def filter(self, t: float, x: float) -> float:
        te = t - self.t_prev
        if te <= 0.0:
            return self.x_prev

        # Estimate velocity
        a_d = self._smoothing_factor(te, self.d_cutoff)
        dx = (x - self.x_prev) / te
        dx_hat = a_d * dx + (1.0 - a_d) * self.dx_prev

        # Compute cutoff based on velocity
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = self._smoothing_factor(te, cutoff)
        x_hat = a * x + (1.0 - a) * self.x_prev

        # Update state
        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t

        return x_hat
