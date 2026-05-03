Algorithm Retrieve(query, top_k)
Input:
    query: string
    top_k: integer
Output:
    List of (doc_id, score, metadata) sorted descending by score

1.  bm25_tokens   ← TextProcessor.process(query, lemmatize=true, remove_stopwords=true)
2.  raw_tokens    ← TextProcessor.process(query, lemmatize=false, remove_stopwords=false)
3.  candidates    ← empty set
4.  for each token in bm25_tokens:
5.      candidates.addAll( tf_index[token].keys() )
6.  query_pairs   ← ProximityScorer.generate_query_pairs(raw_tokens)
7.  scored        ← empty list
8.  for each doc in documents where doc.doc_id in candidates:
9.      bm25       ← BM25Scorer.score(bm25_tokens, doc.doc_id)
10.     if bm25 == 0: continue
11.     title_bonus ← |bm25_tokens ∩ title_tokens[doc.doc_id]| * TITLE_BOOST
12.     prox_score ← ProximityScorer.score(doc.doc_id, query_pairs, max_window=30)
13.     final      ← bm25 + title_bonus + PROXIMITY_WEIGHT * prox_score
14.     scored.append( (final, doc) )
15. sort scored descending by final
16. return top_k entries with metadata