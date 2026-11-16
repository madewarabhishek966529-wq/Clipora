import React, { useState, useEffect } from 'react';
import { Card, Button, Badge } from '../../components/primitives';
import { api } from '../../api/client';
import { ClipEditorModal } from '../clip-editor/ClipEditorModal';
import { PublishModal } from '../publishing/PublishModal';

export function ResultsView({ activeJobId, onSelectJob }) {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [editingClip, setEditingClip] = useState(null);
  const [publishingClip, setPublishingClip] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchJobs = async () => {
    try {
      const data = await api.listJobs();
      setJobs(data.jobs || []);
      if (activeJobId) {
        const found = data.jobs.find((j) => j.job_id === activeJobId);
        if (found) setSelectedJob(found);
      } else if (data.jobs && data.jobs.length > 0 && !selectedJob) {
        setSelectedJob(data.jobs[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [activeJobId]);

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto text-center py-24 text-slate-400">
        <div className="animate-spin inline-block w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full mb-3"></div>
        <p>Loading rendered viral shorts...</p>
      </div>
    );
  }

  const clips = selectedJob?.clips || [];

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in duration-300">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Rendered Viral Clips</h1>
          <p className="text-slate-400 mt-1 text-sm">
            Engagement-optimized 9:16 vertical shorts with kinetic captions and active-speaker framing.
          </p>
        </div>

        {jobs.length > 1 && (
          <div className="flex items-center space-x-2">
            <label className="text-xs font-semibold text-slate-400 uppercase">Select Job:</label>
            <select
              className="bg-slate-900 border border-slate-800 text-sm text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={selectedJob?.job_id || ''}
              onChange={(e) => {
                const j = jobs.find((x) => x.job_id === e.target.value);
                if (j) {
                  setSelectedJob(j);
                  if (onSelectJob) onSelectJob(j.job_id);
                }
              }}
            >
              {jobs.map((j) => (
                <option key={j.job_id} value={j.job_id}>
                  #{j.job_id} - {j.video_title ? j.video_title.slice(0, 30) : 'Video'} ({j.clip_count} clips)
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {clips.length === 0 ? (
        <Card className="text-center py-20 text-slate-500">
          <p className="text-base font-semibold text-slate-400">No clips available for this run yet.</p>
          <p className="text-xs mt-1">If the job is still processing, check the Processing tab.</p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {clips.map((clip, idx) => {
            const videoUrl = `/videos/${selectedJob.job_id}/vertical_${idx}.mp4`;
            const thumbUrl = `/thumbnails/${selectedJob.job_id}/clip_${idx}_thumb.jpg`;

            return (
              <Card key={idx} className="flex flex-col overflow-hidden p-0 border-slate-800 hover:border-slate-700 transition-all group">
                {/* 9:16 Video Container */}
                <div className="relative aspect-[9/16] bg-slate-950 overflow-hidden">
                  <video
                    src={videoUrl}
                    poster={thumbUrl}
                    controls
                    preload="metadata"
                    className="w-full h-full object-cover"
                  />

                  {/* Viral Score Badge */}
                  <div className="absolute top-3 left-3 pointer-events-none">
                    <Badge variant={clip.viral_score >= 80 ? 'green' : 'indigo'} className="shadow-lg backdrop-blur-md">
                      ★ {clip.viral_score}/100 VIRAL
                    </Badge>
                  </div>

                  {/* Duration Pill */}
                  <div className="absolute top-3 right-3 pointer-events-none">
                    <span className="bg-slate-950/80 backdrop-blur-md text-slate-300 text-[10px] font-mono px-2 py-0.5 rounded-md border border-slate-800">
                      {clip.duration}s
                    </span>
                  </div>
                </div>

                {/* Clip Meta & Actions */}
                <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                  <div>
                    <h3 className="font-bold text-sm text-white line-clamp-2 leading-snug group-hover:text-indigo-400 transition-colors">
                      {clip.viral_hook_text || clip.video_title || `Clip #${idx + 1}`}
                    </h3>
                    <p className="text-xs text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                      {clip.viral_reason}
                    </p>
                  </div>

                  <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      className="flex-1 text-xs"
                      onClick={() => setEditingClip({ ...clip, index: idx, jobId: selectedJob.job_id })}
                    >
                      Edit 🎨
                    </Button>
                    <Button
                      variant="primary"
                      size="sm"
                      className="flex-1 text-xs"
                      onClick={() => setPublishingClip({ ...clip, index: idx, jobId: selectedJob.job_id })}
                    >
                      Publish 🚀
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Clip Editor Modal */}
      {editingClip && (
        <ClipEditorModal
          isOpen={Boolean(editingClip)}
          clip={editingClip}
          onClose={() => setEditingClip(null)}
          onUpdated={() => {
            setEditingClip(null);
            fetchJobs();
          }}
        />
      )}

      {/* Publish Modal */}
      {publishingClip && (
        <PublishModal
          isOpen={Boolean(publishingClip)}
          clip={publishingClip}
          onClose={() => setPublishingClip(null)}
        />
      )}
    </div>
  );
}
