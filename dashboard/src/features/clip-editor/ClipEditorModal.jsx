import React, { useState } from 'react';
import { Modal, Button, Input, Select, Card, Badge } from '../../components/primitives';
import { SUBTITLE_PRESETS, GRADE_PRESETS, WATERMARK_POSITIONS } from '../../lib/uiOptions';
import { REFRAME_MODES } from '../../lib/constants';
import { api } from '../../api/client';

export function ClipEditorModal({ isOpen, onClose, clip, onUpdated }) {
  const [activeTab, setActiveTab] = useState('subtitles'); // 'reframe' | 'subtitles' | 'smartcut' | 'hook' | 'logo' | 'banner' | 'ai'
  const [reframeMode, setReframeMode] = useState(clip?.reframe_mode || 'auto');
  const [subtitlePreset, setSubtitlePreset] = useState(clip?.subtitle_preset || 'hormozi_bold');
  const [gradePreset, setGradePreset] = useState(clip?.grade_preset || 'warm_cinematic');
  const [silenceGap, setSilenceGap] = useState(0.8);
  const [hookText, setHookText] = useState(clip?.viral_hook_text || '');
  const [watermarkPos, setWatermarkPos] = useState('top-right');
  const [channelHandle, setChannelHandle] = useState('@creator');
  const [aiPrompt, setAiPrompt] = useState('');
  const [aiResult, setAiResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!clip) return null;

  const handleApplySmartCut = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.triggerSmartCut(clip.jobId, clip.index, silenceGap);
      alert('SmartCut silence removal applied successfully!');
      if (onUpdated) onUpdated();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyReframe = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.triggerReframe(clip.jobId, clip.index, reframeMode);
      alert('Vertical reframe updated successfully!');
      if (onUpdated) onUpdated();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAiEdit = async () => {
    if (!aiPrompt.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.triggerEditAI(clip.jobId, clip.index, aiPrompt.trim());
      setAiResult(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'subtitles', name: 'Subtitles', icon: '💬' },
    { id: 'reframe', name: 'Reframe', icon: '📐' },
    { id: 'smartcut', name: 'Smart Cut', icon: '✂️' },
    { id: 'hook', name: 'Hook Banner', icon: '🎣' },
    { id: 'logo', name: 'Watermark', icon: '🏷️' },
    { id: 'banner', name: 'Attribution', icon: '👑' },
    { id: 'ai', name: 'AI Trim', icon: '✨' },
  ];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Clip #${clip.index + 1} Editor`} maxWidth="max-w-4xl">
      <div className="space-y-6">
        {error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-300 text-xs">
            {error}
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex space-x-1 border-b border-slate-800 pb-2 overflow-x-auto">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`px-3 py-2 text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition-all whitespace-nowrap ${
                activeTab === t.id
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <span>{t.icon}</span>
              <span>{t.name}</span>
            </button>
          ))}
        </div>

        {/* Tab Contents */}
        {activeTab === 'subtitles' && (
          <div className="space-y-4">
            <h4 className="text-sm font-bold text-white">Animated Karaoke Preset</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {SUBTITLE_PRESETS.map((p) => (
                <div
                  key={p.id}
                  onClick={() => setSubtitlePreset(p.id)}
                  className={`p-3 rounded-xl border cursor-pointer transition-all ${
                    subtitlePreset === p.id
                      ? 'border-indigo-500 bg-indigo-500/10 shadow-md'
                      : 'border-slate-800 bg-slate-950/60 hover:border-slate-700'
                  }`}
                >
                  <div className="font-semibold text-xs text-white">{p.name}</div>
                  <div className="mt-2 text-center py-2 bg-slate-900 rounded font-black text-sm uppercase" style={{ color: p.color }}>
                    {p.sample}
                  </div>
                </div>
              ))}
            </div>

            <div className="pt-3 border-t border-slate-800">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Color Grading Preset</label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {GRADE_PRESETS.map((g) => (
                  <button
                    key={g.id}
                    onClick={() => setGradePreset(g.id)}
                    className={`p-2.5 rounded-lg border text-xs text-left transition-all ${
                      gradePreset === g.id ? 'border-indigo-500 bg-indigo-500/10 text-white font-bold' : 'border-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    {g.name}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'reframe' && (
          <div className="space-y-4">
            <h4 className="text-sm font-bold text-white">9:16 Vertical Reframing Mode</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {REFRAME_MODES.map((rm) => (
                <div
                  key={rm.id}
                  onClick={() => setReframeMode(rm.id)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                    reframeMode === rm.id ? 'border-indigo-500 bg-indigo-500/10' : 'border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="font-semibold text-sm text-white">{rm.name}</div>
                  <div className="text-xs text-slate-400 mt-1">{rm.desc}</div>
                </div>
              ))}
            </div>
            <Button onClick={handleApplyReframe} loading={loading} size="sm">
              Re-render Vertical Crop
            </Button>
          </div>
        )}

        {activeTab === 'smartcut' && (
          <div className="space-y-4">
            <h4 className="text-sm font-bold text-white">Smart Cut Silence & Filler Removal</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Detects and purges dead air pauses longer than the threshold and filler words (um, uh, like) while maintaining a natural 0.15s cushion.
            </p>
            <div>
              <div className="flex justify-between text-xs text-slate-300 font-semibold mb-1">
                <span>Minimum Silence Pause Threshold</span>
                <span className="text-indigo-400 font-mono">{silenceGap} seconds</span>
              </div>
              <input
                type="range"
                min="0.3"
                max="2.0"
                step="0.05"
                value={silenceGap}
                onChange={(e) => setSilenceGap(parseFloat(e.target.value))}
                className="w-full accent-indigo-500"
              />
            </div>
            <Button onClick={handleApplySmartCut} loading={loading} size="sm">
              Apply Smart Cut
            </Button>
          </div>
        )}

        {activeTab === 'hook' && (
          <div className="space-y-4">
            <h4 className="text-sm font-bold text-white">Dynamic Curiosity-Gap Hook Banner</h4>
            <Input
              label="Hook Overlay Text (3-8 Words)"
              value={hookText}
              onChange={(e) => setHookText(e.target.value)}
              placeholder="The one mistake everyone makes"
            />
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl text-center">
              <span className="text-xs text-slate-500 block mb-2 font-mono">Rendered Preview</span>
              <div className="inline-block px-5 py-2.5 rounded-xl bg-black/80 border border-white/20 text-white font-black text-base shadow-2xl">
                {hookText || 'Hook Title Overlay'}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'logo' && (
          <div className="space-y-4">
            <h4 className="text-sm font-bold text-white">Watermark Placement</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {WATERMARK_POSITIONS.map((pos) => (
                <button
                  key={pos.id}
                  onClick={() => setWatermarkPos(pos.id)}
                  className={`p-3 rounded-lg border text-xs font-semibold text-center transition-all ${
                    watermarkPos === pos.id ? 'border-indigo-500 bg-indigo-500/10 text-white' : 'border-slate-800 text-slate-400'
                  }`}
                >
                  {pos.name}
                </button>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'banner' && (
          <div className="space-y-4">
            <h4 className="text-sm font-bold text-white">Creator Attribution Banner</h4>
            <Input
              label="Creator Handle"
              value={channelHandle}
              onChange={(e) => setChannelHandle(e.target.value)}
              placeholder="@username"
            />
          </div>
        )}

        {activeTab === 'ai' && (
          <div className="space-y-4">
            <h4 className="text-sm font-bold text-white">Natural Language AI Trimming</h4>
            <p className="text-xs text-slate-400">
              Type an edit instruction in plain English (e.g. "Cut the first 4 seconds", "Remove where he stumbles").
            </p>
            <div className="flex gap-2">
              <Input
                placeholder="e.g. Cut the first 5 seconds"
                value={aiPrompt}
                onChange={(e) => setAiPrompt(e.target.value)}
              />
              <Button onClick={handleRunAiEdit} loading={loading} size="sm">
                Interpret
              </Button>
            </div>
            {aiResult && (
              <div className="p-3 bg-indigo-500/10 border border-indigo-500/30 rounded-lg text-xs space-y-1">
                <div className="font-semibold text-indigo-300">AI Trim Analysis:</div>
                <div>Detected Drop Ranges: {JSON.stringify(aiResult.drop_ranges)}</div>
              </div>
            )}
          </div>
        )}

        <div className="pt-4 border-t border-slate-800 flex justify-end">
          <Button variant="secondary" onClick={onClose} size="sm">
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
}
