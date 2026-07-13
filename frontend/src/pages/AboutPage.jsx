import Card from '../components/ui/Card';

export default function AboutPage() {
  return (
    <main className="mx-auto mt-12 max-w-2xl px-4">
      <h1 className="text-lg font-semibold text-neutral-900 mb-6">About</h1>
      <Card>
        <div className="prose text-sm">
          <p>
            Constitutional Assistant is a Retrieval-Augmented Generation (RAG)
            system that answers natural-language questions about the
            Constitution of Nepal (2072 / 2015).
          </p>
          <p>
            Users ask legal questions in plain English and receive ranked
            constitutional provisions from a hybrid search engine, along with
            optional LLM-generated answers grounded strictly in the retrieved
            articles.
          </p>
          <p className="text-neutral-500 text-xs mt-6">
            Built by Ronish Ghimire, Devraj Khatiwada, and Nayan Nepal.
          </p>
        </div>
      </Card>
    </main>
  );
}
