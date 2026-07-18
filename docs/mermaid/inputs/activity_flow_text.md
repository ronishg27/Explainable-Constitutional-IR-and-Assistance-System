## Online Mode (Retrieval)

1. Receive user query
2. NLP processing — two pipelines:
   - BM25: normalization, tokenization, stopword removal, spaCy lemmatization
   - Proximity: normalization, tokenization (raw tokens, stopwords kept)
3. Query expansion (44 synonym groups)
4. Score candidates using: BM25 scoring + Proximity scoring + Title boost (×5)
5. Sort top-50 by combined score
6. Rerank top-8 using: RRF fusion + MMR diversity + Rule-based boost
7. Article promotion (clause→article merge, dedup)
8. If LLM mode: truncate context, format prompt, feed to Ollama, retrieve response
9. Persist to MongoDB
10. Send response to frontend

## Offline Mode (Data Ingestion)

1. Constitution JSON → flattened JSON (nested to flat documents)
2. NLP processing (custom normalization, tokenization, stopword removal, spaCy lemmatization) — two configs:
   - BM25 config: lemmatized, no stopwords
   - Proximity config: raw tokens, stopwords kept
3. Lemma dictionary generation (rule-based lemmatization fallback)
4. Compute statistics: term frequency, document length, average document length
5. Indexing — inverted (tf_index.json) and positional (pos_index.json) saved to files
