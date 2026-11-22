import React, { useState, useRef } from 'react';
import { Camera, Video, Upload, Trash2, AlertCircle, CheckCircle, FileText } from 'lucide-react';
import { uploadMediaFile } from '../../api/complaints';
import { ComplaintMediaItem } from '../../types';

interface MediaUploaderProps {
  mediaList: ComplaintMediaItem[];
  onMediaAdded: (item: ComplaintMediaItem) => void;
  onMediaRemoved: (index: number) => void;
}

export const MediaUploader: React.FC<MediaUploaderProps> = ({
  mediaList,
  onMediaAdded,
  onMediaRemoved,
}) => {
  const [uploading, setUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setError(null);
    setUploading(true);

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        if (file.size > 25 * 1024 * 1024) {
          setError(`File ${file.name} exceeds the 25MB limit.`);
          continue;
        }
        const uploadedItem = await uploadMediaFile(file);
        onMediaAdded(uploadedItem);
      }
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('Authentication required to upload media. Please sign in or use 1-Click Demo Citizen.');
      } else {
        setError(err.response?.data?.detail || 'Media upload encountered an error.');
      }
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-xs font-semibold text-slate-200 flex items-center gap-2">
          <Camera className="w-4 h-4 text-blue-400" />
          <span>Incident Media (Photographs & Videos)</span>
        </label>
        <span className="text-[11px] text-slate-400">
          Max 25MB each &bull; PNG, JPG, MP4, MOV
        </span>
      </div>

      {error && (
        <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Drag & Drop Upload Zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`p-6 sm:p-8 rounded-2xl border-2 border-dashed text-center cursor-pointer transition-all ${
          dragActive
            ? 'border-blue-500 bg-blue-500/10'
            : 'border-slate-800 bg-slate-950/70 hover:border-slate-700 hover:bg-slate-950'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*,video/*"
          onChange={(e) => handleFiles(e.target.files)}
          className="hidden"
        />

        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-blue-600/10 text-blue-400 flex items-center justify-center border border-blue-500/20 shadow-md">
            {uploading ? (
              <Upload className="w-6 h-6 animate-bounce" />
            ) : (
              <Camera className="w-6 h-6" />
            )}
          </div>
          <div className="space-y-1">
            <p className="text-sm font-semibold text-white">
              {uploading ? 'Uploading Media Evidence...' : 'Click to upload or drag & drop photos/videos'}
            </p>
            <p className="text-xs text-slate-400">
              Photographs will be analyzed by our local YOLO road damage detector.
            </p>
          </div>
        </div>
      </div>

      {/* Uploaded Media Thumbnails */}
      {mediaList.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
          {mediaList.map((item, idx) => (
            <div
              key={idx}
              className="group relative rounded-xl overflow-hidden border border-slate-800 bg-slate-900 shadow-md flex flex-col justify-between"
            >
              {item.media_type === 'IMAGE' ? (
                <div className="h-28 bg-black/40 overflow-hidden relative">
                  <img
                    src={item.file_url}
                    alt="Complaint evidence"
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                  <span className="absolute top-1.5 left-1.5 px-2 py-0.5 rounded bg-black/70 text-[10px] font-bold text-white uppercase tracking-wider backdrop-blur-sm">
                    Photo
                  </span>
                </div>
              ) : item.media_type === 'VIDEO' ? (
                <div className="h-28 bg-slate-950 flex flex-col items-center justify-center p-2 relative">
                  <Video className="w-8 h-8 text-cyan-400 mb-1" />
                  <span className="text-[10px] text-slate-400 truncate max-w-full">
                    {item.file_name || 'Video Clip'}
                  </span>
                  <span className="absolute top-1.5 left-1.5 px-2 py-0.5 rounded bg-cyan-900/70 text-[10px] font-bold text-cyan-300 uppercase tracking-wider backdrop-blur-sm">
                    Video
                  </span>
                </div>
              ) : (
                <div className="h-28 bg-slate-950 flex flex-col items-center justify-center p-2">
                  <FileText className="w-8 h-8 text-blue-400 mb-1" />
                  <span className="text-[10px] text-slate-400">Audio Note</span>
                </div>
              )}

              <div className="p-2 bg-slate-950/90 flex items-center justify-between border-t border-slate-800">
                <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                  <CheckCircle className="w-3 h-3" /> Ready
                </span>
                <button
                  type="button"
                  onClick={() => onMediaRemoved(idx)}
                  className="p-1 rounded text-slate-400 hover:text-rose-400 transition-colors"
                  title="Remove file"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
