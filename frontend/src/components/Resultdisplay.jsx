import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Accordion from './ui/Accordion';
import Badge from './ui/Badge';
import Spinner from './ui/Spinner';

const TITLE_BOOST_WEIGHT = 5.0;

const ScoreSummary = ({ score, bm25, proximity, titleMatchCount, boostMultiplier, maxScore }) => {
  const [expanded, setExpanded] = useState(false);

  const pct = maxScore > 0 ? Math.round((score / maxScore) * 100) : 0;

  let label, dotColor, textColor;
  if (pct >= 70) {
    label = 'High'; dotColor = 'bg-green-500'; textColor = 'text-green-700';
  } else if (pct >= 40) {
    label = 'Medium'; dotColor = 'bg-amber-500'; textColor = 'text-amber-700';
  } else {
    label = 'Low'; dotColor = 'bg-neutral-400'; textColor = 'text-neutral-500';
  }

  const titleBoost = (titleMatchCount ?? 0) * TITLE_BOOST_WEIGHT;
  const boost = boostMultiplier ?? 1.0;

  const breakdownRows = [
    { label: 'BM25', value: bm25 },
    { label: 'Proximity', value: proximity },
    { label: 'Title boost', value: titleBoost, hint: titleMatchCount != null ? `${titleMatchCount} term${titleMatchCount !== 1 ? 's' : ''} × ${TITLE_BOOST_WEIGHT}` : undefined },
  ];

  if (boost !== 1.0) {
    breakdownRows.push({ label: 'Boost', value: `×${Number(boost).toFixed(2)}` });
  }

  return (
    <div className="text-xs leading-relaxed">
      <div className="flex items-center gap-2 mb-1">
        <span className={`inline-block w-2 h-2 rounded-full ${dotColor}`} />
        <span className={`font-semibold ${textColor}`}>{label}</span>
        <span className="font-medium text-neutral-400">{pct}%</span>
      </div>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 bg-transparent border-none cursor-pointer text-neutral-400 hover:text-neutral-600 transition-colors text-xs p-0"
      >
        <span>Why this result?</span>
        <span className={`inline-block transition-transform ${expanded ? 'rotate-180' : ''}`}>▾</span>
      </button>
      {expanded && (
        <div className="mt-2 space-y-0.5 border-t border-neutral-200 pt-2">
          {breakdownRows.map(
            (row) =>
              row.value !== undefined && (
                <div key={row.label} className="flex items-center justify-between">
                  <span className="text-neutral-500">{row.label}</span>
                  <span className="font-medium text-neutral-700 tabular-nums">
                    {typeof row.value === 'string' ? row.value : Number(row.value).toFixed(2)}
                    {row.hint && (
                      <span className="ml-1 font-normal text-neutral-400">
                        ({row.hint})
                      </span>
                    )}
                  </span>
                </div>
              ),
          )}
          <div className="border-t border-neutral-200 mt-1 pt-0.5 flex items-center justify-between font-medium">
            <span className="text-neutral-600">Total</span>
            <span className="text-neutral-900 tabular-nums">
              {score != null ? Number(score).toFixed(2) : '-'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

const HighlightText = ({ text, terms, exactTerms }) => {
  if (!terms || terms.length === 0 || !text) return text;

  const exactSet = new Set((exactTerms || []).map(t => t.toLowerCase()));
  const allSet = new Set(terms.map(t => t.toLowerCase()));

  const escaped = terms.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const pattern = new RegExp(`(${escaped.join('|')})`, 'gi');
  const parts = text.split(pattern);

  return parts.map((part, i) => {
    const lower = part.toLowerCase();
    if (exactSet.has(lower)) {
      return <mark key={i} className="bg-yellow-300 rounded px-0.5">{part}</mark>;
    }
    if (allSet.has(lower)) {
      return <mark key={i} className="bg-yellow-100 rounded px-0.5">{part}</mark>;
    }
    return part;
  });
};

const ArticleContent = ({ article, maxScore }) => {
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

      {article.score != null && (
        <ScoreSummary
          score={article.score}
          bm25={article.bm25_score}
          proximity={article.proximity_score}
          titleMatchCount={article.title_match_count}
          boostMultiplier={article.boost_multiplier}
          maxScore={maxScore}
        />
      )}

      <div>
        <p className="text-sm text-neutral-700 leading-relaxed whitespace-pre-line">
          <HighlightText
            text={showFull && hasFullText ? article.full_text : article.text}
            terms={article.matched_terms}
            exactTerms={article.exact_matched_terms}
          />
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

  const articles = (data?.articles || []).sort(
    (a, b) => (b.score ?? 0) - (a.score ?? 0)
  );

  const maxScore = articles.length > 0
    ? Math.max(...articles.map(a => a.score ?? 0))
    : 0;

  const accordionItems = articles.map((article, index) => ({
    id: article.doc_id || index,
    title: article.title,
    subtitle: article.citation,
    content: <ArticleContent article={article} maxScore={maxScore} />,
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
