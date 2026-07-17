export const HighlightText = ({ text, terms, exactTerms }) => {
  if (!terms || terms.length === 0 || !text) return text;

  const exactSet = new Set((exactTerms || []).map(t => t.toLowerCase()));
  const allSet = new Set(terms.map(t => t.toLowerCase()));

  const escaped = terms.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const pattern = new RegExp(`(${escaped.map(t => `\\b${t}\\b`).join('|')})`, 'gi');
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
