import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { createComplaint } from '../api/complaints';
import { MediaUploader } from '../components/complaints/MediaUploader';
import { VoiceRecorder } from '../components/complaints/VoiceRecorder';
import { LocationPicker } from '../components/complaints/LocationPicker';
import { PreSubmissionReviewCard } from '../components/complaints/PreSubmissionReviewCard';
import axios from 'axios';
import { ComplaintCategory, PriorityLevel, ComplaintMediaItem, ComplaintLocation, RoadDamageAnalysisResult } from '../types';
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
  Layers,
  Camera,
  MessageSquare,
  MapPin,
  Eye,
  Check,
  Scan,
  Loader2,
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

  // Wizard Step State:
  // Step 1: Select complaint category
  // Step 2: Upload photographs, videos or voice recordings
  // Step 3: Enter written description or record voice complaint
  // Step 4: Select geographical location using map
  // Step 5: Display complaint review screen
  // Step 6: Submit and generate tracking ID
  const [currentStep, setCurrentStep] = useState<number>(1);

  // Form State (preserved across steps)
  const [category, setCategory] = useState<ComplaintCategory>('Road Infrastructure');
  const [subcategory, setSubcategory] = useState('Pothole / Road Cavity');
  const [mediaList, setMediaList] = useState<ComplaintMediaItem[]>([]);
  const [audioItem, setAudioItem] = useState<ComplaintMediaItem | undefined>(undefined);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState<ComplaintLocation>({
    latitude: 17.3850,
    longitude: 78.4867,
    address: 'Hyderabad Civic Region',
  });

  // Severity state (calculated deterministically: 0.30*Damage + 0.30*Risk + 0.20*Impact + 0.20*Sensitivity)
  const [damageScore, setDamageScore] = useState<number>(70);
  const [riskScore, setRiskScore] = useState<number>(75);
  const [publicImpact, setPublicImpact] = useState<number>(65);
  const [locationSensitivity, setLocationSensitivity] = useState<number>(60);

  // Submission Status
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [stepError, setStepError] = useState<string | null>(null);
  const [submittedTrackingId, setSubmittedTrackingId] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  // Local YOLO Road Damage AI State (Phase 4B)
  const [roadDamageResult, setRoadDamageResult] = useState<RoadDamageAnalysisResult | null>(null);
  const [scanningRoadDamage, setScanningRoadDamage] = useState<boolean>(false);

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

  const triggerRoadDamageScan = async (url?: string) => {
    const targetUrl = url || mediaList.find((m) => m.media_type === 'IMAGE')?.file_url;
    if (!targetUrl) return;

    setScanningRoadDamage(true);
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('media_url', targetUrl);
      formData.append('confidence_threshold', '0.35');

      const res = await axios.post<RoadDamageAnalysisResult>('/api/ai/detect-road-damage', formData, {
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });

      if (res.data) {
        setRoadDamageResult(res.data);
        if (res.data.processing_status === 'SUCCESS' && res.data.detection_count > 0) {
          setDamageScore(Math.round(res.data.estimated_visual_damage_level));
        }
      }
    } catch (err) {
      console.warn('Road damage detection scan skipped or offline:', err);
    } finally {
      setScanningRoadDamage(false);
    }
  };

  const handleCategoryChange = (cat: ComplaintCategory) => {
    setCategory(cat);
    const catObj = CATEGORIES.find((c) => c.label === cat);
    if (catObj && catObj.subcategories.length > 0) {
      setSubcategory(catObj.subcategories[0]);
    }
  };

  const handleMediaAdded = (item: ComplaintMediaItem) => {
    setMediaList((prev) => [...prev, item]);
    if (category === 'Road Infrastructure' && item.media_type === 'IMAGE') {
      triggerRoadDamageScan(item.file_url);
    }
  };

  const handleMediaRemoved = (index: number) => {
    setMediaList((prev) => {
      const updated = prev.filter((_, i) => i !== index);
      if (updated.filter((m) => m.media_type === 'IMAGE').length === 0) {
        setRoadDamageResult(null);
      }
      return updated;
    });
  };

  const handleAudioUploaded = (item: ComplaintMediaItem) => {
    setAudioItem(item);
  };

  const handleAudioRemoved = () => {
    setAudioItem(undefined);
  };

  // Step Navigation with validation
  const goToStep = (step: number) => {
    setStepError(null);

    // If moving forward from Step 3 (Description), validate title
    if (currentStep === 3 && step > 3) {
      if (!title.trim() || title.trim().length < 3) {
        setStepError('Please enter a clear title (at least 3 characters) for your grievance.');
        return;
      }
    }

    setCurrentStep(step);
  };

  const handleSubmit = async () => {
    if (!isAuthenticated) {
      openAuthModal('login');
      return;
    }

    if (!title.trim() || title.trim().length < 3) {
      setStepError('Please provide a title with at least 3 characters.');
      setCurrentStep(3);
      return;
    }

    setSubmitting(true);
    setStepError(null);

    // Combine media items
    const allMedia = [...mediaList];
    if (audioItem) {
      allMedia.push(audioItem);
    }

    try {
      const result = await createComplaint({
        title: title.trim(),
        description: description.trim() || 'Civic grievance reported through multimodal submission portal.',
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
      setCurrentStep(6); // Step 6: Tracking ID Confirmation
    } catch (err: any) {
      setStepError(err.response?.data?.detail || 'Failed to submit grievance. Please verify details and try again.');
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

  const stepperItems = [
    { num: 1, label: 'Category', icon: Layers },
    { num: 2, label: 'Media', icon: Camera },
    { num: 3, label: 'Description', icon: MessageSquare },
    { num: 4, label: 'Location', icon: MapPin },
    { num: 5, label: 'Review', icon: Eye },
    { num: 6, label: 'Tracking ID', icon: Check },
  ];

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

      {/* Guest Warning / Persona switcher */}
      {!isAuthenticated && (
        <div className="p-4 rounded-2xl bg-slate-900 border border-blue-500/30 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Shield className="w-5 h-5 text-blue-400 shrink-0" />
            <p className="text-xs text-slate-300">
              You are currently reporting as a guest. Sign in or use the 1-click test persona to link this issue to your citizen dashboard.
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

      {/* 6-Step Stepper Header */}
      {currentStep <= 5 && (
        <div className="grid grid-cols-5 gap-2 text-center text-xs font-semibold">
          {stepperItems.slice(0, 5).map((st) => (
            <button
              key={st.num}
              type="button"
              onClick={() => goToStep(st.num)}
              className={`py-2 px-1 rounded-xl border flex flex-col items-center gap-1 transition-all ${
                currentStep === st.num
                  ? 'bg-blue-600 text-white border-blue-500 shadow-md shadow-blue-600/20'
                  : currentStep > st.num
                  ? 'bg-slate-900 text-emerald-400 border-emerald-500/30'
                  : 'bg-slate-950 text-slate-500 border-slate-800'
              }`}
            >
              <st.icon className="w-3.5 h-3.5" />
              <span className="truncate">{st.num}. {st.label}</span>
            </button>
          ))}
        </div>
      )}

      {/* Step Validation / API Error Banner */}
      {stepError && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{stepError}</span>
        </div>
      )}

      {/* STEP 1: SELECT COMPLAINT CATEGORY */}
      {currentStep === 1 && (
        <div className="p-6 sm:p-8 rounded-2xl bg-slate-900 border border-slate-800 space-y-6">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-blue-500/10 text-blue-400 text-[11px] font-semibold">
              <Layers className="w-3.5 h-3.5" />
              <span>Step 1 of 5</span>
            </div>
            <h3 className="text-lg font-bold text-white">Select Complaint Category</h3>
            <p className="text-xs text-slate-400">
              Select the primary infrastructure category that best describes the municipal issue.
            </p>
          </div>

          {/* Category Grid */}
          <div className="space-y-2">
            <label className="text-xs text-slate-300 font-medium">Infrastructure Category *</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
              {CATEGORIES.map((c) => (
                <button
                  key={c.label}
                  type="button"
                  onClick={() => handleCategoryChange(c.label)}
                  className={`p-3.5 rounded-xl border text-left transition-all ${
                    category === c.label
                      ? 'bg-blue-600/20 border-blue-500 text-blue-200 font-bold shadow-md shadow-blue-500/10 ring-1 ring-blue-500/50'
                      : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                  }`}
                >
                  <div className="font-semibold text-xs text-white">{c.label}</div>
                  <div className="text-[10px] text-cyan-400/80 truncate mt-1">
                    Routes to: {c.dept}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Subcategory */}
          <div className="space-y-1.5 text-xs">
            <label className="text-slate-300 font-medium">Specific Problem Type / Subcategory</label>
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

          {/* Routing recommendation badge */}
          <div className="p-3 rounded-xl bg-blue-950/40 border border-blue-900/50 flex items-center justify-between text-xs">
            <span className="text-slate-400">Recommended Handling Department:</span>
            <span className="font-semibold text-cyan-400">{selectedCategoryObj.dept}</span>
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={() => goToStep(2)}
              className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs flex items-center gap-2 shadow-lg shadow-blue-600/30 transition-all"
            >
              <span>Continue to Media Upload</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: UPLOAD PHOTOGRAPHS, VIDEOS OR VOICE RECORDINGS */}
      {currentStep === 2 && (
        <div className="p-6 sm:p-8 rounded-2xl bg-slate-900 border border-slate-800 space-y-6">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-blue-500/10 text-blue-400 text-[11px] font-semibold">
              <Camera className="w-3.5 h-3.5" />
              <span>Step 2 of 5</span>
            </div>
            <h3 className="text-lg font-bold text-white">Upload Media Evidence</h3>
            <p className="text-xs text-slate-400">
              Upload photographs, recorded videos, or audio evidence of the damage. (Files validated up to 25MB).
            </p>
          </div>

          <MediaUploader
            mediaList={mediaList}
            onMediaAdded={handleMediaAdded}
            onMediaRemoved={handleMediaRemoved}
          />

          {/* Local YOLO Road Damage Computer Vision Trigger (Phase 4B) */}
          {category === 'Road Infrastructure' && mediaList.some((m) => m.media_type === 'IMAGE') && (
            <div className="p-4 rounded-xl bg-slate-950 border border-cyan-500/30 space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2 text-cyan-400 font-bold text-xs">
                  <Scan className="w-4 h-4" />
                  <span>Local Road Damage Computer Vision (YOLO)</span>
                </div>
                <button
                  type="button"
                  disabled={scanningRoadDamage}
                  onClick={() => triggerRoadDamageScan()}
                  className="px-3 py-1.5 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/40 text-xs font-semibold flex items-center gap-1.5 transition-all w-fit"
                >
                  {scanningRoadDamage ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Scanning Evidence...</span>
                    </>
                  ) : (
                    <>
                      <Scan className="w-3.5 h-3.5" />
                      <span>{roadDamageResult ? 'Re-scan Evidence' : 'Scan for Potholes & Cracks'}</span>
                    </>
                  )}
                </button>
              </div>

              {roadDamageResult ? (
                <div className="text-xs space-y-1.5 pt-1 border-t border-slate-900">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                      {roadDamageResult.model_name} • {roadDamageResult.inference_device} ({roadDamageResult.inference_time_ms}ms)
                    </span>
                    <span className="text-slate-400 text-[11px]">
                      {roadDamageResult.detection_count} defect(s) detected
                    </span>
                  </div>
                  <p className="text-slate-300 text-[11px]">
                    {roadDamageResult.visual_evidence_explanation}
                  </p>
                </div>
              ) : (
                <p className="text-[11px] text-slate-400">
                  Click to inspect uploaded road photos locally using YOLO computer vision. Detected potholes and surface cracks will automatically modulate physical severity.
                </p>
              )}
            </div>
          )}

          <div className="flex items-center justify-between pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={() => goToStep(1)}
              className="px-4 py-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 text-slate-300 text-xs font-semibold flex items-center gap-2 border border-slate-800"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Category</span>
            </button>
            <button
              type="button"
              onClick={() => goToStep(3)}
              className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs flex items-center gap-2 shadow-lg shadow-blue-600/30 transition-all"
            >
              <span>Continue to Description</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: ENTER WRITTEN DESCRIPTION OR RECORD A VOICE COMPLAINT */}
      {currentStep === 3 && (
        <div className="p-6 sm:p-8 rounded-2xl bg-slate-900 border border-slate-800 space-y-6">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-blue-500/10 text-blue-400 text-[11px] font-semibold">
              <MessageSquare className="w-3.5 h-3.5" />
              <span>Step 3 of 5</span>
            </div>
            <h3 className="text-lg font-bold text-white">Description & Voice Complaint</h3>
            <p className="text-xs text-slate-400">
              Enter a clear title, type a written description, or record a voice note in Telugu or English.
            </p>
          </div>

          <div className="space-y-4 text-xs">
            {/* Title */}
            <div className="space-y-1.5">
              <label className="text-slate-300 font-medium">Grievance Headline / Title *</label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Hazardous deep pothole causing two-wheeler skids"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs placeholder-slate-600 focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Description Textarea */}
            <div className="space-y-1.5">
              <label className="text-slate-300 font-medium">Written Description</label>
              <textarea
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the severity, frequency, or landmarks (e.g. Near Gandhi statue junction, water overflowing into street)..."
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs placeholder-slate-600 focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Voice Recorder Integration */}
            <div className="space-y-1.5 pt-2">
              <label className="text-slate-300 font-medium">Or Record Voice Complaint (Telugu / English)</label>
              <VoiceRecorder
                currentAudio={audioItem}
                onAudioUploaded={handleAudioUploaded}
                onAudioRemoved={handleAudioRemoved}
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={() => goToStep(2)}
              className="px-4 py-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 text-slate-300 text-xs font-semibold flex items-center gap-2 border border-slate-800"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Media</span>
            </button>
            <button
              type="button"
              onClick={() => goToStep(4)}
              className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs flex items-center gap-2 shadow-lg shadow-blue-600/30 transition-all"
            >
              <span>Continue to Location</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: SELECT GEOGRAPHICAL LOCATION USING MAP */}
      {currentStep === 4 && (
        <div className="p-6 sm:p-8 rounded-2xl bg-slate-900 border border-slate-800 space-y-6">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-blue-500/10 text-blue-400 text-[11px] font-semibold">
              <MapPin className="w-3.5 h-3.5" />
              <span>Step 4 of 5</span>
            </div>
            <h3 className="text-lg font-bold text-white">Select Geographical Location</h3>
            <p className="text-xs text-slate-400">
              Pinpoint the issue on the interactive map or use browser GPS auto-detection. Manual address entry is available below.
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
              onClick={() => goToStep(3)}
              className="px-4 py-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 text-slate-300 text-xs font-semibold flex items-center gap-2 border border-slate-800"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Description</span>
            </button>
            <button
              type="button"
              onClick={() => goToStep(5)}
              className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs flex items-center gap-2 shadow-lg shadow-blue-600/30 transition-all"
            >
              <span>Review Grievance Summary</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 5: DISPLAY COMPLAINT REVIEW SCREEN */}
      {currentStep === 5 && (
        <div className="space-y-6">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-bold text-white">Step 5: Review Grievance Details Before Submission</span>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
              Pre-Dispatch Triage
            </span>
          </div>

          <PreSubmissionReviewCard
            title={title || 'Untitled Grievance'}
            description={description || 'Multimodal complaint report.'}
            category={category}
            severity={currentPriority}
            severityScore={computedSeverityScore}
            departmentName={selectedCategoryObj.dept}
            address={location.address}
            mediaList={audioItem ? [...mediaList, audioItem] : mediaList}
            roadDamageResult={roadDamageResult}
          />

          {/* Explainable Severity Factor Controls */}
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold text-amber-400">
              <Sliders className="w-4 h-4" />
              <span>Severity Scoring (Formula: 0.30×Damage + 0.30×Risk + 0.20×Impact + 0.20×Sensitivity)</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="space-y-1">
                <div className="flex justify-between text-slate-400">
                  <span>Physical Damage Factor:</span>
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
              onClick={() => goToStep(4)}
              className="px-4 py-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 text-slate-300 text-xs font-semibold flex items-center gap-2 border border-slate-800"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Location</span>
            </button>

            <button
              type="button"
              disabled={submitting}
              onClick={handleSubmit}
              className="px-8 py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm flex items-center gap-2 shadow-lg shadow-emerald-600/30 transition-all disabled:opacity-50"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>{submitting ? 'Submitting to Civic Registry...' : 'Submit & Generate Tracking ID'}</span>
            </button>
          </div>
        </div>
      )}

      {/* STEP 6: SUBMISSION SUCCESS SCREEN & TRACKING ID */}
      {currentStep === 6 && submittedTrackingId && (
        <div className="p-8 sm:p-12 rounded-2xl bg-slate-900 border border-emerald-500/40 text-center space-y-6 shadow-2xl animate-fade-in">
          <div className="w-16 h-16 rounded-full bg-emerald-500/20 text-emerald-400 mx-auto flex items-center justify-center border border-emerald-500/30">
            <CheckCircle2 className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-semibold border border-emerald-500/20">
              <Check className="w-3.5 h-3.5" />
              <span>Step 6: Registration Complete</span>
            </div>
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

          {/* Action Navigation */}
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
