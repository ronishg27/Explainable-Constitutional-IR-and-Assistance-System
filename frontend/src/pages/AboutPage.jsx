export default function AboutPage() {
  return (
    <div className="max-w-2xl mx-auto mt-16 px-4">
      <h1 className="text-3xl font-bold text-gray-900 mb-4">About</h1>
      <p className="text-gray-600 leading-relaxed mb-4">
        Constitutional Assistant is a Retrieval-Augmented Generation (RAG) system that answers
        natural-language questions about the Constitution of Nepal (2072 / 2015).
      </p>
      <p className="text-gray-600 leading-relaxed mb-4">
        Users ask legal questions in plain English and receive ranked constitutional provisions
        from a hybrid search engine, along with optional LLM-generated answers grounded strictly
        in the retrieved articles.
      </p>
      <p className="text-gray-600 leading-relaxed">
        Built by Ronish Ghimire, Devraj Khatiwada, and Nayan Nepal.
      </p>
    </div>
  );
}
