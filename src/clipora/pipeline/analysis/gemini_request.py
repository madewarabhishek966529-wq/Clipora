"""TOON (Token-Oriented Object Notation) serializer and Gemini prompt builder."""

import csv
import io
from typing import List, Optional
from clipora.pipeline.transcription.diarization import NormalizedTranscript, TranscriptWord

GEMINI_PROMPT_TEMPLATE = """You are a senior short-form video editor specialized in TikTok, IG Reels and YouTube Shorts virality. Read the ENTIRE transcript + word-level timestamps and select the 3–15 MOST VIRAL 15–60s moments.

## IS THIS MOMENT EVEN WORTH CUTTING? (gate — apply BEFORE scoring)
A clip must hit at least ONE of these HARD. A moment that is merely pleasant, well-spoken or on-topic is NOT a clip, however clean the audio is.
1. UNEXPECTED TURN — plot twist, pattern interrupt, someone contradicting what they just said, a reveal nobody saw coming. The surprise is the product.
2. STRONG EMOTION OR POLARIZATION — instant laugh, rage, awe, secondhand embarrassment; or a take that splits the audience in two. The test: would a viewer send this to a friend or drop it in a group chat? A moment half the audience wants to argue with outperforms one everybody agrees with.
3. RELATABILITY — "this is literally me". Specific and everyday, not abstract.
4. NEW OR USEFUL INFO — a fact, number, trick or broken misconception a viewer would SAVE for later.
Emit FEWER, harder clips rather than padding the list with competent-but-flat moments: a weak clip costs the account more than a missing one.
The reaction beat is PART of the clip — the laugh, the silence after the reveal, the "what?!". End after it lands, never before.

## VIRAL_SCORE RUBRIC (1–100)
Score each axis from 1 to 20 and sum (cap at 100):
- HOOK_STRENGTH: do the first 1–3s grab attention? (pattern-break, bold claim, surprise). Roughly half of viewers swipe before 3s — a slow ramp is fatal.
- EMOTIONAL_PAYOFF: is there an actual turn or reaction — shock, laugh, rage, awe — and does it LAND on screen? Score the surprise and reaction, not the subject matter.
- QUOTABILITY: is there a line viewers would screenshot, repeat, or argue with?
- SELF_CONTAINED: makes sense without context from the rest of the video?
- DENSITY: no dead air, no rambling, every second earns its place. Silence and tangents are the top retention killer.

## HARD CONSTRAINTS (violating = clip REJECTED)
- 15s <= duration <= 60s
- start on a complete sentence boundary; end on a natural beat
- no cold-open ambiguity ("...and then she said" with no setup)
- 0 <= start < end <= VIDEO_DURATION_SECONDS
- ANCHOR TO REAL TIMESTAMPS: `start` MUST equal the `s` of the FIRST word in the WORDS section, and `end` MUST equal the `e` of the LAST word. Do not invent times between words; do not round to integers.
- start and end are FLOAT SECONDS with up to 3 decimals (e.g. 12.340, 1517.724). NEVER emit colon or dotted timecodes like "25:17" or "25.17.724".
- viral_reason MUST be >= 20 characters and cite the specific hook, payoff or quote.
- viral_hook_text is REQUIRED (3-8 words), written AS A SCROLL-STOPPING OVERLAY — NOT a transcript quote. Standalone copywriting designed to stop scrolling on TikTok/Reels.

## TITLE & CAPTION COPY
A title is NOT a summary of the clip. It is bait: its only job is to make someone stop, watch, and COMMENT.
1. PLAY UP THE STAKES. Frame what happens at its most dramatic, absurd, or consequential reading.
2. SPECULATE OUT LOUD. Allowed ONLY as open speculation using conditionals or questions ("Did he just ruin his stream?", "With this move he might retire"). Never invent false statements of fact.
3. BAIT COMMENTS IMPLICITLY. Give viewers something to reply to: an opinion that splits the room, a debatable valuation, a genuine question ("Tell me I'm wrong"). NEVER use mechanical engagement bait ("comment X for link", "like if you agree").
4. LEAVE THE LOOP OPEN. Name the object or reaction, never the outcome — the payoff must be watched.
5. CONCRETE > VAGUE. Use real numbers and specific objects.
6. STACK EXACTLY TWO triggers per title.

## VIDEO METADATA
VIDEO_DURATION_SECONDS: {video_duration}
{creator_block}

TRANSCRIPT_TEXT:
{transcript_text}

WORDS (TOON tabular format):
{words_toon}

{user_instructions_block}

## OUTPUT CONTRACT
1. Think step-by-step internally about candidate moments.
2. On its own line, emit the LITERAL delimiter:
### JSON ###
3. Emit ONLY the JSON object conforming to the schema:
{{
  "clips": [
    {{
      "start": 12.340,
      "end": 45.670,
      "viral_score": 92,
      "viral_reason": "Opens with immediate disbelief, builds tension with two failed attempts, and lands a high-energy punchline.",
      "viral_hook_text": "The one mistake everyone makes",
      "video_title_for_youtube_short": "Did he actually just lose 10,000 dollars live?",
      "video_description_for_tiktok": "He really thought he had it. Would you have taken the risk?",
      "video_description_for_instagram": "Watch until the end. Tell me you wouldn't have done the exact same thing."
    }}
  ]
}}
"""

def serialize_to_toon(words: List[TranscriptWord]) -> str:
    """Serialize word list into Token-Oriented Object Notation (TOON) saving up to 65% tokens."""
    lines = [f"words[{len(words)}]{{w,s,e}}:"]
    for w in words:
        word_text = w.word.strip()
        # Escape quotes or commas if present
        if "," in word_text or '"' in word_text:
            escaped = word_text.replace('"', '""')
            word_str = f'"{escaped}"'
        else:
            word_str = word_text
        lines.append(f"  {word_str},{w.start:.3f},{w.end:.3f}")
    return "\n".join(lines)

def build_gemini_prompt(
    transcript: NormalizedTranscript,
    video_duration: float,
    creator_info: Optional[str] = None,
    custom_instructions: Optional[str] = None,
) -> str:
    """Construct complete virality prompt with TOON word tabular data."""
    words_toon = serialize_to_toon(transcript.words)

    creator_block = f"CREATOR_CONTEXT: {creator_info}" if creator_info else ""
    user_instructions_block = (
        f"## USER CUSTOM EDITING INSTRUCTIONS:\n{custom_instructions}"
        if custom_instructions
        else ""
    )

    return GEMINI_PROMPT_TEMPLATE.format(
        video_duration=f"{video_duration:.3f}",
        creator_block=creator_block,
        transcript_text=transcript.text,
        words_toon=words_toon,
        user_instructions_block=user_instructions_block,
    )
