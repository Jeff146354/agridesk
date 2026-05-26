import axios from 'axios';

// In production the nginx container proxies /api/* to the backend service.
// In local dev, Vite's proxy (vite.config.js) handles /api/* the same way.
// VITE_API_BASE_URL can override this (e.g. for a standalone dev setup pointing at a remote backend).
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

export default api;
