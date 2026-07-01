import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach JWT Token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Unwrap success, handle errors
api.interceptors.response.use(
  (response) => {
    // The backend standard is { success: true, data: { ... } }
    if (response.data && response.data.success) {
      return response.data.data;
    }
    return response.data;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Auto-logout on unauthorized if it's not the login route
      if (!error.config.url.includes('/auth/login')) {
        useAuthStore.getState().logout();
      }
    }
    
    // Check for standard error response: { success: false, error: { message: "..." } }
    const serverError = error.response?.data?.error;
    if (serverError) {
      return Promise.reject(serverError);
    }
    
    return Promise.reject(error);
  }
);
