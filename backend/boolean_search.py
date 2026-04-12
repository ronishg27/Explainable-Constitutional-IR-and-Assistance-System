import math

from backend.text_processing import tokenize


def build_inverted_index(documents):
	index = {}
	for doc in documents:
		tokens = tokenize(doc["text"])
		for token in tokens:
			if token not in index:
				index[token] = {}
			doc_id = doc["doc_id"]
			index[token][doc_id] = index[token].get(doc_id, 0) + 1
	return index


def boolean_search(query, index, docs):
	tokens = tokenize(query)
	if not tokens:
		return []

	if tokens[0] not in index:
		return []
	result_set = set(index[tokens[0]].keys())

	for token in tokens[1:]:
		if token not in index:
			return []
		result_set = result_set.intersection(set(index[token].keys()))
		if not result_set:
			return []

	return [doc for doc in docs if doc["doc_id"] in result_set]


def score_documents(query, index, docs):
	tokens = tokenize(query)
	total_docs = len(docs)
	scores = {}

	for token in tokens:
		if token not in index:
			continue
		idf = math.log(total_docs / len(index[token]))
		for doc_id, tf in index[token].items():
			scores[doc_id] = scores.get(doc_id, 0) + (tf * idf)

	sorted_doc_ids = sorted(scores.keys(), key=lambda d: scores[d], reverse=True)
	ranked_results = []
	for doc_id in sorted_doc_ids:
		doc = next(d for d in docs if d["doc_id"] == doc_id)
		doc_copy = doc.copy()
		doc_copy["score"] = scores[doc_id]
		ranked_results.append(doc_copy)
	return ranked_results
