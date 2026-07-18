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
    <div className="mx-auto mt-16 max-w-[1300px] px-6">
      <div className="text-center mb-10">
        <h1 className="text-4xl font-bold tracking-tight text-neutral-900 md:text-5xl">
          Search the Constitution
        </h1>
        <p className="mt-3 text-lg text-neutral-500 max-w-2xl mx-auto">
          Ask a legal question about the Constitution of Nepal
        </p>
      </div>

      <div className="mx-auto max-w-3xl rounded-4xl border border-neutral-200 bg-white p-6 shadow-lg md:p-8">
        <div className="flex items-end gap-3">
          <div className="min-w-0 flex-1 relative">
            <label htmlFor="search-input" className="sr-only">
              Search query
            </label>
            <div className="relative">
              <svg
                className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400 pointer-events-none"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z" />
              </svg>
              <input
                id="search-input"
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="e.g. What are fundamental rights?"
                className="block w-full rounded-xl border border-neutral-200 bg-neutral-50 pl-11 pr-4 py-[15px] text-base text-neutral-900 placeholder-neutral-400 transition-all hover:border-neutral-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-0 focus:bg-white"
              />
            </div>
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

        <div className="mt-4 flex items-center gap-4">
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
        useLlm={useLlm}
      />
    </div>
  );
}
