"""Heavy pipeline execution wrapper."""

from clipora.pipeline.orchestrator import run_job_pipeline

def execute_pipeline(job_id: str) -> None:
    """Execute heavy video processing pipeline for given job ID."""
    run_job_pipeline(job_id)
