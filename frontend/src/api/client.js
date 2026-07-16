export const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000';

export const API = {
  MESSAGES: '/api/v1/messages',
  LOGIN: '/api/v1/auth/login',
  REGISTER: '/api/v1/auth/register',
  LOGOUT: '/api/v1/auth/logout',
  ME: '/api/v1/auth/me',
  ASK: '/api/v1/ask',
  ASK_STREAM: '/api/v1/ask-stream',
};

export async function apiClient(endpoint, options = {}) {
  const token = localStorage.getItem('token');
  const headers = { 'Content-Type': 'application/json', ...options.headers };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
    signal: AbortSignal.timeout(100000),
  });

  let data;
  try {
    data = await res.json();
  } catch {
    throw new Error(`Unexpected response (${res.status}): ${await res.text().catch(() => 'Could not read body')}`);
  }

  if (!res.ok) {
    throw new Error(data.error || `Request failed with status ${res.status}`);
  }

  return data;
}

export function setToken(token) {
  if (token) {
    localStorage.setItem('token', token);
  } else {
    localStorage.removeItem('token');
  }
}

export function getToken() {
  return localStorage.getItem('token');
}
