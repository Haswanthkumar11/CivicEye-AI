import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { createComplaint } from '../api/complaints';
import { MediaUploader } from '../components/complaints/MediaUploader';
import { VoiceRecorder } from '../components/complaints/VoiceRecorder';
import { LocationPicker } from '../components/complaints/LocationPicker';
import { PreSubmissionReviewCard } from '../components/complaints/PreSubmissionReviewCard';
import { ComplaintCategory, PriorityLevel, ComplaintMediaItem, ComplaintLocation } from '../types';
import {
  FileText,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  Copy,
  ExternalLink,
  Shield,
  Sliders,
} from 'lucide-react';

const CATEGORIES: { label: ComplaintCategory; dept: string; subcategories: string[] }[] = [
  {
    label: 'Road Infrastructure',
    dept: 'Municipal Roads & Infrastructure',
    subcategories: ['Pothole / Road Cavity', 'Asphalt Cracks', 'Manhole Cave-in', 'Damaged Divider', 'Missing Guardrail'],
  },
  {
    label: 'Water Supply',
    dept: 'Water Supply & Sewerage Board',
    subcategories: ['Pipe Leak / Burst', 'Contaminated Water', 'No Water Supply', 'Low Pressure', 'Broken Valve'],
  },
  {
    label: 'Sanitation',
    dept: 'Solid Waste Management & Sanitation',
    subcategories: ['Garbage Pileup', 'Open Waste Burning', 'Dead Animal Carcass', 'Overflowing Dustbin', 'Debris Dumping'],
  },
  {
    label: 'Drainage',
    dept: 'Storm Water & Surface Drainage',
    subcategories: ['Clogged Storm Drain', 'Sewage Overflow', 'Open Sewer Manhole', 'Monsoon Waterlogging'],
  },
  {
    label: 'Electricity and Streetlights',
    dept: 'Electricity & Public Lighting',
    subcategories: ['Dark Streetlight', 'Hanging Live Wire', 'Damaged Transformer', 'Sparking Pole', 'Power Fluctuations'],
  },
  {
    label: 'Public Infrastructure',
    dept: 'Public Infrastructure & Parks',
    subcategories: ['Broken Footpath', 'Damaged Bus Shelter', 'Park Encroachment', 'Broken Public Bench', 'Damaged Signage'],
  },
  {
    label: 'Other',
    dept: 'Municipal General Administration',
    subcategories: ['Civic Noise Nuisance', 'Illegal Construction', 'Stray Cattle / Animals', 'General Grievance'],
  },
];

