# cli.py — interactive search using the production engine
from src.core.engine_factory import EngineFactory

DOCS_PATH = "data/output/flattened_nepal_constitution.json"
INDEX_DIR = "data/output"

engine = EngineFactory.from_artifacts(DOCS_PATH, INDEX_DIR)

print(f"Search engine ready. Type 'exit' to quit.\n")
while True:
    query = input("Query: ").strip()
    if not query or query.lower() == "exit":
        break

    results = engine.search(query, top_k=5)
    if not results:
        print("No results found.\n")
        continue

    print("\nTop results:")
    for rank, res in enumerate(results, start=1):
        print(f"{rank}. [{res['doc_id']}] {res['citation']}  (score={res['score']:.4f})")
        preview = res['text'][:150].replace('\n', ' ')
        print(f"   {preview}...\n")