// Configuration
import { API_BASE_URL } from '../config.js';

// Import auth store
import { getToken, clearToken } from '../auth/store.js';

/**
 * Make an API request
 * @param {string} path - API endpoint path (e.g., '/candidates')
 * @param {object} options - { method, body, auth }
 * @returns {Promise<any>} - Parsed JSON response
 */
export async function request(path, options = {}) {
  const { method = 'GET', body = null, auth = true } = options;
  
  const headers = {
    'Content-Type': 'application/json',
  };
  
  if (auth) {
    const token = getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }
  
  const config = {
    method,
    headers,
  };
  
  if (body) {
    config.body = JSON.stringify(body);
  }
  
  const response = await fetch(`${API_BASE_URL}${path}`, config);
  
  // Handle 401 - redirect to login
  if (response.status === 401) {
    clearToken();
    // Don't redirect if already on login page
    if (!window.location.pathname.includes('login.html')) {
      window.location.href = 'login.html';
    }
    throw new Error('Unauthorized');
  }
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || 'Request failed');
  }
  
  return response.json();
}

// Convenience methods
export const api = {
  get: (path) => request(path, { method: 'GET' }),
  post: (path, body) => request(path, { method: 'POST', body }),
  patch: (path, body) => request(path, { method: 'PATCH', body }),
  put: (path, body) => request(path, { method: 'PUT', body }),
  delete: (path) => request(path, { method: 'DELETE' }),
};