export const ReportComplaintPage: React.FC = () => {
  const { isAuthenticated, openAuthModal, demoLogin } = useAuth();

  // Wizard Step State (1: Media, 2: Details, 3: Location, 4: Review, 5: Success)
  const [currentStep, setCurrentStep] = useState<number>(1);

  // Form State
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState<ComplaintCategory>('Road Infrastructure');
  const [subcategory, setSubcategory] = useState('Pothole / Road Cavity');
  const [mediaList, setMediaList] = useState<ComplaintMediaItem[]>([]);
  const [audioItem, setAudioItem] = useState<ComplaintMediaItem | undefined>(undefined);
  const [location, setLocation] = useState<ComplaintLocation>({
    latitude: 17.3850,
    longitude: 78.4867,
    address: 'Hyderabad Civic Region',
  });

  // Severity state (calculated deterministically)
  const [damageScore, setDamageScore] = useState<number>(70);
  const [riskScore, setRiskScore] = useState<number>(75);
  const [publicImpact, setPublicImpact] = useState<number>(65);
  const [locationSensitivity, setLocationSensitivity] = useState<number>(60);

  // Status
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [submittedTrackingId, setSubmittedTrackingId] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  // Compute deterministic severity score
  const computedSeverityScore = Math.round(
    0.30 * damageScore +
    0.30 * riskScore +
    0.20 * publicImpact +
    0.20 * locationSensitivity
  );

  const getPriorityLevel = (score: number): PriorityLevel => {
    if (score <= 30) return 'LOW';
    if (score <= 60) return 'MEDIUM';
    if (score <= 80) return 'HIGH';
    return 'CRITICAL';
  };

  const currentPriority = getPriorityLevel(computedSeverityScore);

  const selectedCategoryObj = CATEGORIES.find((c) => c.label === category) || CATEGORIES[0];

  const handleMediaAdded = (item: ComplaintMediaItem) => {
    setMediaList((prev) => [...prev, item]);
  };

  const handleMediaRemoved = (index: number) => {
    setMediaList((prev) => prev.filter((_, i) => i !== index));
  };

  const handleAudioUploaded = (item: ComplaintMediaItem) => {
    setAudioItem(item);
  };

  const handleAudioRemoved = () => {
    setAudioItem(undefined);
  };

  const handleCategoryChange = (cat: ComplaintCategory) => {
    setCategory(cat);
    const catObj = CATEGORIES.find((c) => c.label === cat);
    if (catObj && catObj.subcategories.length > 0) {
      setSubcategory(catObj.subcategories[0]);
    }
  };

  const handleSubmit = async () => {
    if (!isAuthenticated) {
      openAuthModal('login');
      return;
    }

    if (!title.trim()) {
      setError('Please provide a title for the grievance.');
      setCurrentStep(2);
      return;
    }

    setSubmitting(true);
    setError(null);

    // Combine media
    const allMedia = [...mediaList];
    if (audioItem) {
      allMedia.push(audioItem);
    }

    try {
      const result = await createComplaint({
        title,
        description: description || 'Civic infrastructure complaint submitted via CivicEye multimodal reporting portal.',
        category,
        subcategory,
        severity: currentPriority,
        severity_score: computedSeverityScore,
        risk_level: currentPriority,
        address: location.address,
        latitude: location.latitude,
        longitude: location.longitude,
        media: allMedia,
        location,
      });

      setSubmittedTrackingId(result.tracking_id);
      setCurrentStep(5); // Success step
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit grievance. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const copyTrackingId = () => {
    if (submittedTrackingId) {
      navigator.clipboard.writeText(submittedTrackingId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Page Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <span className="p-2 rounded-xl bg-blue-600/20 text-blue-400">
            <FileText className="w-5 h-5" />
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Report a Civic Grievance
          </h1>
        </div>
        <p className="text-sm text-slate-400">
          Transform unstructured photographs, voice recordings, and videos into an actionable municipal issue.
        </p>
      </div>

      {/* Auth prompt if guest */}
      {!isAuthenticated && (
        <div className="p-4 rounded-2xl bg-slate-900 border border-blue-500/30 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Shield className="w-5 h-5 text-blue-400 shrink-0" />
            <p className="text-xs text-slate-300">
              You are reporting as a guest. Sign in or use the 1-click test persona to link this issue to your citizen dashboard.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => demoLogin('citizen')}
              className="px-3 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 text-xs font-semibold"
            >
              1-Click Demo Citizen
            </button>
            <button
              onClick={() => openAuthModal('login')}
              className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold"
            >
              Sign In
            </button>
          </div>
        </div>
      )}

      {/* Step Progress Stepper */}
      {currentStep < 5 && (
        <div className="grid grid-cols-4 gap-2 text-center text-xs font-semibold">
          {[
            { num: 1, label: '1. Media Capture' },
            { num: 2, label: '2. Issue Details' },
            { num: 3, label: '3. Location Pin' },
            { num: 4, label: '4. AI Review' },
          ].map((st) => (
            <button
              key={st.num}
              type="button"
              onClick={() => setCurrentStep(st.num)}
              className={`py-2.5 rounded-xl border transition-all ${
                currentStep === st.num
                  ? 'bg-blue-600 text-white border-blue-500 shadow-md shadow-blue-600/20'
                  : currentStep > st.num
                  ? 'bg-slate-900 text-emerald-400 border-emerald-500/30'
                  : 'bg-slate-950 text-slate-500 border-slate-800'
              }`}
            >
              <span>{st.label}</span>
            </button>
          ))}
        </div>
      )}

      {error && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* STEP 1: MEDIA CAPTURE */}
      {currentStep === 1 && (
        <div className="p-6 sm:p-8 rounded-2xl bg-slate-900 border border-slate-800 space-y-6">
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-white">Step 1: Capture Media Evidence</h3>
            <p className="text-xs text-slate-400">
              Provide visual photographs or speak a Telugu/English voice description of the damage.
            </p>
          </div>

          <MediaUploader
            mediaList={mediaList}
            onMediaAdded={handleMediaAdded}
            onMediaRemoved={handleMediaRemoved}
          />

          <VoiceRecorder
            currentAudio={audioItem}
            onAudioUploaded={handleAudioUploaded}
            onAudioRemoved={handleAudioRemoved}
          />

          <div className="flex justify-end pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setCurrentStep(2)}
              className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs flex items-center gap-2 shadow-lg shadow-blue-600/30 transition-all"
            >
              <span>Continue to Issue Details</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: ISSUE DETAILS */}
      {currentStep === 2 && (
        <div className="p-6 sm:p-8 rounded-2xl bg-slate-900 border border-slate-800 space-y-6">
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-white">Step 2: Grievance Information</h3>
            <p className="text-xs text-slate-400">
              Describe what is damaged. Our backend routes it to the responsible municipal department automatically.
            </p>
          </div>

          <div className="space-y-4 text-xs">
            {/* Title */}
            <div className="space-y-1.5">
              <label className="text-slate-300 font-medium">Grievance Headline / Summary *</label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Hazardous deep pothole causing two-wheeler skids"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs placeholder-slate-600 focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Category Grid */}
            <div className="space-y-1.5">
              <label className="text-slate-300 font-medium">Civic Infrastructure Category *</label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {CATEGORIES.map((c) => (
                  <button
                    key={c.label}
                    type="button"
                    onClick={() => handleCategoryChange(c.label)}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      category === c.label
                        ? 'bg-blue-600/20 border-blue-500 text-blue-300 font-bold shadow-sm'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <div className="font-semibold text-xs">{c.label}</div>
                    <div className="text-[10px] text-slate-500 truncate mt-0.5">{c.dept}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Subcategory */}
            <div className="space-y-1.5">
              <label className="text-slate-300 font-medium">Specific Problem Type</label>
              <select
                value={subcategory}
                onChange={(e) => setSubcategory(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-blue-500"
              >
                {selectedCategoryObj.subcategories.map((sub) => (
                  <option key={sub} value={sub}>
                    {sub}
                  </option>
                ))}
              </select>
            </div>

            {/* Description */}
            <div className="space-y-1.5">
              <label className="text-slate-300 font-medium">Detailed Description</label>
              <textarea
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Provide details about the issue (e.g. depth of pothole, frequency of water overflow, landmark references)..."
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs placeholder-slate-600 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setCurrentStep(1)}
              className="px-4 py-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 text-slate-300 text-xs font-semibold flex items-center gap-2 border border-slate-800"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </button>
            <button
              type="button"
              onClick={() => setCurrentStep(3)}
              className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs flex items-center gap-2 shadow-lg shadow-blue-600/30 transition-all"
            >
              <span>Continue to Location</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: LOCATION */}
      {currentStep === 3 && (
        <div className="p-6 sm:p-8 rounded-2xl bg-slate-900 border border-slate-800 space-y-6">
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-white">Step 3: Select Incident Location</h3>
            <p className="text-xs text-slate-400">
              Drag the pin on OpenStreetMap or tap "Use My Current Location" for precise GPS triage.
            </p>
          </div>

          <LocationPicker
            latitude={location.latitude}
            longitude={location.longitude}
            address={location.address}
            onChange={(loc) => setLocation(loc)}
          />

          <div className="flex items-center justify-between pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setCurrentStep(2)}
              className="px-4 py-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 text-slate-300 text-xs font-semibold flex items-center gap-2 border border-slate-800"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </button>
            <button
              type="button"
              onClick={() => setCurrentStep(4)}
              className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs flex items-center gap-2 shadow-lg shadow-blue-600/30 transition-all"
            >
              <span>Review AI Triage Summary</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: REVIEW & CONFIRM */}
      {currentStep === 4 && (
        <div className="space-y-6">
          <PreSubmissionReviewCard
            title={title || 'Untitled Grievance'}
            description={description || 'Multimodal complaint report.'}
            category={category}
            severity={currentPriority}
            severityScore={computedSeverityScore}
            departmentName={selectedCategoryObj.dept}
            address={location.address}
            mediaList={audioItem ? [...mediaList, audioItem] : mediaList}
          />

          {/* Interactive Severity Assessment Sliders for Citizen Transparency */}
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold text-amber-400">
              <Sliders className="w-4 h-4" />
              <span>Explainable Severity Factors (Formula: 0.30×Damage + 0.30×Risk + 0.20×Impact + 0.20×Sensitivity)</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="space-y-1">
                <div className="flex justify-between text-slate-400">
                  <span>Physical Damage:</span>
                  <span className="font-mono text-blue-400">{damageScore}/100</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={damageScore}
                  onChange={(e) => setDamageScore(Number(e.target.value))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-slate-400">
                  <span>Public Safety Risk:</span>
                  <span className="font-mono text-cyan-400">{riskScore}/100</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={riskScore}
                  onChange={(e) => setRiskScore(Number(e.target.value))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                />
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-slate-400">
                  <span>Public Impact / Traffic:</span>
                  <span className="font-mono text-emerald-400">{publicImpact}/100</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={publicImpact}
                  onChange={(e) => setPublicImpact(Number(e.target.value))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                />
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-slate-400">
                  <span>Location Sensitivity:</span>
                  <span className="font-mono text-amber-400">{locationSensitivity}/100</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={locationSensitivity}
                  onChange={(e) => setLocationSensitivity(Number(e.target.value))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
                />
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between p-4 rounded-2xl bg-slate-900 border border-slate-800">
            <button
              type="button"
              onClick={() => setCurrentStep(3)}
              className="px-4 py-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 text-slate-300 text-xs font-semibold flex items-center gap-2 border border-slate-800"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </button>

            <button
              type="button"
              disabled={submitting}
              onClick={handleSubmit}
              className="px-8 py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm flex items-center gap-2 shadow-lg shadow-emerald-600/30 transition-all disabled:opacity-50"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>{submitting ? 'Submitting to Civic Registry...' : 'Confirm & Submit Grievance'}</span>
            </button>
          </div>
        </div>
      )}

      {/* STEP 5: SUBMISSION SUCCESS SCREEN */}
      {currentStep === 5 && submittedTrackingId && (
        <div className="p-8 sm:p-12 rounded-2xl bg-slate-900 border border-emerald-500/40 text-center space-y-6 shadow-2xl animate-fade-in">
          <div className="w-16 h-16 rounded-full bg-emerald-500/20 text-emerald-400 mx-auto flex items-center justify-center border border-emerald-500/30">
            <CheckCircle2 className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-white tracking-tight">
              Grievance Successfully Registered!
            </h2>
            <p className="text-xs text-slate-300 max-w-md mx-auto leading-relaxed">
              Your issue has been recorded and routed to <strong className="text-cyan-400">{selectedCategoryObj.dept}</strong>. You can track resolution progress transparently with your tracking code below.
            </p>
          </div>

          {/* Tracking ID Badge & Copy Box */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 max-w-md mx-auto flex items-center justify-between gap-3">
            <div className="text-left">
              <div className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">
                Permanent Tracking Code
              </div>
              <div className="text-lg font-mono font-black text-emerald-400 tracking-wider">
                {submittedTrackingId}
              </div>
            </div>

            <button
              type="button"
              onClick={copyTrackingId}
              className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 text-xs font-medium flex items-center gap-1.5 transition-colors"
            >
              <Copy className="w-3.5 h-3.5" />
              <span>{copied ? 'Copied!' : 'Copy'}</span>
            </button>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-4">
            <Link
              to={`/track/${submittedTrackingId}`}
              className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs flex items-center gap-2 shadow-lg shadow-blue-600/30 transition-all"
            >
              <span>Track Live Status</span>
              <ExternalLink className="w-4 h-4" />
            </Link>

            <Link
              to="/dashboard"
              className="px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 transition-all"
            >
              View My Grievances
            </Link>

            <button
              type="button"
              onClick={() => {
                setTitle('');
                setDescription('');
                setMediaList([]);
                setAudioItem(undefined);
                setSubmittedTrackingId(null);
                setCurrentStep(1);
              }}
              className="px-6 py-3 rounded-xl bg-slate-950 hover:bg-slate-800 text-slate-400 text-xs font-semibold border border-slate-800 transition-all"
            >
              Report Another Issue
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
