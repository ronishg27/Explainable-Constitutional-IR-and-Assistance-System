import React from 'react';

const Resultdisplay = ({ data }) => {
  if (!data) return null; // don't show anything if no data

  return (
    <div
      className="text-white w-full max-w-4xl mx-auto mt-10 px-4 py-4 rounded-lg"
      style={{ backgroundColor: 'hsl(189, 35%, 56%)' }}
    >
      <h2 className="text-xl font-bold mb-3 text-center">
        Results
      </h2>

      <pre className="whitespace-pre-wrap">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
};

export default Resultdisplay;