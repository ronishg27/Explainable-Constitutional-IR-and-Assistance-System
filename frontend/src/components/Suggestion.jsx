
import React from 'react';

const Suggestion = ({ setQuery }) => {


  const suggestions = [
    "Can police  take my phone?",
    "Right to free education",
    "Can I be arrested without reason?",
    "Freedom of speech limits",
    
  ];

  return (
    <div className="max-w-2xl mx-auto mt-4 flex flex-wrap justify-center gap-2 px-4">
      {suggestions.map((text, index) => (
        <button
          key={index}
          type="button"
          onClick={() => setQuery(text)}
          className="bg-white rounded-full px-3.5 py-1.5 text-sm text-gray-700 border border-gray-300 hover:bg-blue-100 cursor-pointer shadow-sm transition"
        >
          {text}
        </button>
      ))}
    </div>
  );
};

export default Suggestion;