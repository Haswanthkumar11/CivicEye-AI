import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getComplaints } from '../api/complaints';
import { Complaint, ComplaintStatus } from '../types';
import {
  FileText,
  Plus,
  Search,
  ChevronRight,
  Camera,
  Mic,
  MapPin,
  Shield,
  RefreshCw,
} from 'lucide-react';

export const CitizenDashboard: React.FC = () => {
  const { isAuthenticated, openAuthModal, demoLogin } = useAuth();
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const fetchComplaints = async () => {
    setLoading(true);
    try {
      const data = await getComplaints({ mine: true });
      setComplaints(data);
    } catch {
      // Graceful fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchComplaints();
    } else {
      setLoading(false);
    }
  }, [isAuthenticated]);

  // Statistics
  const totalCount = complaints.length;
  const pendingCount = complaints.filter(
    (c) => c.status === 'SUBMITTED' || c.status === 'UNDER_REVIEW'
  ).length;
  const inProgressCount = complaints.filter(
    (c) => c.status === 'ASSIGNED' || c.status === 'IN_PROGRESS'
  ).length;
  const resolvedCount = complaints.filter((c) => c.status === 'RESOLVED').length;

  // Filtered list
  const filteredComplaints = complaints.filter((c) => {
    const matchesStatus = statusFilter === 'ALL' || c.status === statusFilter;
    const matchesQuery =
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.tracking_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.category.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesQuery;
  });

  const getStatusBadge = (status: ComplaintStatus) => {
    switch (status) {
      case 'SUBMITTED':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'UNDER_REVIEW':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'ASSIGNED':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
      case 'IN_PROGRESS':
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20';
      case 'RESOLVED':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'REJECTED':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
    }
  };

  const getPriorityBadge = (p: string) => {
    switch (p) {
      case 'CRITICAL':
        return 'text-rose-400 bg-rose-500/10';
      case 'HIGH':
        return 'text-amber-400 bg-amber-500/10';
      case 'MEDIUM':
        return 'text-blue-400 bg-blue-500/10';
      default:
        return 'text-emerald-400 bg-emerald-500/10';
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-blue-600/20 text-blue-400">
              <FileText className="w-5 h-5" />
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Citizen Grievance Dashboard
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Track reported civic issues, municipal dispatch status, and field resolution timelines.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchComplaints}
            className="p-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 transition-colors"
            title="Refresh Registry"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <Link
            to="/report"
            className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs flex items-center gap-2 shadow-lg shadow-blue-600/30 transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Report New Issue</span>
          </Link>
        </div>
      </div>

      {/* Guest Warning if not logged in */}
      {!isAuthenticated && (
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 text-center space-y-4">
          <Shield className="w-10 h-10 text-cyan-400 mx-auto" />
          <div className="space-y-1">
            <h3 className="text-base font-bold text-white">Sign In to View Your Grievances</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Please sign in or use the 1-click test persona to load your citizen grievance history.
            </p>
          </div>
          <div className="flex justify-center gap-3">
            <button
              onClick={() => demoLogin('citizen')}
              className="px-4 py-2 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 text-xs font-semibold"
            >
              Log in as Demo Citizen
            </button>
            <button
              onClick={() => openAuthModal('login')}
              className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold"
            >
              Sign In
            </button>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      {isAuthenticated && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
            <div className="text-[11px] text-slate-400 font-medium">Total Reported</div>
            <div className="text-2xl font-black font-mono text-white">{totalCount}</div>
          </div>
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
            <div className="text-[11px] text-slate-400 font-medium">Pending Triage</div>
            <div className="text-2xl font-black font-mono text-amber-400">{pendingCount}</div>
          </div>
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
            <div className="text-[11px] text-slate-400 font-medium">Active in Field</div>
            <div className="text-2xl font-black font-mono text-cyan-400">{inProgressCount}</div>
          </div>
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
            <div className="text-[11px] text-slate-400 font-medium">Resolved</div>
            <div className="text-2xl font-black font-mono text-emerald-400">{resolvedCount}</div>
          </div>
        </div>
      )}

      {/* Filters and Search Bar */}
      {isAuthenticated && (
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/60 p-3 rounded-2xl border border-slate-800">
          {/* Status Tabs */}
          <div className="flex flex-wrap gap-1 text-xs">
            {['ALL', 'SUBMITTED', 'UNDER_REVIEW', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                  statusFilter === st
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                {st.replace('_', ' ')}
              </button>
            ))}
          </div>

          {/* Search box */}
          <div className="relative w-full md:w-72">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search ID, title, or category..."
              className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>
      )}

      {/* Complaints List */}
      {isAuthenticated && (
        <div className="space-y-3">
          {loading ? (
            <div className="p-12 text-center text-xs text-slate-500">
              Loading your grievances registry...
            </div>
          ) : filteredComplaints.length === 0 ? (
            <div className="p-12 rounded-2xl bg-slate-900 border border-slate-800 text-center space-y-3">
              <FileText className="w-10 h-10 text-slate-600 mx-auto" />
              <div className="text-slate-300 font-semibold text-sm">No Grievances Found</div>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                {searchQuery || statusFilter !== 'ALL'
                  ? 'No issues match the selected filter criteria.'
                  : 'You have not submitted any civic complaints yet.'}
              </p>
              <Link
                to="/report"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 text-white text-xs font-semibold shadow"
              >
                <Plus className="w-4 h-4" />
                <span>Submit Your First Report</span>
              </Link>
            </div>
          ) : (
            filteredComplaints.map((c) => (
              <div
                key={c.id}
                className="p-4 sm:p-5 rounded-xl bg-slate-900 hover:bg-slate-850 border border-slate-800 transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 group"
              >
                {/* Left block with details */}
                <div className="space-y-1.5 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs font-bold text-white tracking-wider">
                      {c.tracking_id}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${getStatusBadge(c.status)}`}>
                      {c.status.replace('_', ' ')}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${getPriorityBadge(c.severity)}`}>
                      SCORE: {c.severity_score} ({c.severity})
                    </span>
                  </div>

                  <h3 className="text-sm font-semibold text-white group-hover:text-blue-400 transition-colors">
                    {c.title}
                  </h3>

                  <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-400">
                    <span>Category: <strong className="text-slate-300">{c.category}</strong></span>
                    {c.department_name && (
                      <span>Dept: <strong className="text-slate-300">{c.department_name}</strong></span>
                    )}
                    {c.address && (
                      <span className="flex items-center gap-1 truncate max-w-xs">
                        <MapPin className="w-3 h-3 text-cyan-400" />
                        {c.address}
                      </span>
                    )}
                  </div>
                </div>

                {/* Right block: media icons + action button */}
                <div className="flex items-center gap-4 self-end sm:self-center">
                  <div className="flex items-center gap-2 text-slate-500">
                    {c.media.some((m) => m.media_type === 'IMAGE') && (
                      <span title="Photo attached">
                        <Camera className="w-4 h-4 text-blue-400" />
                      </span>
                    )}
                    {c.media.some((m) => m.media_type === 'AUDIO') && (
                      <span title="Audio note attached">
                        <Mic className="w-4 h-4 text-cyan-400" />
                      </span>
                    )}
                  </div>

                  <Link
                    to={`/complaints/${c.id}`}
                    className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 border border-slate-700 transition-colors"
                  >
                    <span>View Details</span>
                    <ChevronRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};
