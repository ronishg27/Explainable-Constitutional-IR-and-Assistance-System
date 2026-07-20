# Code Review — Staff Engineer Review

Reviewing the three most important modules: `search_engine.py`, `reranker.py`, and `rag_repository.py`.

---

## `search_engine.py` — Review

### Why it is written this way

The `SearchEngine` follows a **pipeline** pattern — each step (tokenize → expand → generate candidates → score → format) is a separate method. The constructor pre-computes what can be pre-computed (title tokens) and accepts all dependencies via injection.

**Alternative considered:** Making each signal scorer a mixin that `SearchEngine` inherits from. Rejected because it would couple the scoring algorithms to the orchestration — current design keeps each scorer independently testable.

### Tradeoffs

| Decision | Pro | Con |
|----------|-----|-----|
| Pre-computed title tokens | Fast per-query title boost (O(1) lookup) | ~700 docs × 5 tokens = negligible memory, but doesn't adapt to runtime changes (not needed) |
| Candidate set = union of all term postings | High recall — no document is missed if it has any query term | Large candidate sets for common terms (e.g., "right" → hundreds of docs scored) |
| Single `_score_document` returns 7-element tuple | One pass over candidates, all signals computed | Unreadable magic-index destructuring in `_format_results` (tuple[5] for Document, tuple[6] for matched_terms, etc.) |
| `query` → two separate tokenizations (BM25 + proximity) | Optimal configuration for each signal | Double-tokenization could be cached if performance-critical |

### Hidden assumptions

- Title tokens are pre-computed with the BM25 processor (lemmatized, stopwords removed). If a query term is a stopword (e.g., "right **to** education"), it will never match in the title because "to" is removed from `bm25_tokens` and wasn't in `title_tokens`. But since stopwords are removed from BM25 tokens, they're also removed from title tokens — consistency is maintained.
- `bm25_processor.process_text()` and `proximity_processor.process_text()` both use the same spaCy pipeline under the hood. If spaCy behaves differently between calls (e.g., model reload), the two tokenizations could diverge. In practice this doesn't happen because the model is loaded once at startup.

### Clever ideas

- **Dual matched_terms tracking:** `matched_terms` (lemmatized, from BM25 tokens) for scoring analysis and `exact_matched_terms` (original query tokens) for frontend highlighting. The frontend can highlight exactly what the user typed, while the backend uses standardized lemmas.
- **Early exit on zero BM25:** If BM25 returns 0.0, the document is skipped entirely — no proximity scoring or title boost is computed. This is a significant optimization for long-tail candidates that have no real BM25 match.

### Possible bugs

- `_generate_candidates()` collects doc_ids from `tf_index[token].keys()` for each token. If `tf_index` has a token with no postings (empty dict), `.keys()` returns an empty view — no error, but no candidates added. This shouldn't happen with a valid index.
- `_score_document` line 168: `set(bm25_tokens) & set(self.title_tokens[doc.doc_id])`. If `doc.doc_id` is not in `self.title_tokens` (which would happen only if documents were added after construction), this raises `KeyError`. The constructor populates `title_tokens` from `self.documents`, so this is safe as long as the document list and SearchEngine are consistent.

### Performance implications

- **Scoring loop:** For `recall_k=50` candidates, the loop runs 50 iterations. Each iteration does BM25 scoring (O(q) for q query terms), title boost (set intersection), and proximity scoring (O(p) for p pairs). For a 5-token query with synonym expansion to ~15 tokens, this is about 100-200 operations per candidate. Total per query: ~10,000 operations. Well within acceptable range.
- **Candidate generation:** The union set operation runs in O(k) where k is total postings across all tokens. For common terms like "right" and "constitution", this could be 200-300 doc_ids. The union set handles deduplication efficiently.

---

## `reranker.py` — Review

### Why it is written this way

The `Reranker` implements three independent stages (RRF → MMR → boost) as private methods called sequentially from the public `rerank()`. Each stage is composable — they could be rearranged, skipped, or replaced without changing the others.

**Alternative considered:** Using a single formula that combines all three stages into one score. Rejected: three-stage pipeline allows each stage to be tuned independently and makes the mathematical contribution of each stage explicit.

### Tradeoffs

