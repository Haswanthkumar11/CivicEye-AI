import React from 'react';
import { Eye, ExternalLink } from 'lucide-react';

interface NavbarProps {
  backendOnline: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ backendOnline }) => {
  return (
    <header className="sticky top-0 z-50 bg-[#0a0f1d]/90 backdrop-blur-md border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
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
        </div>

        {/* Center Nav links */}
        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-300">
          <a href="#portals" className="hover:text-blue-400 transition-colors">Portals</a>
          <a href="#pipeline" className="hover:text-blue-400 transition-colors">AI Pipeline</a>
          <a href="#severity-engine" className="hover:text-blue-400 transition-colors">Priority Engine</a>
          <a href="#architecture" className="hover:text-blue-400 transition-colors">Architecture</a>
          <a href="#diagnostics" className="hover:text-blue-400 transition-colors">Diagnostics</a>
        </nav>

        {/* Right CTA & Status Indicator */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs">
            <span className={`w-2 h-2 rounded-full ${backendOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
            <span className="text-slate-300 font-mono text-[11px]">
              API: {backendOnline ? 'CONNECTED' : 'DISCONNECTED'}
            </span>
          </div>

          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition-colors border border-slate-700"
          >
            <span>API Docs</span>
            <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
          </a>
        </div>
      </div>
    </header>
  );
};
