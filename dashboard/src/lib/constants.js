export const APP_NAME = "Clipora";
export const APP_VERSION = "0.1.0";

export const REFRAME_MODES = [
  { id: 'auto', name: 'Auto Tripod', desc: 'Active speaker tracking locked per shot (Recommended)' },
  { id: 'subject', name: 'Subject Multi-Class', desc: 'Weighted interest tracking (Face, Person, Objects)' },
  { id: 'disabled', name: 'Letterboxed Landscape', desc: 'Full landscape frame with letterboxing' },
];

export const TRANSCRIPTION_PROVIDERS = [
  { id: 'deepgram', name: 'Deepgram Nova-3', desc: 'Multilingual automatic code-switching & diarization' },
  { id: 'elevenlabs', name: 'ElevenLabs Scribe', desc: 'Audio event tagging (laughter, applause)' },
  { id: 'whisper', name: 'Local Faster-Whisper', desc: '100% offline hardware-adaptive transcription' },
];

export const SOCIAL_PLATFORMS = [
  { id: 'tiktok', name: 'TikTok', color: 'from-pink-500 to-rose-500' },
  { id: 'instagram', name: 'Instagram Reels', color: 'from-purple-500 to-pink-500' },
  { id: 'youtube_shorts', name: 'YouTube Shorts', color: 'from-red-500 to-red-700' },
];
