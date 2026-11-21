import React, { useState, useRef } from 'react';
import { Mic, Square, Trash2, Upload, AlertCircle, Volume2, Sparkles } from 'lucide-react';
import { uploadMediaFile } from '../../api/complaints';
import { ComplaintMediaItem } from '../../types';

interface VoiceRecorderProps {
  onAudioUploaded: (mediaItem: ComplaintMediaItem) => void;
  onAudioRemoved: () => void;
  currentAudio?: ComplaintMediaItem;
}

export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({
  onAudioUploaded,
  onAudioRemoved,
  currentAudio,
}) => {
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [recordingDuration, setRecordingDuration] = useState<number>(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(currentAudio?.file_url || null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerIntervalRef = useRef<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const startRecording = async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const localPreview = URL.createObjectURL(audioBlob);
        setAudioUrl(localPreview);

        // Upload to backend
        const audioFile = new File([audioBlob], `voice_note_${Date.now()}.webm`, { type: 'audio/webm' });
        await handleUpload(audioFile);

        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingDuration(0);

      timerIntervalRef.current = setInterval(() => {
        setRecordingDuration((prev) => prev + 1);
      }, 1000);
    } catch (err: any) {
      setError(`Microphone access error: ${err.message || 'Permission denied'}`);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      clearInterval(timerIntervalRef.current);
    }
  };

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    setError(null);
    try {
      const mediaItem = await uploadMediaFile(file);
      onAudioUploaded(mediaItem);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload audio recording.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAudioUrl(URL.createObjectURL(file));
      await handleUpload(file);
    }
  };

  const handleClear = () => {
    setAudioUrl(null);
    setRecordingDuration(0);
    setError(null);
    onAudioRemoved();
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <div className="space-y-3 p-4 rounded-xl bg-slate-950 border border-slate-800">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Mic className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-semibold text-slate-200">
            Voice Recording / Audio Grievance
          </span>
        </div>
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 text-[10px] font-medium border border-cyan-500/20">
          <Sparkles className="w-3 h-3 text-cyan-400" />
          <span>Telugu (తెలుగు) & English</span>
        </div>
      </div>

      <p className="text-[11px] text-slate-400">
        Speak in Telugu or English to describe the infrastructure issue. Our local faster-whisper speech AI will transcribe it directly into the complaint registry.
      </p>

      {error && (
        <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Record or Upload Action Area */}
      {!audioUrl ? (
        <div className="flex flex-col sm:flex-row items-center gap-3 pt-1">
          {isRecording ? (
            <div className="flex items-center gap-3 w-full sm:w-auto">
              <button
                type="button"
                onClick={stopRecording}
                className="px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs flex items-center gap-2 shadow-lg shadow-rose-600/30 animate-pulse"
              >
                <Square className="w-3.5 h-3.5" />
                <span>Stop Recording ({formatTime(recordingDuration)})</span>
              </button>
              <div className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                <span className="text-xs font-mono text-rose-400 font-bold">LIVE MIC</span>
              </div>
            </div>
          ) : (
            <button
              type="button"
              onClick={startRecording}
              className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 hover:text-white font-medium text-xs flex items-center justify-center gap-2 transition-colors"
            >
              <Mic className="w-4 h-4 text-cyan-400" />
              <span>Record Voice Note</span>
            </button>
          )}

          <span className="text-xs text-slate-600 hidden sm:inline">or</span>

          {/* Upload file fallback */}
          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*"
              onChange={handleFileChange}
              className="hidden"
            />
            <button
              type="button"
              disabled={isRecording || isUploading}
              onClick={() => fileInputRef.current?.click()}
              className="w-full sm:w-auto px-3.5 py-2.5 rounded-xl bg-slate-900/60 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 text-xs font-medium flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
            >
              <Upload className="w-3.5 h-3.5 text-slate-400" />
              <span>{isUploading ? 'Uploading Audio...' : 'Upload Audio File (.wav, .mp3, .m4a)'}</span>
            </button>
          </div>
        </div>
      ) : (
        /* Audio Preview Player */
        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-cyan-600/20 text-cyan-400 flex items-center justify-center">
              <Volume2 className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-semibold text-slate-200">
                Voice Note Attached
              </div>
              <div className="text-[10px] text-cyan-400 font-mono">
                {isUploading ? 'Processing upload...' : '✓ Ready for faster-whisper local transcription'}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <audio controls src={audioUrl} className="h-8 max-w-[200px] sm:max-w-[280px]" />
            <button
              type="button"
              onClick={handleClear}
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
              title="Remove Audio"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
