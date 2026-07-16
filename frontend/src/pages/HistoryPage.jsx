import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiClient, API } from '../api/client';
import Pagination from '../components/ui/Pagination';
import Dialog from '../components/ui/Dialog';
import Alert from '../components/ui/Alert';
import Spinner from '../components/ui/Spinner';

const LIMIT = 20;

export default function HistoryPage() {
  const [messages, setMessages] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [clearOpen, setClearOpen] = useState(false);

  const fetchPage = async (page) => {
    const skip = (page - 1) * LIMIT;
    setError('');
    setLoading(true);
    try {
      const res = await apiClient(`${API.MESSAGES}?limit=${LIMIT}&skip=${skip}`);
      setMessages(res.data);
      setPagination(res.pagination);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await apiClient(`${API.MESSAGES}/${deleteTarget}`, { method: 'DELETE' });
      setMessages((prev) => prev.filter((m) => m.id !== deleteTarget));
    } catch (err) {
      setError(err.message);
    } finally {
      setDeleteTarget(null);
    }
  };

  const handleClearAll = async () => {
    try {
      await apiClient(API.MESSAGES, { method: 'DELETE' });
      setMessages([]);
      setPagination(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setClearOpen(false);
    }
  };

  useEffect(() => {
    let cancelled = false;

    (async () => {
      setLoading(true);
      setError('');
      try {
        const res = await apiClient(`${API.MESSAGES}?limit=${LIMIT}&skip=0`);
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
    <main className="mx-auto mt-8 max-w-3xl px-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-lg font-semibold text-neutral-900">Chat History</h1>
        <div className="flex items-center gap-3">
          {messages.length > 0 && (
            <button
              onClick={() => setClearOpen(true)}
              className="text-sm text-error hover:text-red-700 transition-colors bg-transparent border-none cursor-pointer"
            >
              Clear All
            </button>
          )}
          <Link
            to="/"
            className="text-sm text-primary-600 hover:text-primary-700 no-underline"
          >
            &larr; New Search
          </Link>
        </div>
      </div>

      {error && (
        <Alert variant="error" className="mb-4">{error}</Alert>
      )}

      {loading && messages.length === 0 && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-[72px] animate-pulse rounded-lg bg-neutral-100"
            />
          ))}
        </div>
      )}

      {!loading && messages.length === 0 && !error && (
        <p className="text-sm text-neutral-400">
          No searches yet.{" "}
          <Link to="/" className="text-primary-600 hover:text-primary-700 underline">
            Try asking a question
          </Link>
        </p>
      )}

      <div className="space-y-2">
        {messages.map((msg) => (
          <div key={msg.id} className="group relative">
            <Link
              to={`/history/${msg.id}`}
              className="block rounded-lg border border-neutral-200 bg-white px-4 py-3.5 hover:border-neutral-300 transition-colors no-underline"
            >
              <p className="text-sm font-medium text-neutral-900 truncate pr-8">
                {msg.query}
              </p>
              <p className="text-xs text-neutral-400 mt-1">
                {new Date(msg.created_at).toLocaleString()} &middot;{' '}
                {msg.articles?.length || 0} articles
              </p>
            </Link>
            <button
              onClick={() => setDeleteTarget(msg.id)}
              className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 p-1 rounded text-neutral-400 hover:text-error transition-all bg-white border border-neutral-200 shadow-sm cursor-pointer"
              aria-label="Delete this chat"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
            </button>
          </div>
        ))}
      </div>

      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={fetchPage}
        className="mt-8"
      />

      <Dialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete chat"
        message="Are you sure you want to delete this chat?"
        confirmLabel="Delete"
        variant="danger"
      />

      <Dialog
        open={clearOpen}
        onClose={() => setClearOpen(false)}
        onConfirm={handleClearAll}
        title="Clear all chats"
        message="Delete all chats? This cannot be undone."
        confirmLabel="Clear All"
        variant="danger"
      />
    </main>
  );
}
