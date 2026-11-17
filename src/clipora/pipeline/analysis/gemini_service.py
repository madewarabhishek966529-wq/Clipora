"""Google GenAI service for autonomous virality scoring and clip selection."""

import logging
import os
from typing import List, Optional
from clipora.core.clip_schema import ViralClip
from clipora.core.errors import ViralityAnalysisError
from clipora.storage.config_store import get_config_store
from clipora.pipeline.transcription.diarization import NormalizedTranscript
from clipora.pipeline.analysis.gemini_request import build_gemini_prompt
from clipora.pipeline.analysis.gemini_parser import parse_viral_clips_response

logger = logging.getLogger("clipora.gemini")

CANDIDATE_MODELS = [
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.8-flash",
]

def call_gemini_api(prompt: str, api_key: str, model_name: Optional[str] = None) -> str:
    """Invoke Gemini API via google-genai or google-generativeai SDK with candidate fallback."""
    models_to_try = [model_name] if model_name else []
    for m in CANDIDATE_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

    last_exc = None
    for target_model in models_to_try:
        # 1. Attempt using modern google.genai Client
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=target_model,
                contents=prompt,
            )
            if response.text:
                return response.text
        except Exception as e1:
            last_exc = e1
            logger.debug(f"google.genai with {target_model} failed ({e1})")

        # 2. Fallback to google.generativeai
        try:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=api_key)
            model = legacy_genai.GenerativeModel(target_model)
            response = model.generate_content(prompt)
            if response.text:
                return response.text
        except Exception as e2:
            last_exc = e2
            logger.debug(f"google.generativeai with {target_model} failed ({e2})")

    raise ViralityAnalysisError(f"All Gemini models failed. Last error: {last_exc}")

def analyze_video_virality(
    transcript: NormalizedTranscript,
    video_duration: float,
    creator_info: Optional[str] = None,
    custom_instructions: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[ViralClip]:
    """Execute complete virality moment detection and copy generation."""
    cfg = get_config_store().get_config()
    key = api_key or cfg.gemini_api_key or os.getenv("GEMINI_API_KEY", "")

    if not key:
        logger.warning("Gemini API key is not configured. Running fallback topic segmentation.")
        from clipora.pipeline.analysis.texttiling_ops import fallback_topic_segmentation
        return fallback_topic_segmentation(transcript)

    prompt = build_gemini_prompt(
        transcript=transcript,
        video_duration=video_duration,
        creator_info=creator_info,
        custom_instructions=custom_instructions,
    )

    try:
        raw_output = call_gemini_api(prompt, key)
    except Exception as e:
        logger.error(f"Gemini API calls failed: {e}. Falling back to TextTiling algorithmic segmentation.")
        from clipora.pipeline.analysis.texttiling_ops import fallback_topic_segmentation
        return fallback_topic_segmentation(transcript)

    def level4_llm_fixer(bad_text: str) -> str:
        fix_prompt = f"Convert this text into pure valid JSON matching {{'clips': [...]}} schema:\n\n{bad_text}"
        return call_gemini_api(fix_prompt, key)

    clips = parse_viral_clips_response(
        raw_output,
        transcript=transcript,
        targeted_llm_fixer=level4_llm_fixer,
    )

    # Assign original indices
    for idx, c in enumerate(clips):
        c.original_index = idx
        c.duration = round(c.end - c.start, 3)

    return clips
