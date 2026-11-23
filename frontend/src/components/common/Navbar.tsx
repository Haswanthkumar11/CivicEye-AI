import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Eye, ExternalLink, User as UserIcon, LogOut, Shield, Sparkles, Plus, Search, FileText } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { getDocsUrl } from '../../api/client';

interface NavbarProps {
  backendOnline: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ backendOnline }) => {
  const { user, isAuthenticated, isAdmin, logout, openAuthModal } = useAuth();
  const location = useLocation();

  const isHome = location.pathname === '/';

  return (
    <header className="sticky top-0 z-40 bg-[#0a0f1d]/90 backdrop-blur-md border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform">
            <Eye className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-white tracking-tight">CivicEye AI</span>
              <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                Track 1
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              Transparent Civic Grievance & Infrastructure Triage System
            </p>
          </div>
        </Link>

        {/* Center Nav links */}
        <nav className="hidden md:flex items-center gap-5 text-xs font-semibold text-slate-300">
          <Link
            to="/report"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-colors ${
              location.pathname === '/report' ? 'bg-blue-600 text-white' : 'hover:text-blue-400'
            }`}
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Report Issue</span>
          </Link>

          <Link
            to="/dashboard"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-colors ${
              location.pathname === '/dashboard' ? 'bg-blue-600 text-white' : 'hover:text-blue-400'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>My Grievances</span>
          </Link>

          <Link
            to="/track"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-colors ${
              location.pathname.startsWith('/track') ? 'bg-blue-600 text-white' : 'hover:text-blue-400'
            }`}
          >
            <Search className="w-3.5 h-3.5" />
            <span>Track Status</span>
          </Link>

          {isHome ? (
            <>
              <a href="#pipeline" className="hover:text-blue-400 transition-colors">AI Pipeline</a>
              <a href="#severity-engine" className="hover:text-blue-400 transition-colors">Priority Engine</a>
            </>
          ) : (
            <Link to="/" className="hover:text-blue-400 transition-colors">Overview</Link>
          )}
        </nav>

        {/* Right Auth / Status Indicator */}
        <div className="flex items-center gap-3">
          {/* Health status pill */}
          <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs">
            <span className={`w-2 h-2 rounded-full ${backendOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
            <span className="text-slate-300 font-mono text-[11px]">
              API: {backendOnline ? 'ACTIVE' : 'OFFLINE'}
            </span>
          </div>

          {/* User Auth Section */}
          {isAuthenticated && user ? (
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                <span className={`p-1 rounded-md ${isAdmin ? 'bg-cyan-500/20 text-cyan-400' : 'bg-blue-500/20 text-blue-400'}`}>
                  {isAdmin ? <Shield className="w-3.5 h-3.5" /> : <UserIcon className="w-3.5 h-3.5" />}
                </span>
                <span className="text-slate-200 font-medium truncate max-w-[120px] sm:max-w-[150px]">
                  {user.full_name}
                </span>
                <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${
                  isAdmin ? 'bg-cyan-900/40 text-cyan-300' : 'bg-blue-900/40 text-blue-300'
                }`}>
                  {user.role}
                </span>
              </div>

              <button
                onClick={logout}
                title="Log out"
                className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-rose-400 transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={() => openAuthModal('demo')}
                className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-950/60 hover:bg-emerald-900/60 border border-emerald-800/60 text-emerald-300 text-xs font-semibold transition-all"
              >
                <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                <span>1-Click Demo</span>
              </button>

              <button
                onClick={() => openAuthModal('login')}
                className="px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md shadow-blue-600/20 transition-all flex items-center gap-1.5"
              >
                <UserIcon className="w-3.5 h-3.5" />
                <span>Sign In</span>
              </button>
            </div>
          )}

          {/* API Docs Link */}
          <a
            href={getDocsUrl()}
            target="_blank"
            rel="noreferrer"
            className="hidden xl:inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors border border-slate-800"
          >
            <span>Docs</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>
    </header>
  );
};
