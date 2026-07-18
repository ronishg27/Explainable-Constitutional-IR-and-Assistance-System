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
    <div className="mt-5">
      <p className="text-[11px] uppercase tracking-widest text-neutral-400 mb-3 font-medium">
        Suggested questions
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {suggestions.map((text, index) => (
          <button
            key={index}
            type="button"
            onClick={() => setQuery(text)}
            className="text-left rounded-xl border border-neutral-200 bg-white px-4 py-3 text-sm text-neutral-600 hover:border-neutral-300 hover:bg-neutral-50 hover:text-neutral-800 transition-all duration-200 cursor-pointer hover:shadow-sm active:scale-[0.99]"
          >
            {text}
          </button>
        ))}
      </div>
    </div>
  );
}
