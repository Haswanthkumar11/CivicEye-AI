import axios from 'axios';

// Vite environment configuration with fallback to local proxy / standard port
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

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
