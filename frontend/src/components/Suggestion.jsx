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
