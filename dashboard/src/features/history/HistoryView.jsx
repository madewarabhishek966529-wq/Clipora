import React, { useState, useEffect } from 'react';
import { Card, Button, Input, Badge } from '../../components/primitives';
import { api } from '../../api/client';

export function HistoryView({ onSelectJob }) {
  const [jobs, setJobs] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchJobs = async () => {
    try {
      const data = await api.listJobs();
      setJobs(data.jobs || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleDelete = async (jobId) => {
    if (!window.confirm(`Permanently purge job #${jobId} and its output files from disk?`)) return;
    try {
      await api.deleteJob(jobId);
      await fetchJobs();
    } catch (err) {
      alert(err.message);
    }
  };

  const filtered = jobs.filter((j) => {
    const term = searchTerm.toLowerCase();
    return (
      j.job_id.toLowerCase().includes(term) ||
      (j.video_title && j.video_title.toLowerCase().includes(term)) ||
      (j.source_url && j.source_url.toLowerCase().includes(term))
    );
  });

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-in fade-in duration-300">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Job History & Restore</h1>
          <p className="text-slate-400 mt-1 text-sm">
            Inspect past processing runs, replay rendered clips, or purge artifacts from storage.
          </p>
        </div>

        <div className="w-full md:w-64">
          <Input
            placeholder="Search by ID or title..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {loading ? (
        <Card className="text-center py-16 text-slate-400">Loading past job records...</Card>
      ) : filtered.length === 0 ? (
        <Card className="text-center py-16 text-slate-500">
          No historical processing runs found matching your search.
        </Card>
      ) : (
        <div className="space-y-3">
          {filtered.map((j) => (
            <Card key={j.job_id} className="flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-slate-700 transition-colors">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="font-mono font-bold text-white text-sm">#{j.job_id}</span>
                  <Badge variant={j.status === 'completed' ? 'green' : j.status === 'failed' ? 'red' : 'indigo'}>
                    {j.status.toUpperCase()}
                  </Badge>
                  <span className="text-xs text-slate-500 font-mono">
                    {j.created_at ? new Date(j.created_at).toLocaleDateString() : ''}
                  </span>
                </div>
                <div className="font-semibold text-sm text-slate-200 truncate max-w-xl">
                  {j.video_title || j.source_url || 'Video Processing Job'}
                </div>
                <div className="text-xs text-slate-400">
                  Clips Rendered: <strong className="text-indigo-400">{j.clip_count}</strong> | Duration: {j.video_duration ? `${Math.round(j.video_duration)}s` : 'Unknown'}
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => onSelectJob && onSelectJob(j.job_id)}
                >
                  View Clips 🎬
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-rose-400 text-xs"
                  onClick={() => handleDelete(j.job_id)}
                >
                  Delete 🗑️
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
