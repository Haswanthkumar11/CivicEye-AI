import axios from 'axios';

// Vite environment configuration with fallback to local proxy / standard port
const rawBaseUrl = (import.meta.env.VITE_API_BASE_URL || '/api').trim();

// Normalize: if it's a full URL without trailing /api, ensure /api is attached cleanly
export const API_BASE_URL = (rawBaseUrl.startsWith('http') && !rawBaseUrl.replace(/\/+$/, '').endsWith('/api'))
  ? `${rawBaseUrl.replace(/\/+$/, '')}/api`
  : rawBaseUrl;

export const getDocsUrl = (): string => {
  if (import.meta.env.VITE_API_DOCS_URL) {
    return import.meta.env.VITE_API_DOCS_URL;
  }
  if (rawBaseUrl.startsWith('http')) {
    return `${rawBaseUrl.replace(/\/api\/?$/, '')}/docs`;
  }
  return 'https://civiceye-ai.onrender.com/docs';
};

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach Authorization header automatically if token exists in localStorage
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('civiceye_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const checkSystemHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};