| Decision | Pro | Con |
|----------|-----|-----|
| `rrf_k=60` | Less sensitive to single-rank noise (common in 3-signal fusion) | Higher k dilutes the contribution of strong signals |
| `mmr_lambda=0.5` | Equal weight for relevance and diversity | May over-prioritize diversity over relevance for precision-focused queries |
| BM25 cosine similarity (no embeddings) | Zero ML dependencies, no model download, deterministic | Cannot capture semantic similarity beyond term overlap |
| Unbounded `_vector_cache` | Fast subsequent queries for the same doc_ids | Memory grows with distinct doc_ids seen (for 700 docs, ~700 × avg 20 terms = negligible) |

### Hidden assumptions

- MMR assumes that `rrf_score` (or `score`) is a reasonable measure of query-document relevance. If the original scores from SearchEngine are poorly calibrated (e.g., all scores are within a narrow range), MMR will primarily optimize for diversity and may return irrelevant results.
- The `_vector_cache` assumes the TF index never changes. If the index is rebuilt between queries (it isn't), cached vectors would be stale.

### Clever ideas

- **Static `_apply_boost` method** — it doesn't use `self`, so it could be tested independently or reused in other contexts.
- **Fallback `results.get('rrf_score', results.get('score', 0.0))`** in MMR — if for some reason RRF wasn't called first, MMR still works using the raw `score` from SearchEngine.
- **The `_ranked` helper** inside `_rrf_fuse` is a closure that captures `signal_key` — avoids three copies of the same sorting logic.

### Possible bugs

- `_mmr_diversify` line 103-108: `vec_candidates` and `vec_selected` are recomputed on every iteration of the while loop. This is correct because `candidates` shrinks each iteration, but `vec_selected` grows. The full recomputation is O(r²·t) which is the inherent cost of MMR.
- `_apply_boost` line 156: `result["score"] = score * multiplier`. This overwrites the previous `score`. If `rerank()` is called twice on the same results, scores are multiplied twice. In practice, `rerank()` is called once per query.
- `_cosine_similarity` line 41: `intersection = set(vec_a.keys()) & set(vec_b.keys())`. Creating two sets from dict keys and intersecting them is O(a + b). For small TF vectors this is fine, but for documents with hundreds of unique terms it's wasteful — a `for k, v in vec_a.items(): if k in vec_b` would be O(min(a,b)) with short-circuit.

### Performance implications

- **MMR is O(r²·t):** For r=50 results with t=20 avg unique terms, that's 50² × 20 = 50,000 operations. Acceptable for a single query, but at high concurrency this could become a bottleneck.
- **Vector cache miss:** The first time a doc_id is seen, `_get_tf_vector` traverses the entire `tf_index` (all ~3,000 unique terms × their postings lists). This is expensive but happens only once per doc_id per process lifetime.

---

## `rag_repository.py` — Review

### Why it is written this way

The `RAGRepository` acts as the bridge between the pure IR engine (`RetrievalWorkflow`) and the external LLM (`Ollama`). It owns all LLM-specific concerns: client creation, connectivity caching, retry logic, and prompt-level data transformations (article promotion, context truncation).

**Alternative considered:** Splitting into `LLMClient` (Ollama management) and `ArticleService` (promotion). The current design keeps everything in one class but the responsibilities are clearly separated by method groups (article promotion, retrieval, LLM, context truncation).

### Tradeoffs

| Decision | Pro | Con |
|----------|-----|-----|
| Constructor builds article lookup | Single initialization, fast promotion | Cannot handle runtime corpus changes |
| Lazy Ollama connectivity check | Keeps startup fast | First request pays ~100ms latency |
| Cached `_ollama_available` (never re-checks) | Avoids `/api/tags` call on every request | Won't detect Ollama restart until process restart |
| 3 retries with 0.5s delay | Resilient to transient Ollama failures | 1.5s max additional latency before failure |
| `promote_to_articles` deduplicates by article_no (first wins) | Simple, deterministic | Highest-scoring clause determines article score — lower-scoring clauses of the same article are discarded |

### Hidden assumptions

- `_build_article_lookup()` assumes that documents with `level="article"` have the full article text. Some articles may be stored as a single `level="article"` doc with all sub-clauses included in the text, while others are stored as individual `level="clause"` docs. The code handles both cases, but the distinction depends on the flattening script's output format.
- The article lookup key is `doc.article_no` as a string. If article numbers are not unique across parts (e.g., Part 1 Article 1 and Part 2 Article 1), the lookup would collide. In the Constitution of Nepal, article numbers are unique across the document, so this is safe.

### Clever ideas

- **`_extract_model_names()` handles two response shapes** — Ollama's Python SDK may return a dict or an object depending on the version. The method handles both with `isinstance` checks, making the code resilient to SDK version changes.
- **`build_truncated_text()`** — reduces LLM context by returning only matched clauses. For an article with 10 clauses where only 2 match, the context is 80% smaller. This is important because the LLM context window is 4096 tokens.
- **The `_ENRICHED_RE` regex** strips the "Part X Article Y" header from enriched text, allowing the formatter to present clean clause text to the LLM.

### Possible bugs

- `promote_to_articles` line 196-208: iterates results in their existing order (sorted by descending score). The first occurrence of each `article_no` wins. But if the same article appears at rank 1 and rank 15 with different clause matches, the rank-1 version is kept but its `matched_clauses` may be a subset. This means the context truncation might miss some matching clauses that appeared in lower-ranked results.
- `_build_article_lookup` line 80-85: `defaultdict(lambda: {...})` creates default group dicts with `"article_doc": None`, `"clause_docs": []`. The list is shared across all groups created by the same lambda? No — `defaultdict` calls the lambda each time, so each group gets its own list. This is correct.
- `_clean_body` uses `re.sub(f'^{re.escape(title)}\n*', ...)`. If the title contains regex-special characters (e.g., parentheses), `re.escape` handles them. But the title is compared case-insensitively, while the regex doesn't specify `re.IGNORECASE`. Wait, `_ENRICHED_RE` uses `re.IGNORECASE` for the header, but the title-subtraction regex does not (`re.sub` doesn't use flags). If the title in the text differs in case from the Document's title field, the title won't be stripped. This is likely benign (titles are consistent) but is a subtle inconsistency.

