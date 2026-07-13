import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Accordion from './ui/Accordion';
import Badge from './ui/Badge';
import Spinner from './ui/Spinner';

const TITLE_BOOST_WEIGHT = 5.0;

const ScoreTable = ({ bm25, proximity, titleMatchCount, total }) => {
  const titleBoost = (titleMatchCount ?? 0) * TITLE_BOOST_WEIGHT;

  const rows = [
    { label: 'BM25', value: bm25 },
    { label: 'Proximity', value: proximity },
    { label: 'Title boost', value: titleBoost, hint: titleMatchCount != null ? `${titleMatchCount} term${titleMatchCount !== 1 ? 's' : ''} × ${TITLE_BOOST_WEIGHT}` : undefined },
  ];

  return (
    <div className="text-xs leading-relaxed">
      <p className="font-medium text-neutral-500 mb-1">Score</p>
      <div className="space-y-0.5">
        {rows.map(
          (row) =>
            row.value !== undefined && (
              <div key={row.label} className="flex items-center justify-between">
                <span className="text-neutral-600">{row.label}</span>
                <span className="font-medium text-neutral-800 tabular-nums">
                  {Number(row.value).toFixed(2)}
                  {row.hint && (
                    <span className="ml-1 font-normal text-neutral-400">
                      ({row.hint})
                    </span>
                  )}
                </span>
              </div>
            ),
        )}
      </div>
      <div className="border-t border-neutral-300 mt-1 pt-0.5 flex items-center justify-between font-medium">
        <span className="text-neutral-700">Total</span>
        <span className="text-neutral-900 tabular-nums">
          {total != null ? Number(total).toFixed(2) : '-'}
        </span>
      </div>
    </div>
  );
};

const ArticleContent = ({ article }) => {
  const [showFull, setShowFull] = useState(false);
  const hasFullText =
    article.full_text &&
    article.full_text !== article.text;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {article.article_no && (
          <Badge>Article {article.article_no}</Badge>
        )}
      </div>

      {(article.bm25_score !== undefined || article.proximity_score !== undefined || article.title_match_count !== undefined) && (
        <ScoreTable
          bm25={article.bm25_score}
          proximity={article.proximity_score}
          titleMatchCount={article.title_match_count}
          total={article.score}
        />
      )}

      <div>
        <p className="text-sm text-neutral-700 leading-relaxed whitespace-pre-line">
          {showFull && hasFullText ? article.full_text : article.text}
        </p>
        {hasFullText && (
          <button
            onClick={() => setShowFull(!showFull)}
            className="mt-2 text-xs text-primary-600 hover:text-primary-700 transition-colors bg-transparent border-none cursor-pointer"
          >
            {showFull ? 'Show truncated version' : 'Show full article'}
          </button>
        )}
      </div>
    </div>
  );
};

const ResultDisplay = ({ data, loading, streamedResponse }) => {
  const displayResponse = streamedResponse || data?.response || '';

  const articles = data?.articles || [];

  const accordionItems = articles.map((article, index) => ({
    id: article.doc_id || index,
    title: article.title,
    subtitle: article.citation,
    content: <ArticleContent article={article} />,
  }));

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

      <div className="md:grid md:grid-cols-5 md:gap-8">
        <div className="md:col-span-3 mb-8 md:mb-0">
          {displayResponse && (
            <>
              <h2 className="text-sm font-semibold text-neutral-900 mb-3">
                Answer
              </h2>
              <div className="border-l-2 border-neutral-200 pl-4">
                <div className="prose text-sm leading-relaxed text-neutral-700">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {displayResponse}
                  </ReactMarkdown>
                </div>
              </div>
            </>
          )}

          {loading && !displayResponse && articles.length > 0 && (
            <div className="flex items-center gap-2 text-sm text-neutral-400">
              <Spinner size="sm" />
              Generating answer...
            </div>
          )}

          {loading && !displayResponse && articles.length === 0 && (
            <div className="flex items-center gap-2 text-sm text-neutral-400">
              <Spinner size="sm" />
              Retrieving articles...
            </div>
          )}
        </div>

        {articles.length > 0 && (
          <div className="md:col-span-2">
            <h2 className="text-sm font-semibold text-neutral-900 mb-3">
              Referenced Articles
              <span className="ml-1.5 text-sm font-normal text-neutral-400">
                ({articles.length})
              </span>
            </h2>
            <Accordion items={accordionItems} />
          </div>
        )}
      </div>
    </div>
  );
};

export default ResultDisplay;
