import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { trackComplaint } from '../api/complaints';
import { TrackingData, TimelineStage, StatusHistoryItem } from '../types';
import {
  Search,
  CheckCircle2,
  Clock,
  MapPin,
  AlertCircle,
  Shield,
  ArrowRight,
} from 'lucide-react';

export const TrackComplaintPage: React.FC = () => {
  const { trackingId: routeTrackingId } = useParams<{ trackingId?: string }>();
  const navigate = useNavigate();

  const [inputCode, setInputCode] = useState<string>(routeTrackingId || '');
  const [trackingData, setTrackingData] = useState<TrackingData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (codeToSearch: string) => {
    const query = codeToSearch.trim();
    if (!query) return;

    setLoading(true);
    setError(null);
    try {
      const data = await trackComplaint(query);
      setTrackingData(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || `No record found with tracking code '${query}'.`);
      setTrackingData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (routeTrackingId) {
      handleSearch(routeTrackingId);
    }
  }, [routeTrackingId]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputCode.trim()) {
      navigate(`/track/${inputCode.trim().toUpperCase()}`);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-10">
      {/* Header */}
      <div className="text-center space-y-3 max-w-2xl mx-auto">
        <span className="text-[10px] font-bold uppercase tracking-widest text-cyan-400 bg-cyan-950/40 px-3 py-1 rounded-full border border-cyan-800/40">
          Public Transparency Tracker
        </span>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          Track Grievance Resolution
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
          Enter your permanent tracking code (`CVE-...`) to inspect real-time municipal triage, department dispatch, and field resolution milestones.
        </p>
      </div>

      {/* Tracking Code Search Input */}
      <form onSubmit={handleSubmit} className="max-w-xl mx-auto flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="w-5 h-5 text-slate-500 absolute left-3.5 top-3.5" />
          <input
            type="text"
            required
            value={inputCode}
            onChange={(e) => setInputCode(e.target.value.toUpperCase())}
            placeholder="e.g. CVE-20261121-AB89"
            className="w-full pl-11 pr-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-sm placeholder-slate-600 focus:outline-none focus:border-cyan-500 shadow-lg"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition-all shadow-lg shadow-blue-600/30 disabled:opacity-50 flex items-center gap-2"
        >
          <span>{loading ? 'Searching...' : 'Track'}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>

      {error && (
        <div className="max-w-xl mx-auto p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-3">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Result Display */}
      {trackingData && (
        <div className="p-6 sm:p-8 rounded-2xl bg-slate-900 border border-slate-800 space-y-8 shadow-2xl animate-fade-in">
          {/* Card Top */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
            <div>
              <div className="text-[10px] text-slate-400 font-mono">TRACKING CODE</div>
              <div className="text-xl sm:text-2xl font-black font-mono text-emerald-400 tracking-wider">
                {trackingData.tracking_id}
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">
                {trackingData.status.replace('_', ' ')}
              </span>
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                PRIORITY: {trackingData.severity}
              </span>
            </div>
          </div>

          {/* Title & Info */}
          <div className="space-y-1">
            <h2 className="text-lg font-bold text-white">{trackingData.title}</h2>
            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 pt-1">
              <span>Category: <strong className="text-slate-200">{trackingData.category}</strong></span>
              {trackingData.department_name && (
                <span>Dept: <strong className="text-cyan-400">{trackingData.department_name}</strong></span>
              )}
              {trackingData.address && (
                <span className="flex items-center gap-1">
                  <MapPin className="w-3 h-3 text-slate-400" />
                  {trackingData.address}
                </span>
              )}
            </div>
          </div>

          {/* 5-Step Visual Progression Timeline */}
          <div className="space-y-3">
            <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Resolution Progression Timeline
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
              {trackingData.timeline_stages.map((stage: TimelineStage, idx: number) => (
                <div
                  key={stage.key}
                  className={`p-3.5 rounded-xl border text-xs space-y-1.5 transition-all ${
                    stage.completed
                      ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
                      : 'bg-slate-950 border-slate-800 text-slate-500'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-bold">0{idx + 1}</span>
                    {stage.completed ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <Clock className="w-4 h-4 text-slate-600" />
                    )}
                  </div>
                  <div className="font-semibold">{stage.label}</div>
                  <div className="text-[10px]">
                    {stage.completed ? 'Milestone Completed' : 'Pending Step'}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Audit History Log */}
          {trackingData.status_history && trackingData.status_history.length > 0 && (
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-3">
              <div className="text-xs font-semibold text-slate-300">
                Logged Municipal Actions
              </div>
              <div className="space-y-2 text-xs">
                {trackingData.status_history.map((h: StatusHistoryItem, i: number) => (
                  <div key={i} className="flex items-start justify-between border-t border-slate-800/60 pt-2 text-[11px]">
                    <div>
                      <span className="font-bold text-white">{h.new_status.replace('_', ' ')}</span>: {h.notes}
                    </div>
                    <span className="text-slate-500 font-mono text-[10px]">
                      {h.created_at ? new Date(h.created_at).toLocaleDateString() : ''}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Privacy Notice */}
          <div className="p-3 rounded-xl bg-blue-950/30 border border-blue-900/40 text-slate-400 text-[11px] flex items-center gap-2">
            <Shield className="w-4 h-4 text-blue-400 shrink-0" />
            <span>
              <strong>Citizen Privacy Protected:</strong> Private citizen phone numbers and personal contact details are completely scrubbed from public tracking displays.
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
