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

const PhasedLoading = ({ useLlm, hasArticles }) => {
  if (!useLlm) {
    return (
      <div className="flex items-center gap-2.5 text-sm text-neutral-400">
        <Spinner size="sm" />
        <span className="animate-pulse">Analyzing relevant articles...</span>
      </div>
    );
  }

  if (!hasArticles) {
    return (
      <div className="flex items-center gap-2.5 text-sm text-neutral-400">
        <Spinner size="sm" />
        <span className="animate-pulse">Searching the constitution...</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2.5 text-sm text-neutral-400">
      <Spinner size="sm" />
      <span className="animate-pulse">Generating answer...</span>
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
    <div className="mt-10 mb-20">
      {data?.query && (
        <div className="mb-8 pb-6 border-b border-neutral-200">
          <p className="text-xs uppercase tracking-widest text-neutral-400 mb-1.5 font-medium">
            Query
          </p>
          <p className="text-lg font-semibold text-neutral-900 leading-snug">
            {data.query}
          </p>
        </div>
      )}

      <div className=" bg-red-0 ">
        <div className="min-w-1">
          {(displayResponse || loading) && (
            <div className="bg-white rounded-3xl border border-neutral-200 shadow-soft p-8 mb-8">
              {displayResponse ? (
                <>
                  <div className="flex items-center gap-3 mb-6 flex-wrap">
                    <h2 className="text-sm font-semibold text-neutral-900 uppercase tracking-widest">
                      Answer
                    </h2>
                    <span className="text-xs text-neutral-400">
                      Based on {articles.length} relevant article{articles.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                  <div className="prose max-w-none text-neutral-700">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        a: CitationLink,
                      }}
                    >
                      {processedAnswer}
                    </ReactMarkdown>
                  </div>
                </>
              ) : (
                <PhasedLoading
                  useLlm={useLlm}
                  hasArticles={articles.length > 0}
                />
              )}
            </div>
          )}
        </div>

        {articles.length > 0 && (
          <div className="md:sticky md:top-20 md:self-start">
            <h2 className="text-xs uppercase tracking-widest text-neutral-400 font-semibold mb-4">
              Referenced Articles
              <span className="ml-1.5 font-normal">({articles.length})</span>
            </h2>
            <div className="space-y-4">
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
