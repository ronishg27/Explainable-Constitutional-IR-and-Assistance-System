import React, { useState } from 'react';

const ResultDisplay = ({ data }) => {
  if (!data) return null;

  const { query, response, articles } = data;
  const [openId, setOpenId] = useState(null);

  const toggle = (doc_id) => setOpenId(prev => prev === doc_id ? null : doc_id);

  return (
    <div className="w-fit max-w-2xl mx-auto mt-10 px-6 py-6 bg-gray-100 space-y-6">

      {/* Query */}
      <div>
        <p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Query</p>
        <p className="text-lg font-semibold text-gray-900">{query}</p>
      </div>

      {/* LLM Response */}
      {response && (
        <div className=" pl-4">
          <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">{response}</p>
        </div>
      )}

      {/* Articles */}
      {articles?.length > 0 && (
        <div className="space-y-3">
          <p className="text-sm text-gray-500">
            Following are the constitutional articles related to{' '}
            <span className="text-gray-800 font-medium">"{query}"</span>
          </p>

          <div className="space-y-2">
            {articles.map((article, index) => {
              const isOpen = openId === article.doc_id;
              return (
                <div key={`${article.doc_id}-${index}`}>

                  <button
                    onClick={() => toggle(article.doc_id)}
                    className="w-full text-left bg-white hover:bg-gray-50 border border-gray-200 px-4 py-3 flex items-center gap-3 transition-colors"
                    style={{ borderRadius: isOpen ? '12px 12px 0 0' : '12px', borderColor: isOpen ? '#3b82f6' : '#e5e7eb' }}
                  >
                    <span className="text-xs text-gray-400 w-5 shrink-0">#{index + 1}</span>

                    <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center shrink-0">
                      <span className="text-xs font-semibold text-blue-600">{article.article_no}</span>
                    </div>

                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-800 truncate">{article.title}</p>
                      <p className="text-xs text-gray-00 mt-0.5">{article.citation}</p>
                    </div>

                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none"
                      style={{ transition: 'transform 0.2s', transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)', flexShrink: 0 }}>
                      <path d="M4 6l4 4 4-4" stroke="#9ca3af" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </button>

                  {isOpen && (
                    <div className="bg-blue-50 border border-blue-200 border-t-0 rounded-b-xl px-5 py-4 space-y-2">
                      <p className="text-xs text-gray-500">Article no: <span className="text-gray-800 font-medium">{article.article_no}</span></p>
                      <p className="text-xs text-gray-500">Citation: <span className="text-gray-800 font-medium">{article.citation}</span></p>
                      <p className="text-xs text-gray-500">Doc ID: <span className="text-gray-800 font-medium">{article.doc_id}</span></p>
                      <p className="text-xs text-gray-500">Score: <span className="text-gray-800 font-medium">{article.score.toFixed(2)}</span></p>
                      <p className="text-xs text-gray-500">Title: <span className="text-gray-800 font-medium">{article.title}</span></p>
                    </div>
                  )}

                </div>
              );
            })}
          </div>
        </div>
      )}

    </div>
  );
};

export default ResultDisplay;