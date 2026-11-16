"""5-level robust JSON parser and repair engine for LLM outputs."""

import json
import logging
import re
from typing import Any, Dict, List, Optional
import json_repair
from clipora.core.clip_schema import ViralClip, ViralClipsResponse
from clipora.pipeline.transcription.diarization import NormalizedTranscript
from clipora.pipeline.analysis.texttiling_ops import fallback_topic_segmentation

logger = logging.getLogger("clipora.gemini_parser")

DELIMITER = "### JSON ###"

def _normalize_text_characters(raw: str) -> str:
    """Normalize curly quotes, em-dashes, and unicode whitespace."""
    replacements = {
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
    }
    for old, new in replacements.items():
        raw = raw.replace(old, new)
    return raw

def _deterministic_cleanup(raw: str) -> str:
    """Clean markdown code fences, trailing commas, and escaped backslashes."""
    text = _normalize_text_characters(raw)

    # Strip code block markers
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE)

    # Remove trailing commas before closing braces/brackets
    text = re.sub(r",\s*([\]}])", r"\1", text)

    return text.strip()

def parse_viral_clips_response(
    raw_llm_output: str,
    transcript: Optional[NormalizedTranscript] = None,
    targeted_llm_fixer = None,
) -> List[ViralClip]:
    """Parse Gemini output through the 5-level repair pipeline."""
    # LEVEL 1: Strict parse after delimiter
    target_text = raw_llm_output
    if DELIMITER in raw_llm_output:
        target_text = raw_llm_output.split(DELIMITER, 1)[1].strip()

    try:
        data = json.loads(target_text)
        return ViralClipsResponse.model_validate(data).clips
    except Exception as e1:
        logger.debug(f"Level 1 strict parse failed: {e1}")

    # LEVEL 2: Deterministic regex cleanup
    cleaned = _deterministic_cleanup(target_text)
    try:
        data = json.loads(cleaned)
        return ViralClipsResponse.model_validate(data).clips
    except Exception as e2:
        logger.debug(f"Level 2 deterministic cleanup failed: {e2}")

    # LEVEL 3: json_repair library
    try:
        repaired = json_repair.loads(cleaned)
        if isinstance(repaired, dict):
            return ViralClipsResponse.model_validate(repaired).clips
        elif isinstance(repaired, list):
            return ViralClipsResponse.model_validate({"clips": repaired}).clips
    except Exception as e3:
        logger.debug(f"Level 3 json_repair failed: {e3}")

    # LEVEL 4: Targeted LLM Reformat (if callable provided)
    if targeted_llm_fixer is not None:
        try:
            fixed_text = targeted_llm_fixer(target_text)
            repaired = json_repair.loads(fixed_text)
            if isinstance(repaired, dict):
                return ViralClipsResponse.model_validate(repaired).clips
            elif isinstance(repaired, list):
                return ViralClipsResponse.model_validate({"clips": repaired}).clips
        except Exception as e4:
            logger.warning(f"Level 4 targeted LLM reformat failed: {e4}")

    # LEVEL 5: TextTiling topic segmentation fallback
    logger.warning("All JSON parsing levels exhausted. Executing Level 5 TextTiling topic segmentation fallback.")
    if transcript is not None:
        return fallback_topic_segmentation(transcript)

    return []
