import React, { useState, useEffect } from 'react';
import { Card, Button, Badge } from '../../components/primitives';
import { api } from '../../api/client';

export function ProcessingView({ activeJobId, onSelectJob }) {
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchJob = async () => {
    if (!activeJobId) return;
    try {
      const data = await api.getJob(activeJobId);
      setJob(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchJob();
    const interval = setInterval(fetchJob, 2000);
    return () => clearInterval(interval);
  }, [activeJobId]);

  const handlePause = async () => {
    setActionLoading(true);
    try {
      await api.pauseJob(activeJobId);
      await fetchJob();
    } finally {
      setActionLoading(false);
    }
  };

  const handleResume = async () => {
    setActionLoading(true);
    try {
      await api.resumeJob(activeJobId);
      await fetchJob();
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!window.confirm('Are you sure you want to cancel this processing run?')) return;
    setActionLoading(true);
    try {
      await api.cancelJob(activeJobId);
      await fetchJob();
    } finally {
      setActionLoading(false);
    }
  };

  if (!activeJobId) {
    return (
      <div className="max-w-4xl mx-auto text-center py-20 text-slate-500">
        <p className="text-lg">No active job selected.</p>
        <p className="text-sm mt-1">Submit a video from the Create tab to monitor real-time telemetry.</p>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="max-w-4xl mx-auto text-center py-20 text-slate-400">
        <div className="animate-spin inline-block w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full mb-3"></div>
        <p>Connecting to job orchestrator telemetry...</p>
      </div>
    );
  }

  const isPaused = job.status === 'paused';
  const isCompleted = job.status === 'completed';
  const isFailed = job.status === 'failed';
  const isCancelled = job.status === 'cancelled';

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-300">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold text-white tracking-tight">Job #{job.job_id}</h1>
            <Badge
              variant={
                isCompleted
                  ? 'green'
                  : isFailed
                  ? 'red'
                  : isPaused
                  ? 'yellow'
                  : 'indigo'
              }
            >
              {job.status.toUpperCase()}
            </Badge>
          </div>
          <p className="text-slate-400 text-sm mt-1 truncate max-w-lg">
            {job.video_title || job.source_url || 'Processing video source...'}
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {!isCompleted && !isFailed && !isCancelled && (
            <>
              {isPaused ? (
                <Button variant="secondary" size="sm" onClick={handleResume} disabled={actionLoading}>
                  Resume ▶
                </Button>
              ) : (
                <Button variant="secondary" size="sm" onClick={handlePause} disabled={actionLoading}>
                  Pause ⏸
                </Button>
              )}
              <Button variant="danger" size="sm" onClick={handleCancel} disabled={actionLoading}>
                Cancel ✖
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Progress Bar Card */}
      <Card className="space-y-4">
        <div className="flex items-center justify-between text-sm">
          <span className="font-semibold text-slate-300 capitalize">Phase: {job.current_phase || 'In Progress'}</span>
          <span className="font-bold text-indigo-400">{Math.round(job.progress_percent || 0)}%</span>
        </div>

        <div className="w-full bg-slate-950 h-3 rounded-full overflow-hidden border border-slate-800 p-0.5">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-full transition-all duration-500"
            style={{ width: `${Math.min(100, Math.max(5, job.progress_percent || 0))}%` }}
          />
        </div>

        {job.error_message && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-300 text-xs">
            <strong>Execution Error:</strong> {job.error_message}
          </div>
        )}
      </Card>

      {/* Live Log Terminal */}
      <Card className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Subprocess Pipeline Log</h3>
          <span className="text-xs font-mono text-slate-500">python -m clipora.pipeline.orchestrator</span>
        </div>
        <pre className="bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono text-xs text-slate-300 h-80 overflow-y-auto whitespace-pre-wrap leading-relaxed select-text">
          {job.logs || 'Waiting for pipeline process output...'}
        </pre>
      </Card>
    </div>
  );
}
