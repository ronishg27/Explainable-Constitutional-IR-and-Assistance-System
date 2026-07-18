import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { apiClient, API } from '../api/client';
import Resultdisplay from '../components/Resultdisplay';
import Dialog from '../components/ui/Dialog';
import Alert from '../components/ui/Alert';
import Spinner from '../components/ui/Spinner';

export default function MessageDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleteOpen, setDeleteOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const res = await apiClient(`${API.MESSAGES}/${id}`);
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
    try {
      await apiClient(`${API.MESSAGES}/${id}`, { method: 'DELETE' });
      navigate('/history');
    } catch (err) {
      setError(err.message);
      setDeleteOpen(false);
    }
  };

  if (loading) {
    return (
      <main className="mx-auto mt-12 max-w-3xl px-4 text-center">
        <Spinner size="lg" className="mx-auto" />
      </main>
    );
  }

  if (error) {
    return (
      <main className="mx-auto mt-12 max-w-3xl px-4">
        <Alert variant="error">{error}</Alert>
        <Link
          to="/history"
          className="inline-block mt-4 text-sm text-primary-600 hover:text-primary-700 no-underline"
        >
          &larr; Back to History
        </Link>
      </main>
    );
  }

  const resultData = {
    query: message.query,
    response: message.answer,
    articles: (message.articles || [])
      .sort((a, b) => (b.relevance_score ?? 0) - (a.relevance_score ?? 0))
      .map((a) => ({
      doc_id: a.doc_id,
      title: a.title,
      citation: a.citation,
      score: a.relevance_score,
      bm25_score: a.bm25_score,
      proximity_score: a.proximity_score,
      title_match_count: a.title_match_count,
      boost_multiplier: a.boost_multiplier,
      article_no: a.article_no,
      clause_no: a.clause_no,
      subclause_id: a.subclause_id,
      level: a.level,
      part_no: a.part_no,
      content: a.content,
      text: a.content,
      full_text: a.content,
      matched_terms: a.matched_terms,
      exact_matched_terms: a.exact_matched_terms,
      matched_clauses: a.matched_clauses,
    })),
  };

  return (
    <main className="mx-auto mt-8 max-w-4xl px-4">
      <div className="flex items-center justify-between mb-6">
        <Link
          to="/history"
          className="text-sm text-primary-600 hover:text-primary-700 no-underline"
        >
          &larr; Back to History
        </Link>
        <button
          onClick={() => setDeleteOpen(true)}
          className="text-sm text-error hover:text-red-700 transition-colors bg-transparent border-none cursor-pointer"
        >
          Delete
        </button>
      </div>

      <Resultdisplay data={resultData} />

      <Dialog
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        onConfirm={handleDelete}
        title="Delete chat"
        message="Are you sure you want to delete this chat?"
        confirmLabel="Delete"
        variant="danger"
      />
    </main>
  );
}
