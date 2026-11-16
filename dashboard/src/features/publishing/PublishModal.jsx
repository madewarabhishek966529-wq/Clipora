import React, { useState } from 'react';
import { Modal, Button, Input } from '../../components/primitives';
import { SOCIAL_PLATFORMS } from '../../lib/constants';
import { api } from '../../api/client';

export function PublishModal({ isOpen, onClose, clip }) {
  const [selectedPlatforms, setSelectedPlatforms] = useState(['tiktok', 'instagram', 'youtube_shorts']);
  const [scheduleMode, setScheduleMode] = useState('auto'); // 'now' | 'auto' | 'manual'
  const [manualTime, setManualTime] = useState('');
  const [caption, setCaption] = useState(
    clip?.video_description_for_tiktok || clip?.video_title || clip?.viral_hook_text || ''
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  if (!clip) return null;

  const togglePlatform = (id) => {
    if (selectedPlatforms.includes(id)) {
      if (selectedPlatforms.length > 1) {
        setSelectedPlatforms(selectedPlatforms.filter((p) => p !== id));
      }
    } else {
      setSelectedPlatforms([...selectedPlatforms, id]);
    }
  };

  const handlePublish = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const res = await api.triggerPublish(clip.jobId, clip.index, {
        platforms: selectedPlatforms,
        schedule_mode: scheduleMode,
        manual_scheduled_for: scheduleMode === 'manual' ? manualTime : undefined,
        caption: caption.trim() || undefined,
      });

      setSuccess(`Post scheduled successfully! ID: ${res.post_id || res.intent_id}`);
      setTimeout(() => {
        onClose();
      }, 2000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Publish to Social Platforms" maxWidth="max-w-xl">
      <div className="space-y-6">
        {error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-300 text-xs">
            {error}
          </div>
        )}

        {success && (
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-emerald-300 text-xs">
            {success}
          </div>
        )}

        {/* Platform Selection */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Target Social Channels
          </label>
          <div className="grid grid-cols-3 gap-2">
            {SOCIAL_PLATFORMS.map((plat) => {
              const active = selectedPlatforms.includes(plat.id);
              return (
                <button
                  key={plat.id}
                  type="button"
                  onClick={() => togglePlatform(plat.id)}
                  className={`p-3 rounded-xl border text-xs font-bold text-center transition-all ${
                    active
                      ? 'border-indigo-500 bg-indigo-500/20 text-white shadow'
                      : 'border-slate-800 bg-slate-950 text-slate-500 hover:border-slate-700'
                  }`}
                >
                  {plat.name}
                </button>
              );
            })}
          </div>
        </div>

        {/* Scheduling Mode */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Publish Timing
          </label>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => setScheduleMode('now')}
              className={`p-3 rounded-xl border text-xs font-semibold text-center transition-all ${
                scheduleMode === 'now' ? 'border-indigo-500 bg-indigo-500/20 text-white' : 'border-slate-800 text-slate-400'
              }`}
            >
              Post Now ⚡
            </button>
            <button
              type="button"
              onClick={() => setScheduleMode('auto')}
              className={`p-3 rounded-xl border text-xs font-semibold text-center transition-all ${
                scheduleMode === 'auto' ? 'border-indigo-500 bg-indigo-500/20 text-white' : 'border-slate-800 text-slate-400'
              }`}
            >
              SmartScheduler (Prime-Time) 🎯
            </button>
            <button
              type="button"
              onClick={() => setScheduleMode('manual')}
              className={`p-3 rounded-xl border text-xs font-semibold text-center transition-all ${
                scheduleMode === 'manual' ? 'border-indigo-500 bg-indigo-500/20 text-white' : 'border-slate-800 text-slate-400'
              }`}
            >
              Custom Time 📅
            </button>
          </div>

          {scheduleMode === 'auto' && (
            <p className="text-xs text-indigo-400 mt-2 bg-indigo-500/10 p-2.5 rounded-lg border border-indigo-500/20">
              SmartScheduler automatically selects the highest-engagement prime-time slot (18:00–21:00) with a 90-minute minimum clearance from existing posts.
            </p>
          )}

          {scheduleMode === 'manual' && (
            <div className="mt-3">
              <Input
                type="datetime-local"
                label="Scheduled Date & Time (UTC)"
                value={manualTime}
                onChange={(e) => setManualTime(e.target.value)}
                required
              />
            </div>
          )}
        </div>

        {/* Caption Editor */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
            Caption & Hashtags
          </label>
          <textarea
            rows={4}
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Viral short caption with engaging question and hashtags..."
          />
        </div>

        <div className="flex justify-end space-x-3 pt-3 border-t border-slate-800">
          <Button variant="secondary" size="sm" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button size="sm" onClick={handlePublish} loading={loading}>
            Confirm & Publish 🚀
          </Button>
        </div>
      </div>
    </Modal>
  );
}
