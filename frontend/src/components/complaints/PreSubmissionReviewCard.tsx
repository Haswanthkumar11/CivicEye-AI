import React from 'react';
import { Sparkles, Building2, ShieldAlert, MapPin, CheckCircle2 } from 'lucide-react';
import { ComplaintCategory, PriorityLevel, ComplaintMediaItem } from '../../types';

interface PreSubmissionReviewCardProps {
  title: string;
  description: string;
  category: ComplaintCategory;
  severity: PriorityLevel;
  severityScore: number;
  departmentName: string;
  address?: string;
  mediaList: ComplaintMediaItem[];
}

export const PreSubmissionReviewCard: React.FC<PreSubmissionReviewCardProps> = ({
  title,
  description,
  category,
  severity,
  severityScore,
  departmentName,
  address,
  mediaList,
}) => {
  const getBadgeStyle = (p: PriorityLevel) => {
    switch (p) {
      case 'CRITICAL':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
      case 'HIGH':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case 'MEDIUM':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/40';
      default:
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
    }
  };

  return (
    <div className="rounded-2xl bg-gradient-to-br from-slate-900 to-slate-950 border border-blue-500/30 p-6 space-y-5 shadow-2xl relative overflow-hidden">
      <div className="absolute top-0 right-0 transform translate-x-4 -translate-y-4 w-32 h-32 bg-blue-500/10 rounded-full blur-2xl pointer-events-none" />

      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <span className="p-1.5 rounded-lg bg-blue-600/20 text-blue-400">
            <Sparkles className="w-4 h-4" />
          </span>
          <h4 className="text-sm font-bold text-white tracking-tight">
            AI Pre-Submission Triage Summary
          </h4>
        </div>
        <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/40">
          PRE-DISPATCH AUDIT
        </span>
      </div>

      <div className="space-y-3 text-xs">
        {/* Title & Description preview */}
        <div>
          <span className="text-slate-400 font-medium">Issue Title:</span>
          <div className="text-white font-semibold text-sm mt-0.5">{title || 'Untitled Grievance'}</div>
        </div>

        <div>
          <span className="text-slate-400 font-medium">Description:</span>
          <p className="text-slate-300 text-xs mt-0.5 line-clamp-3 leading-relaxed">
            {description || 'No description provided.'}
          </p>
        </div>

        {/* 2x2 Metadata Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
          {/* Category & Department */}
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
            <div className="flex items-center gap-1.5 text-blue-400 font-semibold text-[11px]">
              <Building2 className="w-3.5 h-3.5" />
              <span>Assigned Municipal Dept</span>
            </div>
            <div className="text-white font-bold">{departmentName}</div>
            <div className="text-[11px] text-slate-400 font-mono">Category: {category}</div>
          </div>

          {/* Priority & Severity Score */}
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-amber-400 font-semibold text-[11px]">
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>Deterministic Severity</span>
              </div>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${getBadgeStyle(severity)}`}>
                {severity}
              </span>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-lg font-black font-mono text-white">{severityScore}</span>
              <span className="text-slate-500 text-[10px]">/ 100</span>
              <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden ml-2">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 via-amber-500 to-rose-500"
                  style={{ width: `${Math.min(severityScore, 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Location & Media summary */}
        <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-slate-300">
            <MapPin className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
            <span className="truncate max-w-[320px]">{address || 'Location coordinates selected'}</span>
          </div>
          <div className="text-[11px] text-slate-400 flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
              {mediaList.length} Media Attachment(s)
            </span>
          </div>
        </div>

        <div className="p-2.5 rounded-xl bg-blue-950/20 border border-blue-900/30 text-slate-400 text-[11px] flex items-start gap-2">
          <CheckCircle2 className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
          <span>
            Upon submission, this issue will be assigned a permanent tracking code (`CVE-...`) and routed to the municipal dispatch queue with live transparency tracking.
          </span>
        </div>
      </div>
    </div>
  );
};
