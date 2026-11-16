"""Unit tests for the durable job journal and startup crash recovery."""

import pytest
from pathlib import Path
from clipora.core.clip_schema import JobStatus
from clipora.jobs.job_journal import JobJournal

def test_job_journal_lifecycle(tmp_path: Path):
    journal_path = tmp_path / "jobs_journal.json"
    journal = JobJournal(journal_path)

    # 1. Record job
    journal.record_job("job-101", {"source_url": "https://youtube.com/watch?v=abc"})
    entry = journal.get_job("job-101")
    assert entry is not None
    assert entry["status"] == JobStatus.QUEUED.value
    assert entry["payload"]["source_url"] == "https://youtube.com/watch?v=abc"

    # 2. Update job
    journal.update_job("job-101", status=JobStatus.DOWNLOADING.value, pid=12345, phase="download")
    updated = journal.get_job("job-101")
    assert updated["status"] == JobStatus.DOWNLOADING.value
    assert updated["pid"] == 12345
    assert updated["phase"] == "download"

    # 3. List active jobs
    active = journal.list_active_jobs()
    assert len(active) == 1
    assert active[0]["job_id"] == "job-101"

    # 4. Remove job
    journal.remove_job("job-101")
    assert journal.get_job("job-101") is None
    assert len(journal.list_active_jobs()) == 0

def test_job_journal_startup_crash_recovery(tmp_path: Path):
    journal_path = tmp_path / "jobs_journal.json"
    journal = JobJournal(journal_path)

    # Simulate 3 jobs before crash: 1 queued, 1 active, 1 completed
    journal.record_job("job-queued", {"url": "test1"})
    journal.record_job("job-active", {"url": "test2"})
    journal.update_job("job-active", status=JobStatus.REFRAMING.value)
    journal.record_job("job-done", {"url": "test3"})
    journal.update_job("job-done", status=JobStatus.COMPLETED.value)

    # Run startup recovery
    to_requeue = journal.recover_on_startup()
    assert len(to_requeue) == 1
    assert to_requeue[0]["job_id"] == "job-queued"

    # The in-flight job should now be marked failed
    active_entry = journal.get_job("job-active")
    assert active_entry["status"] == JobStatus.FAILED.value
    assert "crash" in active_entry["error"].lower() or "interrupted" in active_entry["error"].lower()
