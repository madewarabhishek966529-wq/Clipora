import React, { useState, useEffect } from 'react';
import { Card, Button, Input } from '../../components/primitives';
import { api } from '../../api/client';

export function SettingsView() {
  const [config, setConfig] = useState(null);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);

  const fetchConfig = async () => {
    try {
      const data = await api.getConfig();
      setConfig(data);
      setFormData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const handleTextChange = (key, val) => {
    setFormData((prev) => ({ ...prev, [key]: val }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setStatusMsg(null);
    try {
      await api.updateConfig(formData);
      setStatusMsg({ type: 'success', text: 'Configuration saved successfully!' });
      await fetchConfig();
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.message });
    } finally {
      setSaving(false);
    }
  };

  const handleFileUpload = async (type, file) => {
    if (!file) return;
    try {
      if (type === 'cookies') await api.uploadCookies(file);
      if (type === 'logo') await api.uploadLogo(file);
      if (type === 'font') await api.uploadFont(file);
      alert(`${type.toUpperCase()} uploaded successfully!`);
    } catch (err) {
      alert(`Upload failed: ${err.message}`);
    }
  };

  if (loading) {
    return <div className="text-center py-20 text-slate-400">Loading settings vault...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-300">
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Settings & Credential Vault</h1>
        <p className="text-slate-400 mt-1 text-sm">
          Securely manage AI keys, publishing tokens, session cookies, and brand styling assets.
        </p>
      </div>

      {statusMsg && (
        <div
          className={`p-3 rounded-lg text-xs ${
            statusMsg.type === 'success'
              ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-300'
              : 'bg-rose-500/10 border border-rose-500/30 text-rose-300'
          }`}
        >
          {statusMsg.text}
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* AI & ASR Credentials */}
        <Card className="space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">AI & Speech Recognition Keys</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              type="password"
              label="Gemini API Key"
              placeholder="AIzaSy..."
              value={formData.gemini_api_key || ''}
              onChange={(e) => handleTextChange('gemini_api_key', e.target.value)}
            />
            <Input
              type="password"
              label="Deepgram API Key"
              placeholder="Token..."
              value={formData.deepgram_api_key || ''}
              onChange={(e) => handleTextChange('deepgram_api_key', e.target.value)}
            />
            <Input
              type="password"
              label="ElevenLabs API Key"
              placeholder="xi-api-key..."
              value={formData.elevenlabs_api_key || ''}
              onChange={(e) => handleTextChange('elevenlabs_api_key', e.target.value)}
            />
          </div>
        </Card>

        {/* Social Publishing Vault */}
        <Card className="space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Zernio Social Publishing</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              type="password"
              label="Zernio API Key"
              placeholder="Bearer key..."
              value={formData.zernio_api_key || ''}
              onChange={(e) => handleTextChange('zernio_api_key', e.target.value)}
            />
            <Input
              type="number"
              label="Min Spacing Gap Between Posts (Seconds)"
              value={formData.zernio_min_gap_seconds || 5400}
              onChange={(e) => handleTextChange('zernio_min_gap_seconds', parseInt(e.target.value, 10))}
            />
          </div>
        </Card>

        {/* Live Stream Twitch Credentials */}
        <Card className="space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Twitch Helix API App Credentials</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Twitch Client ID"
              value={formData.twitch_client_id || ''}
              onChange={(e) => handleTextChange('twitch_client_id', e.target.value)}
            />
            <Input
              type="password"
              label="Twitch Client Secret"
              value={formData.twitch_client_secret || ''}
              onChange={(e) => handleTextChange('twitch_client_secret', e.target.value)}
            />
          </div>
        </Card>

        {/* Concurrency & Network Limits */}
        <Card className="space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Concurrency & System Limits</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              type="number"
              label="Max Concurrent Processing Jobs"
              value={formData.max_concurrent_jobs || 2}
              onChange={(e) => handleTextChange('max_concurrent_jobs', parseInt(e.target.value, 10))}
              min={1}
              max={10}
            />
            <Input
              type="number"
              label="API Rate Limit (Reqs / Minute)"
              value={formData.rate_limit_per_minute || 60}
              onChange={(e) => handleTextChange('rate_limit_per_minute', parseInt(e.target.value, 10))}
              min={10}
              max={500}
            />
          </div>
        </Card>

        {/* Asset Uploads */}
        <Card className="space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Asset Uploads</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                YouTube cookies.txt
              </label>
              <input
                type="file"
                accept=".txt"
                onChange={(e) => handleFileUpload('cookies', e.target.files[0])}
                className="w-full text-xs text-slate-400 file:mr-2 file:py-1 file:px-2.5 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-white bg-slate-950 p-2 rounded-lg border border-slate-800 cursor-pointer"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Brand Logo Watermark (.png)
              </label>
              <input
                type="file"
                accept="image/png"
                onChange={(e) => handleFileUpload('logo', e.target.files[0])}
                className="w-full text-xs text-slate-400 file:mr-2 file:py-1 file:px-2.5 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-white bg-slate-950 p-2 rounded-lg border border-slate-800 cursor-pointer"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Custom Font (.ttf / .otf)
              </label>
              <input
                type="file"
                accept=".ttf,.otf"
                onChange={(e) => handleFileUpload('font', e.target.files[0])}
                className="w-full text-xs text-slate-400 file:mr-2 file:py-1 file:px-2.5 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-white bg-slate-950 p-2 rounded-lg border border-slate-800 cursor-pointer"
              />
            </div>
          </div>
        </Card>

        <div className="flex justify-end">
          <Button type="submit" size="lg" loading={saving}>
            Save Changes ✓
          </Button>
        </div>
      </form>
    </div>
  );
}
