export default function Suggestion({ setQuery }) {
  const suggestions = [
    'Can police take my phone?',
    'Right to free education',
    'Can I be arrested without reason?',
    'Freedom of speech limits',
  ];

  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {suggestions.map((text, index) => (
        <button
          key={index}
          type="button"
          onClick={() => setQuery(text)}
          className="rounded-md border border-neutral-200 bg-white px-3 py-1.5 text-xs text-neutral-600 hover:border-neutral-300 hover:bg-neutral-50 hover:text-neutral-800 transition-colors cursor-pointer"
        >
          {text}
        </button>
      ))}
    </div>
  );
}
