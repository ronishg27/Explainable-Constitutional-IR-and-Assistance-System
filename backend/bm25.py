import math

from backend.text_processing import tokenize


class BM25:
	def __init__(self, documents, k1=1.5, b=0.75):
		self.documents = documents
		self.k1 = k1
		self.b = b
		self.avgdl = sum(len(doc["text"].split()) for doc in documents) / len(documents)
		self.index = self._build_index()
		self.doc_lengths = {doc["doc_id"]: len(doc["text"].split()) for doc in documents}
		self.N = len(documents)

	def _build_index(self):
		index = {}
		for doc in self.documents:
			tokens = tokenize(doc["text"])
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
