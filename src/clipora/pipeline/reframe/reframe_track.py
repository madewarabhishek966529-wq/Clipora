"""Pure trajectory tracking, dead-zone hysteresis, and lost speaker drift."""

from typing import Optional
from clipora.pipeline.reframe.reframe_ops import compute_9_16_crop_dimensions, clamp_crop_x, OneEuroFilter

class Cameraman:
    """Manages virtual camera panning, dead-zones, and centering when tracking subjects."""

    def __init__(
        self,
        source_w: int,
        source_h: int,
        fps: float = 30.0,
        lost_hold_frames: int = 90,
        drift_lerp_rate: float = 0.05,
        dead_zone_percent: float = 0.03,
    ):
        self.source_w = source_w
        self.source_h = source_h
        self.fps = fps
        self.lost_hold_frames = lost_hold_frames
        self.drift_lerp_rate = drift_lerp_rate
        self.dead_zone_px = dead_zone_percent * source_w

        self.crop_w, self.crop_h = compute_9_16_crop_dimensions(source_w, source_h)
        self.center_x = source_w / 2.0
        self.current_crop_center_x = self.center_x

        self.lost_frame_count = 0
        self.filter = OneEuroFilter(t0=0.0, x0=self.center_x)

    def update(self, frame_index: int, detected_target_x: Optional[float]) -> int:
        """Update virtual camera target for current frame and return top_left_x coordinate."""
        timestamp = frame_index / self.fps

        if detected_target_x is not None:
            self.lost_frame_count = 0
            # Dead-zone hysteresis
            if abs(detected_target_x - self.current_crop_center_x) > self.dead_zone_px:
                smoothed_x = self.filter.filter(timestamp, detected_target_x)
                self.current_crop_center_x = smoothed_x
        else:
            self.lost_frame_count += 1
            if self.lost_frame_count > self.lost_hold_frames:
                # Drift smoothly back to center
                self.current_crop_center_x += (
                    (self.center_x - self.current_crop_center_x) * self.drift_lerp_rate
                )
                self.filter.filter(timestamp, self.current_crop_center_x)

        return clamp_crop_x(self.current_crop_center_x, self.crop_w, self.source_w)
