"""Subprocess pipeline entrypoint orchestrating end-to-end clip generation."""

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from clipora.core.clip_schema import JobStatus
from clipora.jobs.job_artifacts import (
    get_job_dir,
    read_job_metadata,
    write_job_metadata,
    update_job_metadata,
)
from clipora.jobs.runtime_state import RuntimeCheckpoint
from clipora.pipeline.preflight import run_preflight_check
from clipora.pipeline.download import download_video
from clipora.pipeline.postprocess import extract_flac_audio, cut_clip_slice, extract_thumbnail
from clipora.pipeline.transcription import transcribe_audio
from clipora.pipeline.analysis.gemini_service import analyze_video_virality
from clipora.pipeline.cut_ops import snap_clip_to_words, snap_to_sentences
from clipora.pipeline.reframe.reframe import reframe_video_to_vertical
from clipora.media.media_probe import probe_media

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("clipora.orchestrator")

def run_job_pipeline(job_id: str) -> None:
    job_dir = get_job_dir(job_id)
    checkpoint = RuntimeCheckpoint(job_dir)

    metadata = read_job_metadata(job_id)
    if not metadata:
        logger.error(f"Cannot find metadata for job {job_id}")
        sys.exit(1)

    logger.info(f"Starting pipeline orchestrator for job {job_id}")
    source_video_path = job_dir / "source.mp4"

    # =========================================================================
    # STAGE 1: INGESTION / DOWNLOAD
    # =========================================================================
    if not checkpoint.is_phase_completed("download"):
        update_job_metadata(job_id, {"current_phase": "download", "progress_percent": 5.0})
        if metadata.source_url:
            logger.info(f"Downloading source video from: {metadata.source_url}")
            def on_dl_progress(pct: float):
                update_job_metadata(job_id, {"progress_percent": round(pct, 1)})
            downloaded_path, info = download_video(
                metadata.source_url,
                job_dir,
                "source.mp4",
                progress_callback=on_dl_progress,
            )
            source_video_path = downloaded_path
            metadata.video_title = info.get("title", "Video Source")
            metadata.video_duration = float(info.get("duration", 0.0))
        elif metadata.input_file:
            input_p = Path(metadata.input_file).resolve()
            if not input_p.is_file():
                raise FileNotFoundError(f"Uploaded input file not found: {metadata.input_file}")
            source_video_path = input_p

        # Probe video
        try:
            probe = probe_media(source_video_path)
            metadata.video_duration = probe.duration
        except Exception as e:
            logger.warning(f"Could not probe video duration: {e}")

        # Run preflight disk gate
        duration_sec = metadata.video_duration or 60.0
        run_preflight_check(job_dir, duration_sec)

        checkpoint.update_phase("download", {"source_path": str(source_video_path)})
        update_job_metadata(
            job_id,
            {
                "current_phase": "download",
                "progress_percent": 25.0,
                "video_title": metadata.video_title,
                "video_duration": metadata.video_duration,
            },
        )
    else:
        p_data = checkpoint.get_phase_data("download") or {}
        if "source_path" in p_data:
            source_video_path = Path(p_data["source_path"])

    # =========================================================================
    # STAGE 2: AUDIO EXTRACTION & TRANSCRIPTION
    # =========================================================================
    audio_path = job_dir / "source_audio.flac"
    if not checkpoint.is_phase_completed("transcribe"):
        update_job_metadata(job_id, {"current_phase": "transcribe", "progress_percent": 30.0})
        logger.info("Extracting 16kHz mono FLAC audio...")
        extract_flac_audio(source_video_path, audio_path)

        logger.info("Transcribing audio with diarization...")
        source_id = metadata.source_url or str(source_video_path)
        transcript = transcribe_audio(
            audio_path,
            source_identifier=source_id,
            preferred_provider=metadata.transcription_provider,
        )
        checkpoint.update_phase("transcribe", {"transcript": transcript.to_dict()})
        update_job_metadata(job_id, {"current_phase": "transcribe", "progress_percent": 45.0})
    else:
        from clipora.pipeline.transcription.diarization import NormalizedTranscript
        t_data = checkpoint.get_phase_data("transcribe") or {}
        transcript = NormalizedTranscript.from_dict(t_data.get("transcript", {"text": "", "words": []}))

    # =========================================================================
    # STAGE 3: AI VIRALITY DETECTION & MOMENT SELECTION
    # =========================================================================
    if not checkpoint.is_phase_completed("analysis"):
        update_job_metadata(job_id, {"current_phase": "analysis", "progress_percent": 50.0})
        logger.info("Running AI virality scoring and copy generation...")
        duration_sec = metadata.video_duration or 60.0
        raw_clips = analyze_video_virality(
            transcript=transcript,
            video_duration=duration_sec,
            custom_instructions=metadata.custom_instructions,
        )

        # Micro-precision boundary snapping
        snapped_clips = []
        for c in raw_clips:
            # Word snapping (50ms pre-pad, 80ms post-pad)
            ws, we = snap_clip_to_words(c.start, c.end, transcript.words, video_duration=duration_sec)
            # Sentence boundary snapping
            ss, se = snap_to_sentences(ws, we, transcript.words, video_duration=duration_sec)
            c.start = ss
            c.end = se
            c.duration = round(se - ss, 3)
            snapped_clips.append(c)

        checkpoint.update_phase("analysis", {"clips": [c.model_dump() for c in snapped_clips]})
        update_job_metadata(job_id, {"clips": snapped_clips, "current_phase": "analysis", "progress_percent": 70.0})
    else:
        from clipora.core.clip_schema import ViralClip
        a_data = checkpoint.get_phase_data("analysis") or {}
        snapped_clips = [ViralClip.model_validate(c) for c in a_data.get("clips", [])]

    # =========================================================================
    # STAGE 4: CUTTING SLICES, THUMBNAILS & REFRAMING
    # =========================================================================
    if not checkpoint.is_phase_completed("reframe"):
        update_job_metadata(job_id, {"current_phase": "reframe", "progress_percent": 75.0})
        logger.info(f"Rendering {len(snapped_clips)} video slices and vertical crops...")

        for idx, clip in enumerate(snapped_clips):
            source_slice = job_dir / f"source_{idx}.mp4"
            vertical_slice = job_dir / f"vertical_{idx}.mp4"
            thumb_path = job_dir / f"clip_{idx}_thumb.jpg"

            # 1. Cut pristine source slice
            cut_clip_slice(source_video_path, source_slice, clip.start, clip.end)

            # 2. Extract representative thumbnail
            extract_thumbnail(source_slice, thumb_path, timestamp=1.0)

            # 3. Render vertical 9:16 reframe
            reframe_video_to_vertical(
                input_video=source_slice,
                output_video=vertical_slice,
                mode=metadata.reframe_mode,
            )

            clip.original_index = idx
            clip.clip_filename = f"vertical_{idx}.mp4"
            clip.thumbnail_filename = f"clip_{idx}_thumb.jpg"

        checkpoint.update_phase("reframe")
        update_job_metadata(
            job_id,
            {
                "clips": snapped_clips,
                "current_phase": "completed",
                "progress_percent": 100.0,
                "status": JobStatus.COMPLETED,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    logger.info(f"Pipeline completed successfully for job {job_id}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Clipora Subprocess Pipeline Orchestrator")
    parser.add_argument("--job-id", required=True, help="Job ID to execute")
    args = parser.parse_args()

    try:
        run_job_pipeline(args.job_id)
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error in pipeline orchestrator for job {args.job_id}: {e}")
        update_job_metadata(args.job_id, {"status": JobStatus.FAILED, "error_message": str(e)})
        sys.exit(1)

if __name__ == "__main__":
    main()
