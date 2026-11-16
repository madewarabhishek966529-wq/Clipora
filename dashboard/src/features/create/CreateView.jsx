import React, { useState } from 'react';
import { Card, Button, Input, Select, Badge } from '../../components/primitives';
import { REFRAME_MODES, TRANSCRIPTION_PROVIDERS } from '../../lib/constants';
import { api } from '../../api/client';

export function CreateView({ onJobCreated }) {
  const [mode, setMode] = useState('single'); // 'single' | 'batch' | 'upload'
  const [url, setUrl] = useState('');
  const [batchUrls, setBatchUrls] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [reframeMode, setReframeMode] = useState('auto');
  const [transcriptionProvider, setTranscriptionProvider] = useState('deepgram');
  const [customInstructions, setCustomInstructions] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      if (mode === 'single') {
        if (!url.trim()) throw new Error('Please enter a valid video URL.');
        const res = await api.createJob({
          source_url: url.trim(),
          reframe_mode: reframeMode,
          transcription_provider: transcriptionProvider,
          custom_instructions: customInstructions.trim() || undefined,
        });
        setSuccess(`Job #${res.job_id} enqueued successfully!`);
        setUrl('');
        if (onJobCreated) onJobCreated(res.job_id);

      } else if (mode === 'batch') {
        const urls = batchUrls
          .split('\n')
          .map((u) => u.trim())
          .filter(Boolean);
        if (urls.length === 0) throw new Error('Please enter at least one URL.');

        const res = await api.createBatchJobs({
          urls,
          reframe_mode: reframeMode,
          transcription_provider: transcriptionProvider,
          custom_instructions: customInstructions.trim() || undefined,
        });
        setSuccess(`${res.count} jobs enqueued successfully!`);
        setBatchUrls('');
        if (onJobCreated && res.jobs[0]) onJobCreated(res.jobs[0].job_id);

      } else if (mode === 'upload') {
        if (!selectedFile) throw new Error('Please select a local video file.');
        const uploadRes = await api.uploadVideo(selectedFile);
        const jobRes = await api.createJob({
          input_file: uploadRes.input_file,
          reframe_mode: reframeMode,
          transcription_provider: transcriptionProvider,
          custom_instructions: customInstructions.trim() || undefined,
        });
        setSuccess(`Uploaded and queued Job #${jobRes.job_id}!`);
        setSelectedFile(null);
        if (onJobCreated) onJobCreated(jobRes.job_id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-300">
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Create & Batch Intake</h1>
        <p className="text-slate-400 mt-1 text-sm">
          Convert long-form landscape video (YouTube, Twitch, Kick, uploads) into viral 9:16 vertical shorts.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-rose-400 hover:text-white font-bold ml-2">×</button>
        </div>
      )}

      {success && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-300 text-sm flex items-center justify-between">
          <span>{success}</span>
          <button onClick={() => setSuccess(null)} className="text-emerald-400 hover:text-white font-bold ml-2">×</button>
        </div>
      )}

      {/* Mode Tabs */}
      <div className="flex bg-slate-900 border border-slate-800 p-1 rounded-xl">
        <button
          onClick={() => setMode('single')}
          className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${
            mode === 'single' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
          }`}
        >
          Single Video URL
        </button>
        <button
          onClick={() => setMode('batch')}
          className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${
            mode === 'batch' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
          }`}
        >
          Batch URLs
        </button>
        <button
          onClick={() => setMode('upload')}
          className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${
            mode === 'upload' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
          }`}
        >
          Upload Local Video
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card className="space-y-5">
          {mode === 'single' && (
            <Input
              label="Source Video URL"
              placeholder="https://www.youtube.com/watch?v=... or https://kick.com/..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
            />
          )}

          {mode === 'batch' && (
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Paste Multiple URLs (One per line)
              </label>
              <textarea
                rows={5}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
                placeholder="https://youtube.com/watch?v=aaa&#10;https://youtube.com/watch?v=bbb&#10;https://kick.com/video/ccc"
                value={batchUrls}
                onChange={(e) => setBatchUrls(e.target.value)}
                required
              />
            </div>
          )}

          {mode === 'upload' && (
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Local Video File (MP4, MKV, WebM)
              </label>
              <input
                type="file"
                accept="video/*"
                onChange={(e) => setSelectedFile(e.target.files[0] || null)}
                className="w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer bg-slate-950 p-2 rounded-lg border border-slate-800"
                required
              />
            </div>
          )}

          {/* Reframe Mode Selector */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              9:16 Vertical Reframing Mode
            </label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {REFRAME_MODES.map((rm) => (
                <div
                  key={rm.id}
                  onClick={() => setReframeMode(rm.id)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                    reframeMode === rm.id
                      ? 'border-indigo-500 bg-indigo-500/10 shadow-lg shadow-indigo-500/10'
                      : 'border-slate-800 bg-slate-950/60 hover:border-slate-700'
                  }`}
                >
                  <div className="font-semibold text-sm text-white">{rm.name}</div>
                  <div className="text-xs text-slate-400 mt-1">{rm.desc}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Transcription Provider Selector */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Transcription & Diarization Provider
            </label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {TRANSCRIPTION_PROVIDERS.map((tp) => (
                <div
                  key={tp.id}
                  onClick={() => setTranscriptionProvider(tp.id)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                    transcriptionProvider === tp.id
                      ? 'border-indigo-500 bg-indigo-500/10'
                      : 'border-slate-800 bg-slate-950/60 hover:border-slate-700'
                  }`}
                >
                  <div className="font-semibold text-sm text-white">{tp.name}</div>
                  <div className="text-xs text-slate-400 mt-1">{tp.desc}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Custom Prompt Instructions */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
              Custom AI Editing Instructions (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. Focus on debate arguments, exclude intro banter, highlight tech predictions"
              value={customInstructions}
              onChange={(e) => setCustomInstructions(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </Card>

        <div className="flex justify-end">
          <Button type="submit" size="lg" loading={loading} className="w-full md:w-auto">
            Start Autonomous Pipeline →
          </Button>
        </div>
      </form>
    </div>
  );
}
