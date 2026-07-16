import { useState, useRef, useCallback } from 'react';
import { BASE_URL, API } from '../api/client';

export default function useAskStream() {
  const [articles, setArticles] = useState(null);
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [ollamaStatus, setOllamaStatus] = useState(null);
  const abortRef = useRef(null);

  const startStream = useCallback(async (query, useLlm) => {
    setArticles(null);
    setResponse('');
    setError('');
    setOllamaStatus(null);
    setLoading(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${BASE_URL}${API.ASK_STREAM}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ query, use_llm: useLlm }),
        signal: controller.signal,
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || `Request failed (${res.status})`);
      }

      if (!res.body) {
        throw new Error('Empty response body from server');
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data: ')) continue;

          try {
            const parsed = JSON.parse(trimmed.slice(6));

            switch (parsed.type) {
              case 'articles':
                setArticles(parsed.articles);
                break;
              case 'token':
                setResponse((prev) => prev + parsed.content);
                break;
              case 'done':
                break;
              case 'error':
                setError(parsed.content);
                break;
              case 'status':
                setOllamaStatus(parsed);
                if (!parsed.model_available) {
                  setError(parsed.message || 'Model not available');
                }
                break;
            }
          } catch {
            // skip malformed lines
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message);
      }
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  }, []);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return { articles, response, loading, error, ollamaStatus, startStream, cancel };
}
