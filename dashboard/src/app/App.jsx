import React, { useState } from 'react';
import { CreateView } from '../features/create/CreateView';
import { ProcessingView } from '../features/processing/ProcessingView';
import { ResultsView } from '../features/results/ResultsView';
import { LiveMonitorView } from '../features/live-monitor/LiveMonitorView';
import { HistoryView } from '../features/history/HistoryView';
import { SettingsView } from '../features/settings/SettingsView';

export function App() {
  const [activeTab, setActiveTab] = useState('create');
  const [activeJobId, setActiveJobId] = useState(null);

  const handleJobCreated = (jobId) => {
    setActiveJobId(jobId);
    setActiveTab('processing');
  };

  const handleSelectJob = (jobId) => {
    setActiveJobId(jobId);
    setActiveTab('results');
  };

  const navItems = [
    { id: 'create', label: 'Create & Batch', icon: '⚡' },
    { id: 'processing', label: 'Processing Telemetry', icon: '📡' },
    { id: 'results', label: 'Results & Clips', icon: '🎬' },
    { id: 'monitor', label: 'Live Monitor 24/7', icon: '🔴' },
    { id: 'history', label: 'Job History', icon: '📁' },
    { id: 'settings', label: 'Settings Vault', icon: '⚙️' },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-[#080c14] text-slate-100 selection:bg-indigo-500 selection:text-white">
      {/* Top Navbar */}
      <header className="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-md border-b border-slate-800/80 px-6 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('create')}>
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-600/30">
              <span className="font-black text-white text-lg">C</span>
            </div>
            <div>
              <span className="font-black text-xl tracking-tight text-white flex items-center gap-1.5">
                CLIPORA
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 uppercase tracking-widest">
                  v0.1.0
                </span>
              </span>
            </div>
          </div>

          {/* Navigation Pill List */}
          <nav className="hidden md:flex items-center space-x-1 bg-slate-900/90 border border-slate-800 p-1 rounded-xl">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                  activeTab === item.id
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            ))}
          </nav>

          {/* Active Job Quick Indicator */}
          {activeJobId && (
            <div
              onClick={() => setActiveTab('processing')}
              className="flex items-center space-x-2 bg-indigo-500/10 border border-indigo-500/30 px-3 py-1.5 rounded-lg text-xs font-mono text-indigo-300 cursor-pointer hover:bg-indigo-500/20 transition-all"
            >
              <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping"></span>
              <span>Job #{activeJobId}</span>
            </div>
          )}
        </div>

        {/* Mobile Navigation Bar */}
        <div className="md:hidden flex space-x-1 overflow-x-auto pt-3 border-t border-slate-800/50 mt-3 pb-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap ${
                activeTab === item.id ? 'bg-indigo-600 text-white' : 'text-slate-400'
              }`}
            >
              {item.icon} {item.label}
            </button>
          ))}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
        {activeTab === 'create' && <CreateView onJobCreated={handleJobCreated} />}
        {activeTab === 'processing' && <ProcessingView activeJobId={activeJobId} onSelectJob={handleSelectJob} />}
        {activeTab === 'results' && <ResultsView activeJobId={activeJobId} onSelectJob={handleSelectJob} />}
        {activeTab === 'monitor' && <LiveMonitorView />}
        {activeTab === 'history' && <HistoryView onSelectJob={handleSelectJob} />}
        {activeTab === 'settings' && <SettingsView />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 px-6 text-center text-xs text-slate-500">
        <p>Clipora Autonomous AI Video Clipping, Reframing & Publishing Platform • Self-Hosted & Process-Isolated</p>
      </footer>
    </div>
  );
}
