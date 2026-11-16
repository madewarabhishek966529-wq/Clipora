"""Social media publishing coordinator executing under clip_lock."""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from clipora.clips.clip_locks import clip_lock
from clipora.clips.clip_resolve import resolve_clip_paths
from clipora.core.errors import PublishError, JobNotFoundError
from clipora.jobs.job_artifacts import get_job_dir, read_job_metadata
from clipora.storage.config_store import get_config_store
from clipora.publishing.intent_journal import get_intent_journal, PublishStatus
from clipora.integrations.social_publisher import ZernioClient, SmartScheduler
from clipora.editing.compose import compose_clip

async def publish_clip_to_social(
    job_id: str,
    clip_index: int,
    platforms: List[str],
    schedule_mode: str = "now", # "now" | "auto" | "manual"
    manual_scheduled_for: Optional[str] = None,
    caption: Optional[str] = None,
) -> Dict[str, Any]:
    """Coordinate end-to-end clip rendering, presigned upload, and social publishing."""
    job_dir = get_job_dir(job_id)
    if not job_dir.is_dir():
        raise JobNotFoundError(job_id)

    cfg = get_config_store().get_config()
    if not cfg.zernio_api_key:
        raise PublishError("Zernio API key must be configured in Settings before publishing.")

    async with clip_lock(job_dir, clip_index):
        meta = read_job_metadata(job_id)
        if not meta or clip_index >= len(meta.clips):
            raise JobNotFoundError(f"Clip {clip_index} not found in job {job_id}")

        clip = meta.clips[clip_index]
        paths = resolve_clip_paths(job_dir, clip_index)
        video_to_upload = paths.final_composed

        # If final composed doesn't exist yet, render it
        if not video_to_upload.is_file():
            source = paths.get_preferred_render_source()
            compose_clip(
                input_video=source,
                output_video=video_to_upload,
                grade_preset=clip.grade_preset or "warm_cinematic",
            )

        # Determine scheduled timestamp
        scheduled_for_iso: Optional[str] = None
        if schedule_mode == "auto":
            slot = SmartScheduler.calculate_prime_time_slot(
                existing_slots=[],
                min_gap_seconds=cfg.zernio_min_gap_seconds,
            )
            scheduled_for_iso = slot.isoformat()
        elif schedule_mode == "manual" and manual_scheduled_for:
            scheduled_for_iso = manual_scheduled_for

        intent_id = f"intent_{uuid.uuid4().hex[:10]}"
        idempotency_key = f"clipora_{job_id}_{clip_index}_{intent_id}"

        journal = get_intent_journal()
        journal.record_intent(
            intent_id=intent_id,
            idempotency_key=idempotency_key,
            job_id=job_id,
            clip_index=clip_index,
            platforms=platforms,
            scheduled_for=scheduled_for_iso,
        )

        client = ZernioClient(api_key=cfg.zernio_api_key, base_url=cfg.zernio_base_url)

        try:
            journal.update_intent(intent_id, status=PublishStatus.UPLOADING)
            presigned_data = client.get_presigned_upload_url(filename=video_to_upload.name)
            upload_url = presigned_data["upload_url"]
            media_id = presigned_data.get("media_id", intent_id)

            client.upload_video_bytes(upload_url, video_to_upload)

            post_caption = caption or clip.video_description_for_tiktok or clip.viral_hook_text
            post_title = clip.video_title_for_youtube_short or clip.viral_hook_text

            post_res = client.create_post(
                idempotency_key=idempotency_key,
                media_id=media_id,
                platforms=platforms,
                caption=post_caption,
                title=post_title,
                scheduled_for=scheduled_for_iso,
            )

            post_id = post_res.get("post_id") or post_res.get("id", "confirmed")
            journal.update_intent(intent_id, status=PublishStatus.CONFIRMED, post_id=str(post_id))

            return {
                "status": "success",
                "intent_id": intent_id,
                "post_id": post_id,
                "platforms": platforms,
                "scheduled_for": scheduled_for_iso,
            }

        except Exception as e:
            journal.update_intent(intent_id, status=PublishStatus.FAILED, error=str(e))
            raise e
