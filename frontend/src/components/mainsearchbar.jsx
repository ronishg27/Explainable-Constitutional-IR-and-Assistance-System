import React, { useState, useRef } from 'react';
import Suggestion from './Suggestion';
import Resultdisplay from './Resultdisplay';

const MainSearchBar = () => {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false); // tracks whether backend is still responding

  const buttonRef = useRef(null);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true); // start loading before the request

    try {
      const response = await fetch('http://127.0.0.1:5000/api/v1/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          use_llm: true,
        }),
      });

      if (!response.ok) {
        throw new Error('Backend request failed');
      }

      const data = await response.json();

      console.log('Backend response:', data);

      // Save backend result in state
      setResult(data);

    } catch (error) {
      console.error('Error while calling backend:', error);
    } finally {
      setLoading(false); // stop loading whether request succeeded or failed
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto mt-10 px-4">
      <div className="bg-white shadow-2xl flex items-center rounded-full px-4 py-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && buttonRef.current?.click()}
          placeholder="Search constitutional articles..."
          className="flex-1 outline-none bg-transparent"
        />

        {/* Button is disabled while loading to prevent duplicate requests */}
        <button
          ref={buttonRef}
          type="button"
          onClick={handleSearch}
          disabled={loading}
          className="bg-blue-600 text-white px-5 py-2 rounded-full hover:bg-blue-700 disabled:opacity-60"
        >
          {loading ? 'Analyzing...' : 'Analyze Query'}
        </button>
      </div>

      <Suggestion setQuery={setQuery} />

      {/* Show loading message while waiting for backend, result once it arrives */}
      {loading && (
        <p className="text-center text-gray-400 mt-10 text-sm">Analyzing...</p>
      )}
      {!loading && result && <Resultdisplay data={result} />}
    </div>
  );
};

export default MainSearchBar;