"""Quality metrics and validation checks for candidate clips."""

from clipora.core.clip_schema import ViralClip

def validate_clip_constraints(clip: ViralClip, min_dur: float = 14.5, max_dur: float = 60.5) -> dict:
    """Verify that a candidate clip satisfies duration and scoring invariants."""
    dur = clip.end - clip.start
    issues = []

    if dur < min_dur:
        issues.append(f"Duration too short: {dur:.2f}s < {min_dur}s")
    if dur > max_dur:
        issues.append(f"Duration too long: {dur:.2f}s > {max_dur}s")
    if clip.viral_score < 1 or clip.viral_score > 100:
        issues.append(f"Viral score out of bounds: {clip.viral_score}")
    if len(clip.viral_reason) < 20:
        issues.append("Viral reason explanation too brief (< 20 chars)")
    if len(clip.viral_hook_text) < 3:
        issues.append("Viral hook text missing or too short")

    return {
        "valid": len(issues) == 0,
        "duration": round(dur, 3),
        "issues": issues,
    }
