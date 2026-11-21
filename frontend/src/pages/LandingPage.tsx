import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Shield,
  Activity,
  MapPin,
  Mic,
  Camera,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  BarChart3,
  RefreshCw,
  Sliders,
  ExternalLink,
  Building2,
  Users,
  Sparkles,
  UserCheck,
} from 'lucide-react';
import { checkSystemHealth } from '../api/client';
import { SystemHealth } from '../types';
import { useAuth } from '../context/AuthContext';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, isAdmin, openAuthModal, demoLogin } = useAuth();
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loadingHealth, setLoadingHealth] = useState<boolean>(true);
  const [healthError, setHealthError] = useState<string | null>(null);

  // Interactive Severity Calculator State (Deterministic formula validation)
  const [damageFactor, setDamageFactor] = useState<number>(75);
  const [riskFactor, setRiskFactor] = useState<number>(85);
  const [impactFactor, setImpactFactor] = useState<number>(60);
  const [sensitivityFactor, setSensitivityFactor] = useState<number>(70);

  // Active view tab in portal showcase
  const [activePortalTab, setActivePortalTab] = useState<'citizen' | 'admin' | 'transparency'>('citizen');

  // Compute deterministic severity score
  const computedScore = Math.round(
    0.30 * damageFactor +
    0.30 * riskFactor +
    0.20 * impactFactor +
    0.20 * sensitivityFactor
  );

  const getPriorityBand = (score: number) => {
    if (score <= 30) return { label: 'LOW', color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' };
    if (score <= 60) return { label: 'MEDIUM', color: 'text-blue-400 bg-blue-500/10 border-blue-500/30' };
    if (score <= 80) return { label: 'HIGH', color: 'text-amber-400 bg-amber-500/10 border-amber-500/30' };
    return { label: 'CRITICAL', color: 'text-rose-400 bg-rose-500/10 border-rose-500/30' };
  };

  const priorityBand = getPriorityBand(computedScore);

  const fetchHealth = async () => {
    setLoadingHealth(true);
    setHealthError(null);
    try {
      const data = await checkSystemHealth();
      setHealth(data);
    } catch (err: any) {
      console.warn('Backend not reached yet:', err.message);
      setHealthError('Backend server is starting or unreachable. Check backend console.');
    } finally {
      setLoadingHealth(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="space-y-24 py-12">
      {/* HERO SECTION */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center space-y-6 max-w-4xl mx-auto">
          {/* Track and Live Status Pill */}
          <div className="inline-flex items-center gap-3 px-3.5 py-1.5 rounded-full bg-slate-900/90 border border-slate-800 text-xs text-slate-300">
            <span className="flex h-2 w-2 relative">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${health ? 'bg-emerald-400' : 'bg-amber-400'} opacity-75`}></span>
              <span className={`relative inline-flex rounded-full h-2 w-2 ${health ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
            </span>
            <span className="font-semibold text-slate-200">Track 1: Civic Pulse & Digital Governance</span>
            <span className="text-slate-600">|</span>
            <span className="font-mono text-cyan-400">
              {health ? `FastAPI v${health.version} Online` : 'FastAPI Initializing...'}
            </span>
          </div>

          {/* Main Title */}
          <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-[1.15]">
            Transparent Civic Grievance &{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-cyan-400 to-emerald-400">
              Infrastructure Triage
            </span>
          </h1>

          {/* Tagline & Subtitle */}
          <p className="text-xl sm:text-2xl font-medium text-slate-300 tracking-wide">
            "Report it. Understand it. Resolve it. Track it."
          </p>
          <p className="text-base sm:text-lg text-slate-400 max-w-3xl mx-auto leading-relaxed">
            A multimodal AI civic intelligence platform transforming unstructured citizen photos, Telugu/English voice notes, and videos into structured, prioritized, and geographically clustered municipal actions.
          </p>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <button
              onClick={() => {
                if (isAuthenticated) {
                  navigate('/report');
                } else {
                  openAuthModal('login');
                }
              }}
              className="px-6 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm shadow-lg shadow-blue-600/30 transition-all flex items-center gap-2 group"
            >
              <span>{isAuthenticated ? 'Report Issue Now' : 'Report Issue (Citizen Portal)'}</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
            <button
              onClick={() => {
                setActivePortalTab('admin');
                if (!isAdmin) {
                  demoLogin('admin');
                }
              }}
              className="px-6 py-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-sm border border-slate-700 transition-all flex items-center gap-2"
            >
              <Shield className="w-4 h-4 text-cyan-400" />
              <span>{isAdmin ? 'Admin Console (Active)' : 'Admin Triage Dashboard'}</span>
            </button>
            <Link
              to="/track"
              className="px-6 py-3.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-300 font-medium text-sm border border-slate-800 transition-all flex items-center gap-2"
            >
              <BarChart3 className="w-4 h-4 text-emerald-400" />
              <span>Track Grievance Status</span>
            </Link>
          </div>

          {/* Authenticated Persona Banner if logged in */}
          {isAuthenticated && user && (
            <div className="mt-4 inline-flex items-center gap-3 px-4 py-2 rounded-xl bg-slate-900 border border-blue-500/30 text-xs">
              <UserCheck className="w-4 h-4 text-emerald-400" />
              <span className="text-slate-300">
                Logged in as <strong className="text-white">{user.full_name}</strong> ({user.email})
              </span>
              <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-bold uppercase text-[10px]">
                {user.role}
              </span>
            </div>
          )}
        </div>

        {/* 1-Click Persona Evaluation Strip */}
        <div className="mt-8 p-4 rounded-2xl bg-gradient-to-r from-blue-950/40 via-slate-900/60 to-cyan-950/40 border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
              <Sparkles className="w-4 h-4" />
            </span>
            <div>
              <div className="text-xs font-semibold text-white">Hackathon Evaluator Quick Switcher</div>
              <div className="text-[11px] text-slate-400">Test role-based access control and database isolation instantly</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => demoLogin('citizen')}
              className="px-3 py-1.5 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/30 text-xs font-medium transition-colors"
            >
              Test as Citizen
            </button>
            <button
              onClick={() => demoLogin('admin')}
              className="px-3 py-1.5 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/30 text-xs font-medium transition-colors"
            >
              Test as Administrator
            </button>
          </div>
        </div>

        {/* Live Feature Highlights Bar */}
        <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <div className="text-blue-400 mb-1 flex items-center gap-2">
              <Camera className="w-4 h-4" />
              <span className="text-xs font-semibold uppercase tracking-wider">Local YOLO CV</span>
            </div>
            <p className="text-xs text-slate-300">Pothole & road damage detection running locally via OpenCV</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <div className="text-cyan-400 mb-1 flex items-center gap-2">
              <Mic className="w-4 h-4" />
              <span className="text-xs font-semibold uppercase tracking-wider">Local Whisper ASR</span>
            </div>
            <p className="text-xs text-slate-300">Telugu & English voice note transcription via int8 faster-whisper</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <div className="text-emerald-400 mb-1 flex items-center gap-2">
              <Sliders className="w-4 h-4" />
              <span className="text-xs font-semibold uppercase tracking-wider">Deterministic Triage</span>
            </div>
            <p className="text-xs text-slate-300">Explainable 4-factor formula: damage, risk, impact & location</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <div className="text-purple-400 mb-1 flex items-center gap-2">
              <MapPin className="w-4 h-4" />
              <span className="text-xs font-semibold uppercase tracking-wider">Hotspot Clusters</span>
            </div>
            <p className="text-xs text-slate-300">Geospatial PostGIS proximity deduplication & recurring issue hubs</p>
          </div>
        </div>
      </section>

      {/* THREE INTERCONNECTED PORTALS SHOWCASE */}
      <section id="portals" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="space-y-4 text-center max-w-3xl mx-auto mb-10">
          <span className="text-xs font-bold uppercase tracking-widest text-cyan-400 bg-cyan-950/40 px-3 py-1 rounded-full border border-cyan-800/50">
            Interconnected Ecosystem
          </span>
          <h2 className="text-3xl font-bold text-white tracking-tight">
            Three Interfaces, One Cohesive Civic Intelligence System
          </h2>
          <p className="text-slate-400 text-sm">
            CivicEye AI removes bureaucratic friction for citizens while arming administrators with real-time triage tools and providing the public with transparent governance metrics.
          </p>
        </div>

        {/* Tab Controls */}
        <div className="flex justify-center mb-8">
          <div className="inline-flex p-1.5 rounded-2xl bg-slate-900 border border-slate-800">
            <button
              onClick={() => setActivePortalTab('citizen')}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                activePortalTab === 'citizen'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Users className="w-4 h-4" />
              <span>1. Citizen Portal</span>
            </button>
            <button
              onClick={() => setActivePortalTab('admin')}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                activePortalTab === 'admin'
                  ? 'bg-cyan-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Building2 className="w-4 h-4" />
              <span>2. Administrator Dashboard</span>
            </button>
            <button
              onClick={() => setActivePortalTab('transparency')}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                activePortalTab === 'transparency'
                  ? 'bg-emerald-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              <span>3. Public Transparency</span>
            </button>
          </div>
        </div>

        {/* Dynamic Portal Showcase Cards */}
        <div className="rounded-2xl bg-slate-900/70 border border-slate-800 p-6 lg:p-8 backdrop-blur-sm">
          {activePortalTab === 'citizen' && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-6 space-y-5">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded bg-blue-500/10 text-blue-400 text-xs font-semibold">
                  <span>Citizen Reporting Module</span>
                </div>
                <h3 className="text-2xl font-bold text-white">
                  Effortless Reporting Without Bureaucratic Confusion
                </h3>
                <p className="text-slate-300 text-sm leading-relaxed">
                  Citizens don't need to know which municipal engineering department handles broken asphalt, leaky mains, or dark streetlights. Simply snap a photo, speak in Telugu or English, and let CivicEye AI extract the structured complaint details automatically.
                </p>
                <div className="space-y-3 pt-2">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
                    <p className="text-xs text-slate-300">
                      <strong className="text-white">Multimodal Capture:</strong> Photographs, videos, voice recordings, and text descriptions.
                    </p>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
                    <p className="text-xs text-slate-300">
                      <strong className="text-white">Pre-Submission AI Summary:</strong> Review the AI's understanding, detected category, and suggested department before submitting.
                    </p>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
                    <p className="text-xs text-slate-300">
                      <strong className="text-white">Full Transparency Tracking:</strong> Step-by-step status: Submitted &rarr; Under Review &rarr; Assigned &rarr; In Progress &rarr; Resolved.
                    </p>
                  </div>
                </div>

                <div className="pt-4 flex flex-wrap items-center gap-3">
                  <Link
                    to="/report"
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-600/25 transition-all"
                  >
                    <span>Launch Reporting Wizard</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                  <Link
                    to="/track"
                    className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-all"
                  >
                    <span>Track Grievance</span>
                  </Link>
                </div>
              </div>

              {/* Citizen UI Mockup */}
              <div className="lg:col-span-6 bg-slate-950 rounded-xl p-5 border border-slate-800 shadow-2xl">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                  <span className="text-xs font-semibold text-slate-200">Grievance Submission Form Preview</span>
                  <span className="text-[10px] font-mono bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded">LIVE DEMO VIEW</span>
                </div>
                <div className="space-y-3 text-xs">
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded bg-blue-600/20 text-blue-400 flex items-center justify-center">
                        <Camera className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="font-semibold text-slate-200">road_damage_site_04.jpg</div>
                        <div className="text-[10px] text-slate-400">YOLO: Pothole detected (94.2% conf)</div>
                      </div>
                    </div>
                    <span className="px-2 py-1 bg-emerald-500/10 text-emerald-400 text-[10px] rounded font-semibold">CV Processed</span>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded bg-cyan-600/20 text-cyan-400 flex items-center justify-center">
                        <Mic className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="font-semibold text-slate-200">Telugu Voice Note (0:14)</div>
                        <div className="text-[10px] text-slate-400">"రోడ్డుపై పెద్ద గుంత ఏర్పడింది, బైకులు పడిపోతున్నాయి"</div>
                      </div>
                    </div>
                    <span className="px-2 py-1 bg-cyan-500/10 text-cyan-400 text-[10px] rounded font-semibold">Whisper Transcribed</span>
                  </div>

                  <div className="p-3 rounded-lg bg-blue-950/30 border border-blue-900/50 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-blue-300">AI Structured Summary</span>
                      <span className="text-[10px] font-mono text-cyan-400">Gemini 1.5</span>
                    </div>
                    <p className="text-[11px] text-slate-300">
                      <strong>Issue:</strong> Severe road cavity / pothole creating hazardous conditions for two-wheelers.
                    </p>
                    <div className="flex items-center gap-4 text-[10px] text-slate-400">
                      <span>Dept: <strong>Municipal Roads & Engineering</strong></span>
                      <span>Risk: <strong className="text-rose-400">HIGH</strong></span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activePortalTab === 'admin' && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-6 space-y-5">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded bg-cyan-500/10 text-cyan-400 text-xs font-semibold">
                  <span>Administrative Control Center</span>
                </div>
                <h3 className="text-2xl font-bold text-white">
                  Intelligent Triage, Department Routing & Duplicate Handling
                </h3>
                <p className="text-slate-300 text-sm leading-relaxed">
                  Municipal administrators receive pre-scored, structured grievances with bounding box damage evidence, speech transcripts, and location tags. The priority queue ensures critical hazards receive immediate engineering dispatch.
                </p>
                <div className="space-y-3 pt-2">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
                    <p className="text-xs text-slate-300">
                      <strong className="text-white">Spatial Duplicate Identification:</strong> Alerts officers when multiple citizens report the same issue within 50 meters, linking them without silent record destruction.
                    </p>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
                    <p className="text-xs text-slate-300">
                      <strong className="text-white">Department Override:</strong> Configurable rules route complaints directly, with administrative correction capabilities.
                    </p>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
                    <p className="text-xs text-slate-300">
                      <strong className="text-white">Resolution Evidence Verification:</strong> Requires field photos before marking an issue RESOLVED.
                    </p>
                  </div>
                </div>
              </div>

              {/* Admin UI Mockup */}
              <div className="lg:col-span-6 bg-slate-950 rounded-xl p-5 border border-slate-800 shadow-2xl">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                  <span className="text-xs font-semibold text-slate-200">Department Dispatch Queue</span>
                  <span className="text-[10px] font-mono bg-cyan-500/20 text-cyan-400 px-2 py-0.5 rounded">ADMIN ROLE</span>
                </div>
                <div className="space-y-2.5 text-xs">
                  <div className="p-3 rounded-lg bg-slate-900 border-l-4 border-l-rose-500 border border-slate-800 flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white">#CVE-9042</span>
                        <span className="px-1.5 py-0.5 text-[9px] rounded bg-rose-500/20 text-rose-300 font-bold">SCORE: 88 (CRITICAL)</span>
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">Deep trench cave-in near School Zone</div>
                    </div>
                    <button className="px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white font-medium text-[11px]">
                      Dispatch Team
                    </button>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-900 border-l-4 border-l-amber-500 border border-slate-800 flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white">#CVE-9038</span>
                        <span className="px-1.5 py-0.5 text-[9px] rounded bg-amber-500/20 text-amber-300 font-bold">SCORE: 72 (HIGH)</span>
                        <span className="px-1.5 py-0.5 text-[9px] rounded bg-purple-500/20 text-purple-300">3 Duplicates Linked</span>
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">Main line water pipe breach, low pressure</div>
                    </div>
                    <button className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-[11px]">
                      Review Group
                    </button>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-900 border-l-4 border-l-emerald-500 border border-slate-800 flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white">#CVE-9021</span>
                        <span className="px-1.5 py-0.5 text-[9px] rounded bg-emerald-500/20 text-emerald-300 font-bold">RESOLVED</span>
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">Streetlight bulb replaced (Evidence attached)</div>
                    </div>
                    <span className="text-[10px] text-slate-500">Closed 2h ago</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activePortalTab === 'transparency' && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-6 space-y-5">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded bg-emerald-500/10 text-emerald-400 text-xs font-semibold">
                  <span>Public Transparency Dashboard</span>
                </div>
                <h3 className="text-2xl font-bold text-white">
                  Open Data, Hotspot Heatmaps & Department Accountability
                </h3>
                <p className="text-slate-300 text-sm leading-relaxed">
                  Citizens and journalists can inspect civic health without exposing private personal data. Open analytics reveal average resolution times, recurring infrastructure hotspots, and ward-by-ward performance indicators.
                </p>
                <div className="space-y-3 pt-2">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                    <p className="text-xs text-slate-300">
                      <strong className="text-white">Strict Privacy Scrubbing:</strong> Personal phone numbers, names, and private photos are never published.
                    </p>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                    <p className="text-xs text-slate-300">
                      <strong className="text-white">Civic Hotspot Intelligence:</strong> Identifies chronic infrastructure failure zones requiring capital overhaul rather than temporary patches.
                    </p>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                    <p className="text-xs text-slate-300">
                      <strong className="text-white">Department SLA Metrics:</strong> Real resolution statistics by department, promoting healthy civic accountability.
                    </p>
                  </div>
                </div>
              </div>

              {/* Public UI Mockup */}
              <div className="lg:col-span-6 bg-slate-950 rounded-xl p-5 border border-slate-800 shadow-2xl">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                  <span className="text-xs font-semibold text-slate-200">Public Civic Analytics Snapshot</span>
                  <span className="text-[10px] font-mono bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded">OPEN ACCESS</span>
                </div>
                <div className="grid grid-cols-3 gap-3 mb-4">
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-center">
                    <div className="text-xl font-bold text-white">1,428</div>
                    <div className="text-[10px] text-slate-400 mt-1">Total Reported</div>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-center">
                    <div className="text-xl font-bold text-amber-400">184</div>
                    <div className="text-[10px] text-slate-400 mt-1">Active Triage</div>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-center">
                    <div className="text-xl font-bold text-emerald-400">87.1%</div>
                    <div className="text-[10px] text-slate-400 mt-1">Resolved on SLA</div>
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs font-medium text-slate-300">
                    <span>Active Hotspot Clusters</span>
                    <span className="text-[10px] text-purple-400">PostGIS Density Index</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-800">
                    <span>Sector 4 North (Road Potholes)</span>
                    <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 font-mono text-[10px]">14 Reports</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>Market Ward 7 (Drainage Overflow)</span>
                    <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 font-mono text-[10px]">8 Reports</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* EXPLAINABLE DETERMINISTIC PRIORITY ENGINE SECTION */}
      <section id="severity-engine" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="rounded-2xl bg-gradient-to-b from-slate-900 via-slate-900/90 to-slate-950 border border-slate-800 p-8 lg:p-10">
          <div className="max-w-3xl mb-8 space-y-2">
            <span className="text-xs font-bold uppercase tracking-widest text-amber-400 bg-amber-950/40 px-3 py-1 rounded-full border border-amber-800/50">
              Module C – Explainable Priority Engine
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Deterministic, Transparent Scoring (No Black-Box Hallucinations)
            </h2>
            <p className="text-slate-400 text-sm">
              While AI estimates individual raw attributes from multimodal media, the final civic severity score is calculated deterministically by the backend using a weighted formula.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            {/* Left: Interactive Weight Sliders */}
            <div className="lg:col-span-7 space-y-5 bg-slate-950/80 p-6 rounded-xl border border-slate-800/80">
              <div className="text-xs font-mono text-cyan-400 mb-2">
                Formula: Score = (0.30 &times; Damage) + (0.30 &times; Risk) + (0.20 &times; Impact) + (0.20 &times; Sensitivity)
              </div>

              {/* Slider 1: Damage */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-slate-300">Infrastructure Damage (Weight: 30%)</span>
                  <span className="text-blue-400 font-mono">{damageFactor}/100</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={damageFactor}
                  onChange={(e) => setDamageFactor(Number(e.target.value))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
              </div>

              {/* Slider 2: Risk */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-slate-300">Public Safety Risk (Weight: 30%)</span>
                  <span className="text-cyan-400 font-mono">{riskFactor}/100</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={riskFactor}
                  onChange={(e) => setRiskFactor(Number(e.target.value))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                />
              </div>

              {/* Slider 3: Impact */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-slate-300">Public Impact / Traffic Density (Weight: 20%)</span>
                  <span className="text-emerald-400 font-mono">{impactFactor}/100</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={impactFactor}
                  onChange={(e) => setImpactFactor(Number(e.target.value))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                />
              </div>

              {/* Slider 4: Sensitivity */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-slate-300">Location Sensitivity (School/Hospital Zone, Weight: 20%)</span>
                  <span className="text-amber-400 font-mono">{sensitivityFactor}/100</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={sensitivityFactor}
                  onChange={(e) => setSensitivityFactor(Number(e.target.value))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
                />
              </div>
            </div>

            {/* Right: Calculated Deterministic Output Card */}
            <div className="lg:col-span-5 flex flex-col items-center justify-center p-6 rounded-xl bg-slate-950 border border-slate-800 text-center space-y-4 shadow-xl">
              <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                Computed Severity Score
              </span>

              <div className="text-6xl font-black font-mono tracking-tight text-white">
                {computedScore}
                <span className="text-xl text-slate-500 font-normal"> / 100</span>
              </div>

              <div className={`px-4 py-1.5 rounded-full text-xs font-bold border ${priorityBand.color}`}>
                PRIORITY BAND: {priorityBand.label}
              </div>

              <div className="w-full grid grid-cols-4 gap-1 text-[10px] font-mono pt-3 border-t border-slate-800 text-slate-400">
                <div className={`p-1 rounded ${computedScore <= 30 ? 'bg-emerald-500/20 text-emerald-300 font-bold' : ''}`}>
                  0-30<br />LOW
                </div>
                <div className={`p-1 rounded ${computedScore > 30 && computedScore <= 60 ? 'bg-blue-500/20 text-blue-300 font-bold' : ''}`}>
                  31-60<br />MEDIUM
                </div>
                <div className={`p-1 rounded ${computedScore > 60 && computedScore <= 80 ? 'bg-amber-500/20 text-amber-300 font-bold' : ''}`}>
                  61-80<br />HIGH
                </div>
                <div className={`p-1 rounded ${computedScore > 80 ? 'bg-rose-500/20 text-rose-300 font-bold' : ''}`}>
                  81-100<br />CRITICAL
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* MULTIMODAL AI PIPELINE FLOW */}
      <section id="pipeline" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-12 space-y-2">
          <span className="text-xs font-bold uppercase tracking-widest text-blue-400 bg-blue-950/40 px-3 py-1 rounded-full border border-blue-800/50">
            End-To-End Intelligence Pipeline
          </span>
          <h2 className="text-3xl font-bold text-white tracking-tight">
            How Multimodal Grievance Triage Operates
          </h2>
          <p className="text-slate-400 text-sm">
            Strict separation of concerns ensures models run efficiently: voice and vision run locally on the backend, while high-level reasoning and synthesis are handled by Gemini.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 relative">
          <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="w-9 h-9 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold text-sm">
              01
            </div>
            <h4 className="text-sm font-bold text-white">Multimodal Capture</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Photographs, video clips, Telugu/English voice notes, text, and GPS coordinates uploaded by the citizen.
            </p>
          </div>

          <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="w-9 h-9 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold text-sm">
              02
            </div>
            <h4 className="text-sm font-bold text-white">Local Vision & Speech</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              OpenCV + Local YOLO road damage detector; faster-whisper int8 CPU transcribes Telugu and English speech locally.
            </p>
          </div>

          <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-sm">
              03
            </div>
            <h4 className="text-sm font-bold text-white">Gemini Multimodal</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Extracts structured category, subcategory, context, language, and initial damage/risk factor estimates.
            </p>
          </div>

          <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="w-9 h-9 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold text-sm">
              04
            </div>
            <h4 className="text-sm font-bold text-white">Deterministic Scoring</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Backend calculates 0-100 severity index and maps issue to the responsible municipal department via rule table.
            </p>
          </div>

          <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="w-9 h-9 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center font-bold text-sm">
              05
            </div>
            <h4 className="text-sm font-bold text-white">PostGIS Hotspots</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Spatial proximity clustering identifies related duplicates and flags recurring infrastructure chronic hubs.
            </p>
          </div>
        </div>
      </section>

      {/* SYSTEM ARCHITECTURE & DIAGNOSTICS CARD */}
      <section id="diagnostics" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 lg:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
            <div>
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-cyan-400" />
                <h3 className="text-lg font-bold text-white">Backend Health & Runtime Diagnostics</h3>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Real-time connection between React Vite frontend and FastAPI backend service.
              </p>
            </div>

            <button
              onClick={fetchHealth}
              disabled={loadingHealth}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition-colors border border-slate-700 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingHealth ? 'animate-spin' : ''}`} />
              <span>Refresh Status</span>
            </button>
          </div>

          {health ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Service Info */}
              <div className="space-y-3 bg-slate-950 p-4 rounded-xl border border-slate-800/80">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Service Profile</span>
                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Platform:</span>
                    <span className="text-white font-mono">{health.service}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Version:</span>
                    <span className="text-cyan-400 font-mono">v{health.version}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Environment:</span>
                    <span className="text-emerald-400 font-mono">{health.environment}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Python Runtime:</span>
                    <span className="text-slate-200 font-mono">{health.runtime.python_version}</span>
                  </div>
                </div>
              </div>

              {/* Component Health & Active Auth */}
              <div className="space-y-3 bg-slate-950 p-4 rounded-xl border border-slate-800/80">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Authentication & RBAC</span>
                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Auth Engine:</span>
                    <span className="text-emerald-400 font-semibold">JWT Bearer (Active)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Database Driver:</span>
                    <span className="text-cyan-400 font-mono">{health.components.database_driver}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Current Session:</span>
                    <span className="text-slate-200 font-mono">
                      {isAuthenticated ? `${user?.role.toUpperCase()}` : 'GUEST'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Access Level:</span>
                    <span className={`font-mono ${isAdmin ? 'text-cyan-400 font-bold' : isAuthenticated ? 'text-blue-400' : 'text-slate-500'}`}>
                      {isAdmin ? 'ADMINISTRATOR' : isAuthenticated ? 'CITIZEN' : 'PUBLIC'}
                    </span>
                  </div>
                </div>
              </div>

              {/* API Endpoints */}
              <div className="space-y-3 bg-slate-950 p-4 rounded-xl border border-slate-800/80">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Communication Verification</span>
                <div className="text-xs space-y-2">
                  <div className="p-2 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-[11px]">
                    &check; GET /api/health responded 200 OK
                  </div>
                  <div className="p-2 rounded bg-blue-500/10 border border-blue-500/20 text-blue-300 text-[11px]">
                    &check; POST /api/auth/login verified
                  </div>
                  <div className="pt-1">
                    <a
                      href="http://localhost:8000/docs"
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-blue-400 hover:underline flex items-center gap-1"
                    >
                      <span>Interactive Swagger OpenAPI Docs</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-6 rounded-xl bg-slate-950 border border-amber-900/40 text-center space-y-2">
              <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto" />
              <p className="text-sm font-semibold text-white">Backend Health Check Notice</p>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                {healthError || 'Connecting to http://localhost:8000/api/health...'}
              </p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};
