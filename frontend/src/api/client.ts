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

export const checkSystemHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};
