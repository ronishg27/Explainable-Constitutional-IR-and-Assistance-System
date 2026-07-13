Algorithm Retrieve(query, recall_k, top_k)
Input:
    query: string
    recall_k: integer (default 30)
    top_k: integer (default 8)
Output:
    List of (doc_id, score, metadata) sorted descending by score

--- Phase 1: High-Recall Search (SearchEngine) ---

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
14.     scored.append( (final, bm25, prox, title_matches, doc) )
15. sort scored descending by final
16. return top recall_k entries with metadata

--- Phase 2: Reranking (Reranker) ---

17. results ← output of Phase 1

Stage 2a — RRF Fusion:
18. for each doc in results:
19.     bm25_rank    ← position in sorted-by-bm25 list
20.     prox_rank    ← position in sorted-by-proximity list
21.     title_rank   ← position in sorted-by-title-match list
22.     rrf_score    ← 1/(k + bm25_rank) + 1/(k + prox_rank) + 1/(k + title_rank)
23. sort results by rrf_score descending

Stage 2b — MMR Diversity:
24. selected   ← [results[0]]  (pick highest RRF)
25. candidates ← results[1:]
26. while candidates not empty:
27.     for each cand in candidates:
28.         mmr ← lambda * cand.rrf_score - (1-lambda) * max_similarity(cand, selected)
29.     move candidate with highest mmr to selected
30. results ← selected

Stage 2c — Rule-Based Boost:
31. for each doc in results:
32.     multiplier ← doc.boost * part_rules[doc.part_no] * level_rules[doc.level]
33.     doc.score ← doc.score * multiplier
34. sort results by score descending
35. return top top_k entries
