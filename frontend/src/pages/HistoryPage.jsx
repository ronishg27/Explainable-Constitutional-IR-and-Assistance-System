import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiClient } from '../api/client';

const LIMIT = 20;

export default function HistoryPage() {
  const [messages, setMessages] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchPage = async (skip) => {
    setError('');
    try {
      const res = await apiClient(`/api/v1/messages?limit=${LIMIT}&skip=${skip}`);
      setMessages(res.data);
      setPagination(res.pagination);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this chat?')) return;
    try {
      await apiClient(`/api/v1/messages/${id}`, { method: 'DELETE' });
      setMessages((prev) => prev.filter((m) => m.id !== id));
    } catch (err) {
      setError(err.message);
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm('Delete all chats? This cannot be undone.')) return;
    try {
      await apiClient('/api/v1/messages', { method: 'DELETE' });
      setMessages([]);
      setPagination(null);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    let cancelled = false;

    (async () => {
      setLoading(true);
      setError('');
      try {
        const res = await apiClient(`/api/v1/messages?limit=${LIMIT}&skip=0`);
        if (!cancelled) {
          setMessages(res.data);
          setPagination(res.pagination);
        }
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, []);

  const totalPages = pagination ? Math.ceil(pagination.total / LIMIT) : 0;
  const currentPage = pagination ? Math.floor(pagination.skip / LIMIT) + 1 : 1;

  return (
    <div className="max-w-3xl mx-auto mt-10 px-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Chat History</h1>
        <div className="flex items-center gap-3">
          {messages.length > 0 && (
            <button
              onClick={handleClearAll}
              className="text-sm text-red-500 hover:text-red-700 bg-transparent border-none cursor-pointer"
            >
              Clear All
            </button>
          )}
          <Link
            to="/"
            className="text-sm text-blue-600 hover:text-blue-800 no-underline"
          >
            &larr; New Search
          </Link>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">
          {error}
        </div>
      )}

      {loading && messages.length === 0 && (
        <p className="text-gray-400 text-sm">Loading...</p>
      )}

      {!loading && messages.length === 0 && !error && (
        <p className="text-gray-400 text-sm">No searches yet. Try asking a question!</p>
      )}

      <div className="space-y-3">
        {messages.map((msg) => (
          <div key={msg.id} className="relative group">
            <Link
              to={`/history/${msg.id}`}
              className="block bg-white border border-gray-200 rounded-xl px-5 py-4 hover:border-blue-300 transition-colors no-underline"
            >
              <p className="text-sm font-semibold text-gray-900 truncate">
                {msg.query}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                {new Date(msg.created_at).toLocaleString()} &middot; {msg.articles?.length || 0} articles
              </p>
            </Link>
            <button
              onClick={() => handleDelete(msg.id)}
              className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 p-1.5 text-gray-400 hover:text-red-600 transition-all bg-white rounded-full border border-gray-200 shadow-sm cursor-pointer"
              title="Delete this chat"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
            </button>
          </div>
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 mt-8">
          <button
            disabled={currentPage <= 1}
            onClick={() => fetchPage((currentPage - 2) * LIMIT)}
            className="px-3 py-1 text-sm border border-gray-300 rounded-md bg-white disabled:opacity-40"
          >
            Previous
          </button>
          <span className="text-sm text-gray-500">
            Page {currentPage} of {totalPages}
          </span>
          <button
            disabled={currentPage >= totalPages}
            onClick={() => fetchPage(currentPage * LIMIT)}
            className="px-3 py-1 text-sm border border-gray-300 rounded-md bg-white disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
