export interface SystemHealth {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp: string;
  runtime: {
    python_version: string;
    os: string;
    platform: string;
  };
  components: {
    api_server: string;
    database_driver: string;
    gemini_api: string;
    local_yolo_cv: string;
    local_whisper_asr: string;
    media_storage: string;
  };
  modules: Array<{
    id: string;
    name: string;
    status: string;
  }>;
}

export type ComplaintCategory =
  | 'Road Infrastructure'
  | 'Water Supply'
  | 'Sanitation'
  | 'Drainage'
  | 'Electricity and Streetlights'
  | 'Public Infrastructure'
  | 'Other';

export type PriorityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type ComplaintStatus =
  | 'SUBMITTED'
  | 'UNDER_REVIEW'
  | 'ASSIGNED'
  | 'IN_PROGRESS'
  | 'RESOLVED'
  | 'REJECTED';

export interface ComplaintMediaItem {
  id?: string;
  media_type: 'IMAGE' | 'VIDEO' | 'AUDIO';
  file_url: string;
  file_name?: string;
  file_path?: string;
  file_size?: number;
  mime_type?: string;
  created_at?: string;
}

export interface ComplaintLocation {
  id?: string;
  latitude: number;
  longitude: number;
  address?: string;
  landmark?: string;
  ward?: string;
  city?: string;
  postal_code?: string;
}

export interface StatusHistoryItem {
  id?: string;
  previous_status: string;
  new_status: string;
  notes?: string;
  created_at?: string;
  changed_by?: string;
}

export interface Complaint {
  id: string;
  tracking_id: string;
  citizen_id: string;
  title: string;
  description: string;
  category: ComplaintCategory;
  subcategory?: string;
  severity: PriorityLevel;
  severity_score: number;
  risk_level: string;
  status: ComplaintStatus;
  rejection_reason?: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  department_id?: string;
  department_name?: string;
  duplicate_group_id?: string;
  created_at?: string;
  updated_at?: string;
  media: ComplaintMediaItem[];
  location?: ComplaintLocation;
  status_history: StatusHistoryItem[];
}

export interface TimelineStage {
  key: ComplaintStatus;
  label: string;
  completed: boolean;
}

export interface TrackingData {
  id: string;
  tracking_id: string;
  title: string;
  description?: string;
  category: ComplaintCategory;
  subcategory?: string;
  severity: PriorityLevel;
  severity_score: number;
  risk_level?: string;
  status: ComplaintStatus;
  rejection_reason?: string;
  department_name?: string;
  address?: string;
  created_at?: string;
  updated_at?: string;
  status_history: StatusHistoryItem[];
  media: ComplaintMediaItem[];
  timeline_stages: TimelineStage[];
}

export interface ComplaintCreatePayload {
  title: string;
  description: string;
  category: ComplaintCategory;
  subcategory?: string;
  severity?: PriorityLevel;
  severity_score?: number;
  risk_level?: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  media?: ComplaintMediaItem[];
  location?: ComplaintLocation;
}
