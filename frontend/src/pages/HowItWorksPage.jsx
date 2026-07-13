import Card from '../components/ui/Card';

const steps = [
  {
    title: 'Ask a Question',
    desc: 'Type a legal question in plain English \u2014 for example, "What is the right to privacy?"',
  },
  {
    title: 'Retrieve Provisions',
    desc: 'The hybrid search engine (BM25 + term proximity + title boost) finds the most relevant constitutional articles.',
  },
  {
    title: 'LLM Answer (optional)',
    desc: 'Toggle the AI answer on to get a citation-backed response, grounded in the retrieved articles.',
  },
  {
    title: 'Explore Results',
    desc: 'Expand each article to see the full provision text and relevance score.',
  },
];

export default function HowItWorksPage() {
  return (
    <main className="mx-auto mt-12 max-w-2xl px-4">
      <h1 className="text-lg font-semibold text-neutral-900 mb-6">
        How It Works
      </h1>
      <div className="space-y-3">
        {steps.map((step, i) => (
          <Card key={i}>
            <div className="flex gap-3">
              <span className="shrink-0 flex h-6 w-6 items-center justify-center rounded bg-primary-100 text-xs font-semibold text-primary-600 mt-0.5">
                {i + 1}
              </span>
              <div>
                <h2 className="text-sm font-semibold text-neutral-900">
                  {step.title}
                </h2>
                <p className="mt-1 text-sm text-neutral-600 leading-relaxed">
                  {step.desc}
                </p>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </main>
  );
}
