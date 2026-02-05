import axios from 'axios';

// In dev, use /api so Vite proxy forwards to backend (avoids wrong host/port or CORS)
const effectiveBase = import.meta.env.DEV && !import.meta.env.VITE_API_BASE_URL
  ? '/api'
  : (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000');
console.log('API Base URL:', effectiveBase);

// Create axios instance
const api = axios.create({
  baseURL: effectiveBase,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Add token to requests if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle 401 errors (unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      message: error.message,
      data: error.response?.data
    });
    
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      // Only redirect if we're not already on the login page
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
