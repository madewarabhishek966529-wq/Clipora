/**
 * Clipora REST API Client
 */

const BASE_URL = '/api';

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const headers = options.headers || {};

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errJson = await response.json();
      errorDetail = errJson.error || errJson.detail || JSON.stringify(errJson);
    } catch {
      errorDetail = await response.text();
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Jobs
  createJob: (payload) => request('/jobs', { method: 'POST', body: JSON.stringify(payload) }),
  createBatchJobs: (payload) => request('/jobs/batch', { method: 'POST', body: JSON.stringify(payload) }),
  listJobs: () => request('/jobs'),
  getJob: (jobId) => request(`/jobs/${jobId}`),
  pauseJob: (jobId) => request(`/jobs/${jobId}/pause`, { method: 'POST' }),
  resumeJob: (jobId) => request(`/jobs/${jobId}/resume`, { method: 'POST' }),
  cancelJob: (jobId) => request(`/jobs/${jobId}/cancel`, { method: 'POST' }),
  deleteJob: (jobId) => request(`/jobs/${jobId}`, { method: 'DELETE' }),
  uploadVideo: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return request('/upload', { method: 'POST', body: formData });
  },

  // Per-Clip Operations
  triggerSmartCut: (jobId, clipIndex, minSilenceGap = 0.8) =>
    request(`/clips/${jobId}/${clipIndex}/smartcut`, {
      method: 'POST',
      body: JSON.stringify({ min_silence_gap: minSilenceGap }),
    }),
  triggerReframe: (jobId, clipIndex, reframeMode = 'auto') =>
    request(`/clips/${jobId}/${clipIndex}/reframe`, {
      method: 'POST',
      body: JSON.stringify({ reframe_mode: reframeMode }),
    }),
  triggerPublish: (jobId, clipIndex, payload) =>
    request(`/clips/${jobId}/${clipIndex}/publish`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  triggerEditAI: (jobId, clipIndex, instruction) =>
    request(`/clips/${jobId}/${clipIndex}/edit-ai`, {
      method: 'POST',
      body: JSON.stringify({ instruction }),
    }),

  // Configuration
  getConfig: () => request('/config'),
  updateConfig: (patch) => request('/config', { method: 'POST', body: JSON.stringify(patch) }),
  uploadCookies: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return request('/config/cookies', { method: 'POST', body: formData });
  },
  uploadLogo: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return request('/config/logo', { method: 'POST', body: formData });
  },
  uploadFont: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return request('/config/fonts', { method: 'POST', body: formData });
  },

  // Live Monitors
  listMonitors: () => request('/monitors'),
  addMonitor: (payload) => request('/monitors', { method: 'POST', body: JSON.stringify(payload) }),
  deleteMonitor: (id) => request(`/monitors/${id}`, { method: 'DELETE' }),
};
