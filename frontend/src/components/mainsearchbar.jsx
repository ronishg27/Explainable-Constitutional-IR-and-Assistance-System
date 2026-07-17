import { useState } from 'react';
import useAskStream from '../hooks/useAskStream';
import Suggestion from './Suggestion';
import Resultdisplay from './Resultdisplay';
import Toggle from './ui/Toggle';
import Button from './ui/Button';
import Alert from './ui/Alert';

export default function MainSearchBar() {
  const [query, setQuery] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const [useLlm, setUseLlm] = useState(true);
  const { articles, response, loading, error, startStream, cancel } = useAskStream();

  const handleSearch = () => {
    if (!query.trim()) return;
    setSubmittedQuery(query);
    startStream(query, useLlm);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSearch();
  };

  return (
    <div className="mx-auto mt-10 max-w-5xl px-4">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-semibold text-neutral-900">
          Search the Constitution
        </h1>
        <p className="mt-1.5 text-sm text-neutral-500">
          Ask a legal question about the Constitution of Nepal
        </p>
      </div>

      <div className="rounded-xl border border-neutral-200 bg-neutral-50 p-4 shadow-sm">
        <div className="flex items-end gap-3">
          <div className="min-w-0 flex-1">
            <label htmlFor="search-input" className="sr-only">
              Search query
            </label>
            <input
              id="search-input"
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="e.g. What are fundamental rights?"
              className="block w-full rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-sm text-neutral-900 placeholder-neutral-400 transition-all hover:border-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-0"
            />
          </div>
          {loading ? (
            <Button onClick={() => { cancel(); setSubmittedQuery(''); }} variant="danger">
              Cancel
            </Button>
          ) : (
            <Button onClick={handleSearch} disabled={!query.trim()}>
              Search
            </Button>
          )}
        </div>

        <div className="mt-3 flex items-center gap-4">
          <Toggle label="Use AI answer" enabled={useLlm} onChange={setUseLlm} />
        </div>

        <Suggestion setQuery={setQuery} />
      </div>

      {error && (
        <Alert variant="error" className="mt-6">
          {error}
        </Alert>
      )}

      <Resultdisplay
        data={articles ? { query: submittedQuery, response, articles } : null}
        loading={loading}
        streamedResponse={response}
      />
    </div>
  );
}
