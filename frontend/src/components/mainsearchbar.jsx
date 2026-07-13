import { useState, useRef } from 'react';
import useAskStream from '../hooks/useAskStream';
import Suggestion from './Suggestion';
import Resultdisplay from './Resultdisplay';

const MainSearchBar = () => {
  const [query, setQuery] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const [useLlm, setUseLlm] = useState(true);
  const { articles, response, loading, error, startStream, cancel } = useAskStream();

  const buttonRef = useRef(null);

  const handleSearch = () => {
    if (!query.trim()) return;
    setSubmittedQuery(query);
    startStream(query, useLlm);
  };

  return (
    <div className="w-full max-w-2xl mx-auto mt-10 px-4">
      <div className="mb-3 flex justify-end">
        <button
          type="button"
          onClick={() => setUseLlm((prev) => !prev)}
          className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
            useLlm
              ? 'border-blue-600 bg-blue-50 text-blue-700'
              : 'border-gray-300 bg-white text-gray-600'
          }`}
        >
          <span
            className={`h-2.5 w-2.5 rounded-full ${
              useLlm ? 'bg-blue-600' : 'bg-gray-400'
            }`}
          />
          Use LLM: {useLlm ? 'ON' : 'OFF'}
        </button>
      </div>

      <div className="bg-white shadow-2xl flex items-center rounded-full px-4 py-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && buttonRef.current?.click()}
          placeholder="Search constitutional articles..."
          className="flex-1 outline-none bg-transparent"
        />

        <button
          ref={buttonRef}
          type="button"
          onClick={loading ? () => { cancel(); setSubmittedQuery(''); } : handleSearch}
          className={`px-5 py-2 rounded-full font-medium disabled:opacity-60 ${
            loading
              ? 'bg-red-100 text-red-700 hover:bg-red-200'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {loading ? 'Cancel' : 'Analyze Query'}
        </button>
      </div>

      <Suggestion setQuery={setQuery} />

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mt-6 text-center">
          {error}
        </div>
      )}

      <Resultdisplay
        data={articles ? { query: submittedQuery, response, articles } : null}
        loading={loading}
        streamedResponse={response}
      />
    </div>
  );
};

export default MainSearchBar;
