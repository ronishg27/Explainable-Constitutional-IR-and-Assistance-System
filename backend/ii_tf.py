# inverted index and term frequency

import json
import re
import math

from backend.bm25 import BM25 as BM25Model
from backend.bm25 import search_bm25_with_boost as ranked_search

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
    
    def score_with_boost(self, query_tokens, doc):
        score = 0.0
        # Score Body Text (Weight 1.0)
        score += self.score(query_tokens, doc["doc_id"]) 
        
        # Score Title Text (Weight 5.0) - Simple overlap count
        title_match_count = len(set(query_tokens) & set(doc["title_tokens"]))
        score += title_match_count * 5.0  # Boost factor
        
        return score
    


def tokenize(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = text.split()
    stopwords = {'she', 'thereby', 'government', 'it', 'except'
    ,'made', 'provide', 'case', 'authority', 'tribunals', 'accordance', 'schedule', 'could', 'prescribe', 'person', 'why', 'be', 'a', 'entities', 'judge', 'may', 'wherein', 'any', 'schedules', 'of', 'and', 'their', 'court', 'where', 'article', 'clause', 'them', 'will', 'provision', 'subsection', 'whereupon', 'paragraph', 'thereinbefore', 'your', 'judges', 'statute', 'provides', 'not','no', 'apply', 'including', 'are', 'we', 'party', 'same', 'herein', 'union', 'was', 'prescribed', 'this', 'other', 'laws', 'whereafter', 'stipulations', 'with', 'code', 'provisions', 'deemed', 'rules', 'my', 'shall', 'neither', 'if', 'thereafter', 'provided', 'consistent', 'noting', 'his', 'thereof', 'who', 'another', 'noted', 'chapter', 'include', 'can', 'whereby', 'or', 'each', 'is', 'he', 'state', 'therewith', 'hereunder', 'either', 'deem', 'section', 'at', 'notwithstanding', 'how', 'therein', 'jurisdiction', 'acts', 'in', 'part', 'entity', 'persons', 'what', 'such', 'its', 'whereof', 'wherewith', 'amendments', 'stipulation', 'statutes', 'all', 'have', 'but', 'must', 'to', 'includes', 'her', 'cases', 'the', 'inconsistent', 'every', 'should', 'act', 'by', 'hereto', 'as', 'do', 'on', 'they', 'pursuant', 'subject', 'authorities', 'constitutional', 'our', 'from', 'law', 'hereby', 'hereafter', 'that', 'applies', 'which', 'for', 'amendment', 'constitution', 'regulations', 'an', 'when', 'thereunder', 'herewith', 'has', 'courts', 'parties', 'states', 'tribunal', 'would', 'thereafter', 'whereas', 'thereupon', 'whereinbefore', 'suchlike', 'thereinbefore', 'thereby', 'whereupon', }

    tokens = [token for token in tokens if token not in stopwords]
    return tokens


def build_inverted_index(documents):
    index={}
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
    
    # Find docs containing first token
    if tokens[0] not in index:
        return []
    result_set = set(index[tokens[0]].keys())
    
    # Intersect with remaining tokens
    for token in tokens[1:]:
        if token not in index:
            return []
        result_set = result_set.intersection(set(index[token].keys()))
        if not result_set:
            return []
    
    # Retrieve full document objects
    results = [doc for doc in docs if doc["doc_id"] in result_set]
    return results


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
    
    # Sort doc_ids by score descending
    sorted_doc_ids = sorted(scores.keys(), key=lambda d: scores[d], reverse=True)
    # Retrieve full doc objects
    ranked_results = []
    for doc_id in sorted_doc_ids:
        doc = next(d for d in docs if d["doc_id"] == doc_id)
        doc_copy = doc.copy()
        doc_copy["score"] = scores[doc_id]
        ranked_results.append(doc_copy)
    return ranked_results


def search_bm25(query, bm25_instance, documents, top_k=5):
    """Returns top_k results using BM25 scoring."""
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    
    # Get candidate docs (those containing at least one query term)
    candidate_ids = set()
    for token in query_tokens:
        if token in bm25_instance.index:
            candidate_ids.update(bm25_instance.index[token].keys())
    
    # Score candidates
    scores = []
    for doc in documents:
        if doc["doc_id"] in candidate_ids:
            score = bm25_instance.score(query_tokens, doc["doc_id"])
            if score > 0:
                scores.append((score, doc))
    
    # Sort descending and attach scores
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
            # Base BM25 score from body text
            base_score = bm25_instance.score(query_tokens, doc["doc_id"])
            
            # Title boost: number of query tokens found in title_tokens
            title_match_count = len(set(query_tokens) & set(doc["title_tokens"]))
            boost = title_match_count * title_boost
            
            final_score = base_score + boost
            if final_score > 0:
                scores.append((final_score, doc))
    
    scores.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, doc in scores[:top_k]:
        doc_copy = doc.copy()
        doc_copy["score"] = score
        # Optional: store boost breakdown for transparency
        # doc_copy["base_score"] = base_score
        # doc_copy["title_boost"] = boost
        results.append(doc_copy)
    return results


def main():
    # Load documents once
    with open("data/flattened_constitution.json", "r", encoding="utf-8") as f:
        documents = json.load(f)
    
    # Build inverted index (for TF-IDF or boolean, optional)
    # inverted_index = build_inverted_index(documents)
    
    # Initialize BM25 once (this builds its internal index)
    print("Initializing BM25 index...")
    bm25 = BM25Model(documents)
    print(f"Indexed {len(documents)} documents. Avg doc length: {bm25.avgdl:.1f} words.\n")
    
    print("\n" + "="*60)
    print("   NEPAL CONSTITUTION ASSISTANT - LEGAL SEARCH ENGINE")
    print("="*60)
    print("Type a query or article number. Type 'exit' to quit.\n")
    
    while True:
        query = input("🔍 Search> ").strip()
        if query.lower() == "exit":
            break
        if not query:
            continue
        
        # Direct article number lookup
        if query.isdigit():
            art_no = int(query)
            matches = [d for d in documents if d["article_no"] == art_no]
            if matches:
                print(f"\n📜 Article {art_no}: {matches[0]['title']}")
                for m in matches:
                    print(f"   {m['citation']}")
                    print(f"   {m['text'][:300]}...\n")
            else:
                print(f"\n❌ Article {art_no} not found in Part 3.\n")
            continue
        
        # BM25 Ranked search
        results = ranked_search(query, bm25, documents)
        
        if not results:
            print("\n❌ No relevant constitutional provisions found.\n")
            continue
        
        print(f"\n📋 Top Results for '{query}':\n")
        for i, res in enumerate(results):
            print(f"{i+1}. [BM25 Score: {res['score']:.3f}] {res['citation']}")
            print(f"   {res['text'][:200]}...\n")


if __name__ == "__main__":
    main()