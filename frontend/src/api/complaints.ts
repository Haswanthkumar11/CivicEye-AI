import { apiClient } from './client';
import { Complaint, ComplaintCreatePayload, TrackingData, ComplaintMediaItem } from '../types';

export const uploadMediaFile = async (file: File): Promise<ComplaintMediaItem> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/complaints/upload-media', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return {
    media_type: response.data.media_type,
    file_url: response.data.file_url,
    file_name: response.data.file_name,
    file_path: response.data.file_path,
    file_size: response.data.file_size,
    mime_type: response.data.mime_type,
  };
};

export const createComplaint = async (payload: ComplaintCreatePayload): Promise<Complaint> => {
  const response = await apiClient.post('/complaints', payload);
  return response.data;
};

export const getComplaints = async (params?: {
  mine?: boolean;
  category?: string;
  status?: string;
  skip?: number;
  limit?: number;
}): Promise<Complaint[]> => {
  const response = await apiClient.get('/complaints', { params });
  return response.data;
};

export const getComplaintById = async (id: string): Promise<Complaint> => {
  const response = await apiClient.get(`/complaints/${id}`);
  return response.data;
};

export const trackComplaint = async (trackingId: string): Promise<TrackingData> => {
  const response = await apiClient.get(`/complaints/track/${encodeURIComponent(trackingId.trim())}`);
  return response.data;
};
