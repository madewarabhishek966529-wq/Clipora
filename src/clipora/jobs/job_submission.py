"""Async job queue, submission dispatch, and worker loop with semaphore limits."""

import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from clipora.core.clip_schema import JobMetadata, JobStatus
from clipora.core.errors import ValidationError, SSRFError, JobNotFoundError
from clipora.core.netutil import validate_url_ssrf_safe
from clipora.storage.config_store import get_config_store
from clipora.jobs.job_artifacts import write_job_metadata, read_job_metadata, update_job_metadata, get_job_dir
from clipora.jobs.job_journal import get_job_journal
from clipora.jobs.job_runner import run_pipeline_subprocess
from clipora.jobs.job_control import cancel_job as control_cancel_job

class JobQueueManager:
    """Manages the in-memory queue, concurrency semaphore, and background workers."""

    def __init__(self, max_concurrent: int = 2):
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.worker_task: Optional[asyncio.Task] = None
        self._running = False

    def start(self, max_concurrent: Optional[int] = None) -> None:
        if max_concurrent:
            self.semaphore = asyncio.Semaphore(max_concurrent)
        if not self._running:
            self._running = True
            self.worker_task = asyncio.create_task(self._worker_loop())

    async def stop(self) -> None:
        self._running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass

    async def _worker_loop(self) -> None:
        while self._running:
            try:
                job_id = await self.queue.get()
            except asyncio.CancelledError:
                break

            # Check if job was cancelled before execution started
            journal = get_job_journal()
            job_entry = journal.get_job(job_id)
            if not job_entry or job_entry.get("status") == JobStatus.CANCELLED.value:
                self.queue.task_done()
                continue

            asyncio.create_task(self._execute_with_semaphore(job_id))
            self.queue.task_done()

    async def _execute_with_semaphore(self, job_id: str) -> None:
        async with self.semaphore:
            try:
                await run_pipeline_subprocess(job_id)
            except Exception as e:
                # Subprocess runner already handles logging & status update
                pass

    async def submit_job(
        self,
        source_url: Optional[str] = None,
        input_file: Optional[str] = None,
        reframe_mode: str = "auto",
        custom_instructions: Optional[str] = None,
        transcription_provider: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> JobMetadata:
        """Validate input, record in journal & metadata, and enqueue for processing."""
        if not source_url and not input_file:
            raise ValidationError("Either 'source_url' or 'input_file' must be provided.")

        if source_url:
            # Enforce pre-flight SSRF check
            validate_url_ssrf_safe(source_url)

        if not job_id:
            job_id = uuid.uuid4().hex[:12]

        config = get_config_store().get_config()
        t_provider = transcription_provider or config.transcription_provider

        now_str = datetime.now(timezone.utc).isoformat()
        metadata = JobMetadata(
            job_id=job_id,
            status=JobStatus.QUEUED,
            source_url=source_url,
            input_file=input_file,
            created_at=now_str,
            updated_at=now_str,
            reframe_mode=reframe_mode,
            custom_instructions=custom_instructions,
            transcription_provider=t_provider,
        )

        job_dir = get_job_dir(job_id)
        job_dir.mkdir(parents=True, exist_ok=True)

        try:
            write_job_metadata(metadata)
            payload = {
                "source_url": source_url,
                "input_file": input_file,
                "reframe_mode": reframe_mode,
                "custom_instructions": custom_instructions,
                "transcription_provider": t_provider,
            }
            get_job_journal().record_job(job_id, payload)
            await self.queue.put(job_id)
        except Exception as e:
            # Rollback
            get_job_journal().remove_job(job_id)
            raise e

        return metadata

    def cancel(self, job_id: str) -> bool:
        return control_cancel_job(job_id)

_global_queue_manager = JobQueueManager()

def get_job_queue() -> JobQueueManager:
    return _global_queue_manager
