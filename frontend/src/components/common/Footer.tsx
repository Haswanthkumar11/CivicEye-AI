import React from 'react';
import { Eye, Shield, Cpu, Lock } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-[#070b14] border-t border-slate-800/80 py-12 text-slate-400 text-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-white">
                <Eye className="w-4 h-4" />
              </div>
              <span className="text-white font-bold tracking-tight">CivicEye AI</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Multimodal AI-powered civic intelligence platform transforming unstructured citizen grievances into prioritized, transparent, and actionable civic resolutions.
            </p>
            <div className="text-[11px] text-slate-500">
              Tagline: <em>Report it. Understand it. Resolve it. Track it.</em>
            </div>
          </div>

          <div>
            <h4 className="text-white font-semibold text-xs tracking-wider uppercase mb-3">Core Modules</h4>
            <ul className="space-y-2 text-xs">
              <li>Citizen Reporting Portal (Multilingual Telugu/English)</li>
              <li>Local YOLO Road Damage Vision Engine</li>
              <li>Local faster-whisper Audio Transcription</li>
              <li>Explainable Priority & Severity Calculator</li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold text-xs tracking-wider uppercase mb-3">Governance Portals</h4>
            <ul className="space-y-2 text-xs">
              <li>Citizen Issue Tracking & Status Timeline</li>
              <li>Administrator Municipal Triage Console</li>
              <li>Spatial Duplicate & Cluster Linking</li>
              <li>Public Transparency & Hotspot Heatmaps</li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold text-xs tracking-wider uppercase mb-3">Compliance & Ethics</h4>
            <ul className="space-y-2 text-xs">
              <li className="flex items-center gap-1.5 text-slate-300">
                <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                100% Free Local CV & Speech Execution
              </li>
              <li className="flex items-center gap-1.5 text-slate-300">
                <Shield className="w-3.5 h-3.5 text-emerald-400" />
                Deterministic Scoring (Non-hallucinated)
              </li>
              <li className="flex items-center gap-1.5 text-slate-300">
                <Lock className="w-3.5 h-3.5 text-blue-400" />
                Citizen Privacy Scrubbed from Public Feeds
              </li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-slate-800/60 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div>
            &copy; 2026 CivicEye AI. Built for Smart Civic Governance & Transparency.
          </div>
          <div className="flex items-center gap-4">
            <span className="font-mono text-[11px] bg-slate-900 px-2.5 py-1 rounded border border-slate-800 text-slate-400">
              FastAPI + React 18 + PostGIS + Gemini + YOLO + Whisper
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
};
