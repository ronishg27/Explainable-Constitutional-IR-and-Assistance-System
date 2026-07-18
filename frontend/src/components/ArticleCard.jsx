import { useState } from 'react';
import { HighlightText } from '../utils/highlight.jsx';

const TITLE_BOOST_WEIGHT = 5.0;

const ScoreBreakdown = ({ score, maxScore }) => {
  const pct = maxScore > 0 ? Math.round((score / maxScore) * 100) : 0;

  let label, dotColor, textColor;
  if (pct >= 70) {
    label = 'High'; dotColor = 'bg-green-500'; textColor = 'text-green-700';
  } else if (pct >= 40) {
    label = 'Medium'; dotColor = 'bg-amber-500'; textColor = 'text-amber-700';
  } else {
    label = 'Low'; dotColor = 'bg-neutral-400'; textColor = 'text-neutral-500';
  }

  return (
    <div className="flex items-center gap-1.5 text-xs">
      <span className={`inline-block w-1.5 h-1.5 rounded-full ${dotColor}`} />
      <span className={`font-semibold ${textColor}`}>{label}</span>
      <span className="font-medium text-neutral-400">{pct}%</span>
    </div>
  );
};

const FullScoreBreakdown = ({ score, bm25, proximity, titleMatchCount, boostMultiplier }) => {
  const titleBoost = (titleMatchCount ?? 0) * TITLE_BOOST_WEIGHT;
  const boost = boostMultiplier ?? 1.0;

  const rows = [
    { label: 'BM25', value: bm25 },
    { label: 'Proximity', value: proximity },
    { label: 'Title boost', value: titleBoost, hint: titleMatchCount != null ? `${titleMatchCount} term${titleMatchCount !== 1 ? 's' : ''} × ${TITLE_BOOST_WEIGHT}` : undefined },
  ];

  if (boost !== 1.0) {
    rows.push({ label: 'Boost', value: `×${Number(boost).toFixed(2)}` });
  }

  return (
    <div className="mt-3 space-y-1 border-t border-neutral-100 pt-3 text-xs">
      <p className="text-xs font-medium text-neutral-500 mb-1.5">Scoring breakdown</p>
      {rows.map(
        (row) =>
          row.value !== undefined && (
            <div key={row.label} className="flex items-center justify-between">
              <span className="text-neutral-400">{row.label}</span>
              <span className="font-medium text-neutral-600 tabular-nums">
                {typeof row.value === 'string' ? row.value : Number(row.value).toFixed(2)}
                {row.hint && (
                  <span className="ml-1 font-normal text-neutral-400">({row.hint})</span>
                )}
              </span>
            </div>
          ),
      )}
      <div className="flex items-center justify-between border-t border-neutral-100 pt-1.5 font-medium">
        <span className="text-neutral-500">Total</span>
        <span className="text-neutral-800 tabular-nums">
          {score != null ? Number(score).toFixed(2) : '-'}
        </span>
      </div>
    </div>
  );
};

export default function ArticleCard({ article, maxScore }) {
  const [expanded, setExpanded] = useState(false);

  const body = article.content;

  return (
    <article
      id={`article-${article.article_no}`}
      className="rounded-xl border border-neutral-200 bg-white shadow-sm transition-shadow hover:shadow-md"
    >
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <h3 className="text-sm font-semibold text-neutral-900 leading-snug">
              {article.title}
            </h3>
            {article.citation && (
              <p className="mt-0.5 text-xs text-neutral-500">{article.citation}</p>
            )}
          </div>
          {article.score != null && (
            <ScoreBreakdown
              score={article.score}
              maxScore={maxScore}
            />
          )}
        </div>

        <div className="mt-2 flex flex-wrap gap-1.5">
          {(article.matched_terms || []).slice(0, 4).map((term, i) => (
            <span
              key={i}
              className="inline-flex items-center rounded-full bg-primary-50 px-2 py-0.5 text-[10px] font-medium text-primary-700"
            >
              {term}
            </span>
          ))}
        </div>

        <div className="mt-3 flex items-center gap-3">
          <button
            onClick={() => setExpanded(!expanded)}
            className="inline-flex items-center gap-1 text-xs font-medium text-primary-600 hover:text-primary-700 transition-colors bg-transparent border-none cursor-pointer focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 rounded"
          >
            <span>{expanded ? 'Show less' : 'View details'}</span>
            <svg
              width="12"
              height="12"
              viewBox="0 0 12 12"
              fill="none"
              className={`transition-transform ${expanded ? 'rotate-180' : ''}`}
            >
              <path
                d="M3 4.5L6 7.5L9 4.5"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>

        <div
          className={`overflow-hidden transition-all duration-300 ease-in-out ${
            expanded ? 'max-h-500 opacity-100 mt-3' : 'max-h-0 opacity-0'
          }`}
        >
          <div className="border-t border-neutral-100 pt-3 space-y-3">
            <p className="text-xs text-neutral-700 leading-relaxed whitespace-pre-line">
              <HighlightText
                text={body}
                terms={article.matched_terms}
                exactTerms={article.exact_matched_terms}
              />
            </p>

            {article.score != null && (
              <FullScoreBreakdown
                score={article.score}
                bm25={article.bm25_score}
                proximity={article.proximity_score}
                titleMatchCount={article.title_match_count}
                boostMultiplier={article.boost_multiplier}
              />
            )}
          </div>
        </div>
      </div>
    </article>
  );
}
