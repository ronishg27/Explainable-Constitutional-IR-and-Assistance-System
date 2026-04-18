import json
import math
from pathlib import Path

from text_processing import tokenize


def load_documents(path=None):
	"""Load flattened MVP documents from data/flattened_nepal_constitution_mvp.json."""
	root = Path(__file__).resolve().parents[0]
	if path is None:
		path = root / "data" / "flattened_nepal_constitution_mvp.json"
	else:
		path = Path(path)

	with path.open("r", encoding="utf-8") as f:
		return json.load(f)


class BM25:
	def __init__(self, documents, k1=2, b=0.9):
		self.documents = documents
		self.k1 = k1
		self.b = b
		self.avgdl = sum(len(doc.get("body_tokens", tokenize(doc["text"]))) for doc in documents) / len(documents)
		self.index = self._build_index()
		self.doc_lengths = {
			doc["doc_id"]: len(doc.get("body_tokens", tokenize(doc["text"])))
			for doc in documents
		}
		self.N = len(documents)

	def _build_index(self):
		index = {}
		for doc in self.documents:
			tokens = doc.get("body_tokens", tokenize(doc["text"]))
			doc_id = doc["doc_id"]
			for token in tokens:
				if token not in index:
					index[token] = {}
				index[token][doc_id] = index[token].get(doc_id, 0) + 1
		return index

	def idf(self, term):
		df = len(self.index.get(term, {}))
		if df == 0:
			return 0
		return math.log((self.N - df + 0.5) / (df + 0.5) + 1)

	def score(self, query_tokens, doc_id):
		score = 0.0
		doc_len = self.doc_lengths[doc_id]
		for term in query_tokens:
			if term not in self.index or doc_id not in self.index[term]:
				continue
			tf = self.index[term][doc_id]
			idf = self.idf(term)
			numerator = tf * (self.k1 + 1)
			denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
			score += idf * (numerator / denominator)
		return score

	def score_with_boost(self, query_tokens, doc, title_boost=5.0):
		base_score = self.score(query_tokens, doc["doc_id"])
		title_match_count = len(set(query_tokens) & set(doc.get("title_tokens", [])))
		return base_score + (title_match_count * title_boost)


def search_bm25(query, bm25_instance, documents, top_k=5):
	query_tokens = tokenize(query)
	if not query_tokens:
		return []

	candidate_ids = set()
	for token in query_tokens:
		if token in bm25_instance.index:
			candidate_ids.update(bm25_instance.index[token].keys())

	scores = []
	for doc in documents:
		if doc["doc_id"] in candidate_ids:
			score = bm25_instance.score(query_tokens, doc["doc_id"])
			if score > 0:
				scores.append((score, doc))

	scores.sort(key=lambda x: x[0], reverse=True)
	results = []
	for score, doc in scores[:top_k]:
		doc_copy = doc.copy()
		doc_copy["score"] = score
		results.append(doc_copy)
	return results


def search_bm25_with_boost(query, bm25_instance, documents, title_boost=5.0, top_k=5):
	query_tokens = tokenize(query)
	if not query_tokens:
		return []

	candidate_ids = set()
	for token in query_tokens:
		if token in bm25_instance.index:
			candidate_ids.update(bm25_instance.index[token].keys())

	scores = []
	for doc in documents:
		if doc["doc_id"] in candidate_ids:
			final_score = bm25_instance.score_with_boost(query_tokens, doc, title_boost)
			if final_score > 0:
				scores.append((final_score, doc))

	scores.sort(key=lambda x: x[0], reverse=True)
	results = []
	for score, doc in scores[:top_k]:
		doc_copy = doc.copy()
		doc_copy["score"] = score
		results.append(doc_copy)
	return results


def main():
	documents = load_documents()
	bm25 = BM25(documents)

	print(f"Loaded {len(documents)} documents from flattened_nepal_constitution_mvp.json")
	print(f"Average document length: {bm25.avgdl:.2f} tokens")

	while True:
		query = input("Search query (or type exit): ").strip()
		if not query or query.lower() == "exit":
			break

		results = search_bm25_with_boost(query, bm25, documents)
		if not results:
			print("No results found. Try a different query.")
			continue

		print("\nTop results:")
		for rank, res in enumerate(results, start=1):
			print(f"{rank}. {res['citation']} (score={res['score']:.3f})")
			print(f"   {res['text'][:200].strip()}\n")


if __name__ == "__main__":
	main()
