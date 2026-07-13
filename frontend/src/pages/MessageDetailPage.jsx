import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import Resultdisplay from '../components/Resultdisplay';

export default function MessageDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const res = await apiClient(`/api/v1/messages/${id}`);
        if (!cancelled) setMessage(res);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [id]);

  const handleDelete = async () => {
    if (!window.confirm('Delete this chat?')) return;
    try {
      await apiClient(`/api/v1/messages/${id}`, { method: 'DELETE' });
      navigate('/history');
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return <div className="text-center text-gray-400 mt-20">Loading...</div>;
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto mt-20 px-4 text-center">
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3">
          {error}
        </div>
        <Link to="/history" className="text-blue-600 text-sm mt-4 inline-block no-underline">
          &larr; Back to History
        </Link>
      </div>
    );
  }

  const resultData = {
    query: message.query,
    response: message.answer,
    articles: message.articles?.map((a) => ({
      doc_id: a.doc_id,
      title: a.title,
      citation: a.citation,
      score: a.relevance_score,
    })),
  };

  return (
    <div className="max-w-3xl mx-auto mt-10 px-4">
      <div className="flex items-center justify-between mb-4">
        <Link
          to="/history"
          className="text-sm text-blue-600 hover:text-blue-800 no-underline"
        >
          &larr; Back to History
        </Link>
        <button
          onClick={handleDelete}
          className="text-sm text-red-500 hover:text-red-700 bg-transparent border-none cursor-pointer flex items-center gap-1"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </svg>
          Delete
        </button>
      </div>
      <Resultdisplay data={resultData} />
    </div>
  );
}
