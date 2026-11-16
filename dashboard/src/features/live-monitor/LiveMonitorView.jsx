import React, { useState, useEffect } from 'react';
import { Card, Button, Input, Select, Badge } from '../../components/primitives';
import { api } from '../../api/client';

export function LiveMonitorView() {
  const [monitors, setMonitors] = useState([]);
  const [platform, setPlatform] = useState('kick');
  const [channelId, setChannelId] = useState('');
  const [preliveSkip, setPreliveSkip] = useState(30);
  const [minViralScore, setMinViralScore] = useState(70);
  const [autoPublish, setAutoPublish] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchMonitors = async () => {
    try {
      const data = await api.listMonitors();
      setMonitors(data.monitors || []);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchMonitors();
    const interval = setInterval(fetchMonitors, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleAddMonitor = async (e) => {
    e.preventDefault();
    if (!channelId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await api.addMonitor({
        platform,
        channel_id: channelId.trim(),
        enabled: true,
        prelive_skip_minutes: parseInt(preliveSkip, 10),
        min_viral_score: parseInt(minViralScore, 10),
        auto_publish: autoPublish,
      });
      setChannelId('');
      await fetchMonitors();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this channel monitor?')) return;
    try {
      await api.deleteMonitor(id);
      await fetchMonitors();
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-300">
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">24/7 Autonomous Live Monitor</h1>
        <p className="text-slate-400 mt-1 text-sm">
          Continuously polls creator channels on Kick, Twitch, and YouTube RSS. Slices live streams and auto-publishes viral moments hands-free.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-300 text-xs">
          {error}
        </div>
      )}

      {/* Add Monitor Card */}
      <Card>
        <form onSubmit={handleAddMonitor} className="space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Register Channel Monitor</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Select
              label="Streaming Platform"
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              options={[
                { id: 'kick', name: 'Kick.com' },
                { id: 'twitch', name: 'Twitch.tv' },
                { id: 'youtube', name: 'YouTube RSS' },
              ]}
            />
            <Input
              label="Channel Handle or ID"
              placeholder="e.g. xqc or UCxxxxxxxx"
              value={channelId}
              onChange={(e) => setChannelId(e.target.value)}
              required
            />
            <Input
              type="number"
              label="Pre-Live Skip (Minutes)"
              value={preliveSkip}
              onChange={(e) => setPreliveSkip(e.target.value)}
              min={0}
              max={120}
            />
          </div>

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pt-3 border-t border-slate-800">
            <div className="flex items-center space-x-6 text-xs text-slate-300">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoPublish}
                  onChange={(e) => setAutoPublish(e.target.checked)}
                  className="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500"
                />
                <span>Auto-Publish Viral Moments to Socials</span>
              </label>
              <div className="flex items-center space-x-2">
                <span>Min Viral Score:</span>
                <span className="font-bold text-indigo-400">{minViralScore}+</span>
              </div>
            </div>

            <Button type="submit" size="sm" loading={loading}>
              Add Monitor +
            </Button>
          </div>
        </form>
      </Card>

      {/* Active Monitors List */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">
          Active Channel Monitors ({monitors.length})
        </h3>

        {monitors.length === 0 ? (
          <Card className="text-center py-12 text-slate-500">
            <p>No channel monitors registered yet.</p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {monitors.map((m) => (
              <Card key={m.id} className="space-y-3 relative overflow-hidden">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="font-black uppercase text-sm tracking-wide text-white">
                      {m.channel_id}
                    </span>
                    <Badge variant="slate" className="uppercase font-mono text-[10px]">
                      {m.platform}
                    </Badge>
                  </div>
                  {m.is_active_live ? (
                    <Badge variant="red" className="animate-pulse">
                      🔴 LIVE STREAMING
                    </Badge>
                  ) : (
                    <Badge variant="green">STANDBY</Badge>
                  )}
                </div>

                <div className="text-xs text-slate-400 space-y-1">
                  <div>Pre-live skip: <strong className="text-slate-300">{m.prelive_skip_minutes} min</strong></div>
                  <div>Auto-Publish: <strong className="text-slate-300">{m.auto_publish ? 'Enabled' : 'Disabled'}</strong></div>
                  <div>Last Checked: <span className="font-mono">{m.last_checked_at ? new Date(m.last_checked_at).toLocaleTimeString() : 'Pending'}</span></div>
                </div>

                <div className="pt-2 border-t border-slate-800 flex justify-end">
                  <Button variant="ghost" size="sm" className="text-rose-400 text-xs" onClick={() => handleDelete(m.id)}>
                    Remove
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
