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

export interface ComplaintPreview {
  id: string;
  tracking_id: string;
  title: string;
  category: ComplaintCategory;
  subcategory: string;
  severity: PriorityLevel;
  severity_score: number;
  department: string;
  status: 'SUBMITTED' | 'UNDER_REVIEW' | 'ASSIGNED' | 'IN_PROGRESS' | 'RESOLVED' | 'REJECTED';
  location_name: string;
  created_at: string;
  has_audio: boolean;
  has_image: boolean;
  cv_detected?: string;
  language?: string;
}
