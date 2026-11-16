"""End-to-end QA validation suite for generated clips."""

from pathlib import Path
from typing import List, Dict, Any
from clipora.core.clip_schema import ViralClip
from clipora.pipeline.quality.clip_qa import validate_clip_constraints
from clipora.pipeline.quality.media_qa import check_for_black_or_frozen_frames

def run_clip_qa_suite(clip: ViralClip, rendered_video_path: Path | str | None = None) -> Dict[str, Any]:
    """Run full QA check on candidate clip metadata and physical video file."""
    constraint_report = validate_clip_constraints(clip)
    media_report = {"passed": True}

    if rendered_video_path and Path(rendered_video_path).is_file():
        media_report = check_for_black_or_frozen_frames(rendered_video_path)

    overall_passed = constraint_report["valid"] and media_report.get("passed", True)
    return {
        "overall_passed": overall_passed,
        "constraints": constraint_report,
        "media": media_report,
    }