### Performance implications

- `_build_article_lookup()` traverses all ~700 documents, grouping by article_no and concatenating clause texts. This happens once at startup and is fast (~10ms).
- `promote_to_articles()` iterates the promoted results (max 8 after top_k). This is very fast.
- `build_truncated_text()` does a dict lookup + sorted iteration over matched clauses. Negligible cost.
- `call_llm()` network I/O dominates — retry delay is 0.5s, but each Ollama call can take 2-15s depending on model and query complexity.

---

## Common Patterns Across All Files

### Strong engineering demonstrated:
1. **Dependency injection** throughout the IR engine — scorers, processors, and expanders are injected rather than created inside the search engine. This makes unit testing possible without loading JSON files.
2. **Composability** — each pipeline stage (SearchEngine → Reranker → RetrievalWorkflow → RAGRepository → RAGWorkflow) is a separate class with a small public API. They can be tested in isolation or wired in different configurations.
3. **Fallback patterns** — spaCy blank model as fallback (lemmatization degrades to identity), DB-unavailable fallback in JWT decorator, Ollama connectivity caching, fire-and-forget persistence.
4. **No ML dependencies in the core engine** — the entire retrieval and reranking system uses pure Python and standard libraries. No numpy, no sklearn, no embedding models. This makes the system easy to deploy, debug, and audit.

### Areas for improvement:
1. **Tuple indexing** in `_score_document` returns a 7-element tuple that's destructured by position in `_format_results`. A namedtuple or dataclass would be more readable and maintainable.
2. **No type hints** in some methods — `reranker.py` uses generic `dict` consistently, but the exact shapes could be documented.
3. **`_get_tf_vector`** traverses the entire `tf_index` on cache miss. For a corpus with 3,000+ unique terms, this is O(t·d) where t = unique terms and d = docs per term. Could pre-compute all vectors at construction time.
4. **`_mmr_diversify`** computes `vec_candidates` and `vec_selected` lists on every while-loop iteration instead of incrementally updating them.
5. **`_article_lookup`** and `_clause_structure` in `RAGRepository` are built from `retrieval.engine.documents` — this couples RAGRepository to the SearchEngine's document list. If the retrieval pipeline changes (e.g., to an external search service), the article lookup would need a new data source.
