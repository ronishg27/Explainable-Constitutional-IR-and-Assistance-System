import { useState, useEffect, useCallback } from 'react';
import { apiClient, setToken, getToken } from '../api/client';
import AuthContext from './authContext';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      const token = getToken();
      if (!token) {
        if (!cancelled) setLoading(false);
        return;
      }

      try {
        const res = await apiClient('/api/v1/auth/me');
        if (!cancelled) setUser(res.data);
      } catch {
        if (!cancelled) setToken(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, []);

  const login = useCallback(async (email, password) => {
    const res = await apiClient('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    setToken(res.token);
    setUser(res.user);
    return res;
  }, []);

  const register = useCallback(async (fullname, email, password) => {
    const res = await apiClient('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ fullname, email, password }),
    });
    return res;
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiClient('/api/v1/auth/logout', { method: 'POST' });
    } catch {
      // still clear local state
    }
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
