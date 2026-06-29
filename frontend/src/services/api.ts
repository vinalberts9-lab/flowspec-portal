import axios, { AxiosInstance } from 'axios';
import { useAuthStore } from '../store/authStore';

const API_URL = import.meta.env.REACT_APP_API_URL || 'http://localhost:5000';

const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add token
api.interceptors.request.use((config) => {
  const { token } = useAuthStore.getState();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (username: string, password: string) =>
    api.post('/api/auth/login', { username, password }),
  register: (username: string, email: string, password: string, role: string) =>
    api.post('/api/auth/register', { username, email, password, role }),
};

export const rulesAPI = {
  createRule: (data: any) => api.post('/api/rules', data),
  listRules: (params: any) => api.get('/api/rules', { params }),
  getRule: (id: string) => api.get(`/api/rules/${id}`),
  updateRule: (id: string, data: any) => api.put(`/api/rules/${id}`, data),
  deployRule: (id: string) => api.post(`/api/rules/${id}/deploy`),
  withdrawRule: (id: string) => api.post(`/api/rules/${id}/withdraw`),
  deleteRule: (id: string) => api.delete(`/api/rules/${id}`),
  previewJuniper: (data: any) => api.post('/api/rules/preview/juniper', data),
  previewExaBGP: (data: any) => api.post('/api/rules/preview/exabgp', data),
};

export const dashboardAPI = {
  getStats: () => api.get('/api/dashboard/stats'),
  getActiveRules: () => api.get('/api/dashboard/active-rules'),
};

export const auditAPI = {
  getLogs: (params: any) => api.get('/api/audit-logs', { params }),
};

export default api;
