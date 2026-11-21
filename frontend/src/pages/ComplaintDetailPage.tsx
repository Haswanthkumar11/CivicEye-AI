import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getComplaintById } from '../api/complaints';
import { Complaint, ComplaintMediaItem, StatusHistoryItem } from '../types';
import L from 'leaflet';
import {
  ArrowLeft,
  MapPin,
  Camera,
  Mic,
  Clock,
  CheckCircle2,
  AlertCircle,
  Share2,
} from 'lucide-react';

export const ComplaintDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [complaint, setComplaint] = useState<Complaint | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDetail = async () => {
      if (!id) return;
      setLoading(true);
      setError(null);
      try {
        const data = await getComplaintById(id);
        setComplaint(data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load complaint details.');
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [id]);

  // Leaflet map setup for coordinates display
  const mapContainerRef = React.useRef<HTMLDivElement>(null);
  const mapInstanceRef = React.useRef<L.Map | null>(null);

  useEffect(() => {
    if (!complaint || !mapContainerRef.current) return;
    const lat = complaint.latitude || 17.3850;
    const lng = complaint.longitude || 78.4867;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current).setView([lat, lng], 15);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
      }).addTo(map);

      const customIcon = L.divIcon({
        className: 'custom-leaflet-marker',
        html: `
          <div style="background: #ef4444; color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border: 2px solid white; box-shadow: 0 4px 8px rgba(0,0,0,0.5);">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 28],
      });

      L.marker([lat, lng], { icon: customIcon }).addTo(map);
      mapInstanceRef.current = map;
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [complaint]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center text-xs text-slate-500">
        Loading complaint records...
      </div>
    );
  }

  if (error || !complaint) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-500 mx-auto" />
        <h2 className="text-lg font-bold text-white">Grievance Not Found</h2>
        <p className="text-xs text-slate-400">{error || 'This record does not exist or you do not have permission to view it.'}</p>
        <Link to="/dashboard" className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 text-xs text-white">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to My Dashboard</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Top Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </Link>

        <Link
          to={`/track/${complaint.tracking_id}`}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 border border-blue-500/20 text-xs font-semibold transition-colors"
        >
          <Share2 className="w-3.5 h-3.5" />
          <span>Public Transparency Link</span>
        </Link>
      </div>

      {/* Main Header Card */}
      <div className="p-6 sm:p-8 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <div className="text-[11px] text-slate-400 font-mono">TRACKING IDENTIFIER</div>
            <div className="text-xl sm:text-2xl font-black font-mono text-white tracking-wider">
              {complaint.tracking_id}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">
              {complaint.status.replace('_', ' ')}
            </span>
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
              SEVERITY: {complaint.severity_score} ({complaint.severity})
            </span>
          </div>
        </div>

        <div className="space-y-2">
          <h1 className="text-xl font-bold text-white leading-snug">{complaint.title}</h1>
          <p className="text-slate-300 text-xs leading-relaxed whitespace-pre-wrap">
            {complaint.description}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-xs">
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
            <div className="text-slate-400 text-[10px] uppercase font-semibold">Category</div>
            <div className="text-white font-semibold">{complaint.category}</div>
            {complaint.subcategory && <div className="text-[11px] text-slate-500">{complaint.subcategory}</div>}
          </div>

          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
            <div className="text-slate-400 text-[10px] uppercase font-semibold">Assigned Department</div>
            <div className="text-cyan-400 font-semibold">{complaint.department_name || 'Municipal Roads & Infrastructure'}</div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
            <div className="text-slate-400 text-[10px] uppercase font-semibold">Submission Date</div>
            <div className="text-slate-200">
              {complaint.created_at ? new Date(complaint.created_at).toLocaleString() : 'Recent'}
            </div>
          </div>
        </div>
      </div>

      {/* Media Evidence Gallery */}
      {complaint.media && complaint.media.length > 0 && (
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center gap-2">
            <Camera className="w-4 h-4 text-blue-400" />
            <h3 className="text-sm font-bold text-white">Attached Media Evidence ({complaint.media.length})</h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {complaint.media.map((m: ComplaintMediaItem, idx: number) => (
              <div key={idx} className="rounded-xl overflow-hidden border border-slate-800 bg-slate-950 shadow-md">
                {m.media_type === 'IMAGE' && (
                  <a href={m.file_url} target="_blank" rel="noreferrer">
                    <img src={m.file_url} alt="Evidence" className="h-44 w-full object-cover hover:scale-105 transition-transform" />
                  </a>
                )}
                {m.media_type === 'AUDIO' && (
                  <div className="p-4 space-y-2">
                    <div className="flex items-center gap-2 text-xs font-semibold text-cyan-400">
                      <Mic className="w-4 h-4" />
                      <span>Voice Recording</span>
                    </div>
                    <audio controls src={m.file_url} className="w-full h-8" />
                  </div>
                )}
                {m.media_type === 'VIDEO' && (
                  <video controls src={m.file_url} className="h-44 w-full object-cover" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Incident Location Map */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white">Incident Geographic Location</h3>
          </div>
          {complaint.latitude && complaint.longitude && (
            <span className="font-mono text-xs text-slate-400">
              {complaint.latitude.toFixed(5)}, {complaint.longitude.toFixed(5)}
            </span>
          )}
        </div>

        {complaint.address && (
          <p className="text-xs text-slate-300 font-medium">{complaint.address}</p>
        )}

        <div className="rounded-xl overflow-hidden border border-slate-800">
          <div ref={mapContainerRef} className="h-56 w-full" />
        </div>
      </div>

      {/* Status History Audit Trail */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-bold text-white">Status Timeline & Audit Trail</h3>
        </div>

        <div className="space-y-3">
          {complaint.status_history && complaint.status_history.length > 0 ? (
            complaint.status_history.map((hist: StatusHistoryItem, idx: number) => (
              <div key={idx} className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 flex items-start gap-3">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <div className="space-y-0.5 text-xs flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white">
                      Status transitioned to {hist.new_status.replace('_', ' ')}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {hist.created_at ? new Date(hist.created_at).toLocaleTimeString() : ''}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400">{hist.notes}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-xs text-slate-500">Initial grievance logged.</div>
          )}
        </div>
      </div>
    </div>
  );
};
