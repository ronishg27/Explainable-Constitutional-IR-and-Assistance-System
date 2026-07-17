import { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ArticleCard from './ArticleCard';
import Spinner from './ui/Spinner';

const CITATION_RE = /\(Article\s+(\d+(?:[–-]\d+)?)\)/g;

function processCitations(text) {
  return text.replace(CITATION_RE, (match, id) => `[${match}](#article-${id})`);
}

function CitationLink({ href, children, ...props }) {
  const handleClick = (e) => {
    if (href?.startsWith('#article-')) {
      e.preventDefault();
      const id = href.slice(1);
      const el = document.getElementById(id);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        el.classList.add('ring-2', 'ring-primary-400', 'ring-offset-2');
        setTimeout(() => el.classList.remove('ring-2', 'ring-primary-400', 'ring-offset-2'), 2000);
      }
    }
  };

  return (
    <a
      href={href}
      onClick={handleClick}
      className="text-primary-600 hover:text-primary-700 underline underline-offset-2 decoration-primary-300 font-medium cursor-pointer"
      {...props}
    >
      {children}
    </a>
  );
}

const PhasedLoading = ({ hasArticles, useLlm }) => {
  const phases = [
    { label: 'Searching the constitution...', show: !hasArticles },
    { label: 'Generating answer...', show: hasArticles && useLlm },
  ];

  const active = phases.find((p) => p.show);
  if (!active) return null;

  return (
    <div className="flex items-center gap-2.5 text-sm text-neutral-400">
      <Spinner size="sm" />
      <span className="animate-pulse">{active.label}</span>
    </div>
  );
};

const ResultDisplay = ({ data, loading, streamedResponse, useLlm }) => {
  const displayResponse = streamedResponse || data?.response || '';

  const articles = (data?.articles || []).sort(
    (a, b) => (b.score ?? 0) - (a.score ?? 0)
  );

  const maxScore = articles.length > 0
    ? Math.max(...articles.map(a => a.score ?? 0))
    : 0;

  const processedAnswer = useMemo(
    () => processCitations(displayResponse),
    [displayResponse]
  );

  return (
    <div className="mt-8 mb-16">
      {data?.query && (
        <div className="mb-6">
          <p className="text-xs uppercase tracking-wider text-neutral-400 mb-1">
            Query
          </p>
          <p className="text-base font-medium text-neutral-900">
            {data.query}
          </p>
        </div>
      )}

      <div>
        <div className="mb-8">
          {displayResponse && (
            <>
              <h2 className="text-sm font-semibold text-neutral-900 mb-4">
                Answer
              </h2>
              <div className="border-l-2 border-primary-200 pl-4">
              <div className="prose prose-sm max-w-none text-neutral-700">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    a: CitationLink,
                  }}
                >
                  {processedAnswer}
                </ReactMarkdown>
              </div>
            </div>
          </>
          )}

          {loading && !displayResponse && (
            <div className="flex items-center gap-2 text-sm text-neutral-400">
              <PhasedLoading hasArticles={articles.length > 0} useLlm={useLlm} />
            </div>
          )}
        </div>

        {articles.length > 0 && (
          <div>
            <h2 className="text-sm font-semibold text-neutral-900 mb-3">
              Referenced Articles
              <span className="ml-1.5 text-sm font-normal text-neutral-400">
                ({articles.length})
              </span>
            </h2>
            <div className="space-y-3">
              {articles.map((article, index) => (
                <ArticleCard
                  key={article.doc_id || index}
                  article={article}
                  maxScore={maxScore}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResultDisplay;
