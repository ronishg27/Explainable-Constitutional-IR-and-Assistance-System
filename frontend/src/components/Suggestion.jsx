export default function Suggestion({ setQuery }) {
  const suggestions = [
    'How is the President of Nepal elected?',
    'What fundamental rights are guaranteed to citizens?',
    'How can a person acquire citizenship of Nepal?',
    'What are the duties and obligations of the State?',
    'What is the structure of the Federal Parliament?',
    'What rights do senior citizens have under the constitution?',
  ];

  return (
    <div className="mt-3">
      <p className="text-xs uppercase tracking-wider text-neutral-400 mb-2">
        Suggested questions
      </p>
      <div className="flex flex-wrap gap-1.5">
        {suggestions.map((text, index) => (
          <button
            key={index}
            type="button"
            onClick={() => setQuery(text)}
            className="rounded-lg border border-neutral-200 bg-white px-2.5 py-1 text-xs text-neutral-500 hover:border-neutral-300 hover:bg-neutral-100 hover:text-neutral-700 transition-colors cursor-pointer"
          >
            {text}
          </button>
        ))}
      </div>
    </div>
  );
}
