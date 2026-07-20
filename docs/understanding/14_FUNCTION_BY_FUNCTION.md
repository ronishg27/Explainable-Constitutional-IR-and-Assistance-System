# Function-by-Function: `backend/src/core/search_engine.py`

This is the central retrieval pipeline — the single most important file in the IR engine. Every Q&A request flows through `SearchEngine.search()`.

---

## `SearchEngine.__init__(...)`

| | |
|---|---|
| **Why it exists** | Accepts all dependencies via injection — BM25 scorer, proximity scorer, two text processors, document list, tunable constants, optional synonym expander. Also pre-computes title token vectors for all documents. |
| **Inputs** | `bm25_scorer`, `proximity_scorer`, `bm25_processor`, `proximity_processor`, `documents: list[Document]`, `proximity_weight=1.0`, `title_boost=5.0`, `default_top_k=5`, `max_window=30`, `synonym_expander=None` |
| **Outputs** | None (constructor) |
| **Preconditions** | All scorers and processors must be initialized; `documents` must be non-empty; indexes must be loaded into scorers |
| **Postconditions** | `self.title_tokens` populated for every doc (keyed by `doc_id`) |
| **Side effects** | Pre-tokenizes every document's title with `bm25_processor.process_text()` — O(n) where n = ~700 docs. Happens once at startup. |
| **Time complexity** | O(n·m) where n = docs, m = avg title length |
| **Space complexity** | O(n·m) — `title_tokens` dict stores token lists for all documents |
| **Called by** | `EngineFactory.from_artifacts()` |
| **Calls into** | `bm25_processor.process_text()` per document |

**Example:**
```python
# title_tokens for a document
doc.doc_id = "3_31"
doc.title = "Right relating to education"
# After __init__:
self.title_tokens["3_31"] = ["right", "relate", "education"]
# (lemmatized, stopwords removed)
```

---

## `SearchEngine.search(query, top_k, proximity_weight, title_boost)`

| | |
|---|---|
| **Why it exists** | The single public entry point for hybrid retrieval. Orchestrates the full Phase 1 pipeline. |
| **Inputs** | `query: str` — user question (e.g., "What are fundamental rights?"), `top_k: Optional[int]` (default = `self.default_top_k`), `proximity_weight: Optional[float]`, `title_boost: Optional[float]` |
| **Outputs** | `list[dict]` — scored documents with keys: `doc_id`, `part_no`, `article_no`, `title`, `text`, `citation`, `level`, `clause_no`, `subclause_id`, `score`, `bm25_score`, `proximity_score`, `title_match_count`, `boost`, `matched_terms`, `exact_matched_terms` |
| **Preconditions** | `query` must be a non-empty string. Valid scorers must be loaded. |
| **Postconditions** | Returns top-k results sorted by descending combined score. Returns empty list if no tokens generated or no candidates found. |
| **Side effects** | None |
| **Time complexity** | O(t·c + c·s) where t = query tokens, c = candidates, s = signals per candidate (BM25 + proximity + title) |
| **Space complexity** | O(c) — stores scored results for all candidates |
| **Called by** | `RetrievalWorkflow.retrieve()` on every Q&A request |
| **Calls into** | `bm25_processor.process_text()`, `synonym_expander.expand()`, `_prepare_proximity_query()`, `ProximityScorer.generate_query_pairs()`, `_generate_candidates()`, `_score_document()`, `_format_results()` |

**Example:**
```python
engine.search("right to education", top_k=5)
# Returns top 5 scored dicts, e.g.:
# [
#   {"doc_id": "3_31", "title": "Right relating to education", "score": 45.2, ...},
#   {"doc_id": "3_30", "title": "Right regarding freedom", "score": 32.1, ...},
# ]
```

---

## `SearchEngine._prepare_proximity_query(query)`

| | |
|---|---|
| **Why it exists** | Tokenizes the query for proximity scoring — no lemmatization, stopwords kept. This preserves the exact phrase structure needed for proximity analysis. |
| **Inputs** | `query: str` |
| **Outputs** | `list[str]` — raw tokens (e.g., `"right to education"` → `["right", "to", "education"]`) |
| **Preconditions** | `proximity_processor` must be configured with `use_lemmatization=False, remove_stopwords=False` |
| **Postconditions** | Tokens retain stopwords; no lemmatization applied |
| **Side effects** | None |
| **Time complexity** | O(len(query)) |
| **Called by** | `search()` — once per query |
| **Calls into** | `self.proximity_processor.process_text()` → normalizes → splits |

---

## `SearchEngine._generate_candidates(bm25_tokens)`

| | |
|---|---|
| **Why it exists** | Produces a candidate document set by taking the union of all documents that contain at least one query token in the BM25 TF index. This is the recall-focused first pass. |
| **Inputs** | `bm25_tokens: list[str]` — expanded query tokens |
| **Outputs** | `set[str]` — set of `doc_id` strings matching at least one token |
| **Preconditions** | `self.bm25_scorer.tf_index` must be populated |
| **Postconditions** | Every document that matches any query term is included |
| **Side effects** | None |
| **Time complexity** | O(t·p) where t = unique query tokens, p = avg postings per token. Union is set union, O(k) for k doc_ids. |
| **Space complexity** | O(k) where k = total unique doc_ids across all term postings |
| **Called by** | `search()` — once per query |
| **Calls into** | `self.bm25_scorer.tf_index` dict lookups |

**Example:**
```python
# For query "fundamental right":
# tf_index["fundamental"] = {"1_1": 2, "3_31": 1, ...}
# tf_index["right"] = {"3_31": 1, "3_30": 2, ...}
# → candidates = {"1_1", "3_31", "3_30", ...}
```

---

## `SearchEngine._score_document(doc, bm25_tokens, original_tokens, query_pairs, title_boost, proximity_weight)`

| | |
|---|---|
| **Why it exists** | Computes the triple-signal score for a single candidate document. This is the inner loop of the retrieval pipeline. |
| **Inputs** | `doc: Document`, `bm25_tokens: list[str]` (expanded, lemmatized), `original_tokens: list[str]` (base, no synonym expansion), `query_pairs: list[tuple]`, `title_boost: float`, `proximity_weight: float` |
| **Outputs** | `tuple[float, float, float, int, Document, list[str], list[str]]` — `(final_score, bm25_score, proximity_score, title_match_count, doc, matched_terms, exact_matched_terms)` |
| **Preconditions** | Doc must be in the candidate set. `doc.doc_id` must exist in BM25 index, title_tokens, and positional index. |
| **Postconditions** | If BM25 score is 0.0, returns all-zeros tuple (early exit — no further scoring). Otherwise, returns combined score with all components. |
| **Side effects** | None |
| **Time complexity** | O(q + p) where q = query tokens (BM25 + matched_terms) and p = query pairs (proximity). BM25: O(q), matched_terms: O(q), title boost: O(q), proximity: O(p) |
| **Space complexity** | O(1) — returns a tuple of fixed size |
| **Called by** | `search()` — once per candidate document |
| **Calls into** | `self.bm25_scorer.score()`, `self.bm25_scorer.matched_terms()`, `self.proximity_scorer.score()` |

**Example:**
```python
# For doc "3_31" (Right relating to education), query "right to education":
# - BM25 score ≈ 12.5 (has "right" and "education")
# - title_match_count = 2 ("right", "education" both in title)
# - title_boost = 5.0
# - proximity score = 0.85 ("right" ... "education" close in text)
# - final = 12.5 + 2*5.0 + 1.0*0.85 = 23.35
```

---

## `SearchEngine._format_results(scored_docs)`

| | |
|---|---|
| **Why it exists** | Converts internal `(score_tuple, Document)` format to a list of API-ready dictionaries. |
| **Inputs** | `scored_docs: list[tuple]` — list of 7-element tuples from `_score_document` |
| **Outputs** | `list[dict]` — each dict contains 16 keys for the API response |
| **Preconditions** | Input is sorted by score descending |
| **Postconditions** | Result list length ≤ input length (no filtering, just format) |
| **Side effects** | None |
| **Time complexity** | O(r) where r = number of results |
| **Space complexity** | O(r) — new dicts for each result |
| **Called by** | `search()` — once per query |
| **Calls into** | None — pure data transformation |

---

## `Reranker.rerank(results, top_k, boost_rules)`

| | |
|---|---|
| **Why it exists** | The single public entry point for Phase 2 reranking. Runs all three stages sequentially. |
| **Inputs** | `results: list[dict]` (output of SearchEngine), `top_k: int = 8`, `boost_rules: Optional[dict]` |
| **Outputs** | `list[dict]` — reranked + top-k truncated results |
| **Preconditions** | Results must have `bm25_score`, `proximity_score`, `title_match_count`, `score`, `doc_id` keys |
| **Postconditions** | Results are reordered and truncated to top_k. Each result gets `rrf_score` and `boost_multiplier` added. |
| **Side effects** | Populates `_vector_cache` |
| **Time complexity** | O(r log r + r²·t) where r = results (~50), t = avg unique terms in TF vectors: RRF sort O(3·r log r), MMR O(r²·t) |
| **Space complexity** | O(r·t) for vector cache |
| **Called by** | `RetrievalWorkflow.retrieve()` — every query |
| **Calls into** | `_rrf_fuse()`, `_mmr_diversify()`, `_apply_boost()` |

---

## `Reranker._rrf_fuse(results)`

| | |
|---|---|
| **Why it exists** | Combines three independent ranking signals (BM25, proximity, title-match) into one fused ranking using Reciprocal Rank Fusion. |
| **Inputs** | `results: list[dict]` |
| **Outputs** | `list[dict]` — sorted by `rrf_score` |
| **Preconditions** | Results must have `bm25_score`, `proximity_score`, `title_match_count` |
| **Postconditions** | `rrf_score` key added to each result dict |
| **Time complexity** | O(r log r) — three sorts of r items + one pass |
| **Calls into** | `sorted()` with `key=lambda x: x.get(signal, 0)` |

**Example:**
```python
# 3 results with their signals:
# Doc A: BM25=10, Prox=0.2, Title=2
# Doc B: BM25=8,  Prox=0.8, Title=0
# Doc C: BM25=6,  Prox=0.5, Title=1
#
# Ranks by BM25: A(1), B(2), C(3)
# Ranks by Prox:  B(1), C(2), A(3)
# Ranks by Title: A(1), C(2), B(3)
#
# k=60:
# A: 1/61 + 1/63 + 1/61 = 0.0492
# B: 1/62 + 1/61 + 1/63 = 0.0488
# C: 1/63 + 1/62 + 1/62 = 0.0480
```

---

## `Reranker._mmr_diversify(results)`

| | |
|---|---|
| **Why it exists** | Reorders results to balance relevance and diversity using Maximal Marginal Relevance. Prevents a single topic from dominating the top-8. |
| **Inputs** | `results: list[dict]` (sorted by RRF score) |
| **Outputs** | `list[dict]` — reordered for diversity |
| **Preconditions** | `rrf_score` (or fallback `score`) must exist |
| **Postconditions** | Selected results are in diversity-aware order |
| **Time complexity** | O(r²·t) — each of r iterations scans the remaining candidates and computes cosine similarity against all selected |
| **Called by** | `rerank()` — Stage 2 |
| **Calls into** | `_get_tf_vector()`, `_cosine_similarity()` |

**Example:**
```python
# After MMR, instead of [A, B, C] (all about fundamental rights),
# might get [A, D, B] where D is about a different topic
# but still relevant:
# MMR(A) = 0.5*0.0492 - 0.5*0 = 0.0246  (first, always picked)
# MMR(B) = 0.5*0.0488 - 0.5*0.3 = 0.0094 (similar to A)
# MMR(D) = 0.5*0.0470 - 0.5*0.05 = 0.0210 (less similar, gets picked second)
```

---

## `Reranker._apply_boost(results, boost_rules)`

| | |
|---|---|
| **Why it exists** | Applies configurable multipliers to final scores — per-document boost, per-part rules, per-level rules. |
| **Inputs** | `results: list[dict]`, `boost_rules: Optional[dict]` with optional `part_boost` and `level_boost` override |
| **Outputs** | `list[dict]` — scores multiplied, `boost_multiplier` added |
| **Preconditions** | `score`, `boost`, `part_no`, `level` keys must exist |
| **Postconditions** | Scores are modified in-place. `boost_multiplier` = `boost * part_rule * level_rule` |
| **Time complexity** | O(r) |
| **Called by** | `rerank()` — Stage 3 |

**Example:**
```python
# Default level rules: article=0.98, clause=0.95, subclause=0.90
# Document: boost=1.0, part_no="3", level="article"
# No part rules override
# multiplier = 1.0 * 1.0 * 0.98 = 0.98
# If part_boost = {"3": 1.2} (boost Fundamental Rights):
# multiplier = 1.0 * 1.2 * 0.98 = 1.176
```

---

## `Reranker._get_tf_vector(doc_id)`

| | |
|---|---|
| **Why it exists** | Builds or retrieves a cached sparse TF vector for a document. Used for BM25 cosine similarity in MMR. |
| **Inputs** | `doc_id: str` |
| **Outputs** | `dict[str, int]` — `{term: term_frequency}` for all terms in the document |
| **Preconditions** | `self.tf_index` must be populated |
| **Postconditions** | Vector is cached in `_vector_cache` (never evicted) |
| **Time complexity** | O(t·d) first call where t = unique terms in corpus, d = documents per term (traverses entire tf_index). O(1) subsequent calls (cache hit). |
| **Called by** | `_mmr_diversify()` — once per unique doc_id per query |

---

## `Reranker._cosine_similarity(vec_a, vec_b)`

| | |
|---|---|
| **Why it exists** | Computes cosine similarity between two sparse TF vectors. Used by MMR to measure document topical similarity. |
| **Inputs** | `vec_a: dict[str, int]`, `vec_b: dict[str, int]` — sparse TF vectors |
| **Outputs** | `float` — cosine similarity (0.0 to 1.0) |
| **Preconditions** | Inputs must be non-empty TF vectors |
| **Postconditions** | Returns 0.0 if no term intersection or zero-norm vectors |
| **Time complexity** | O(min(|A|, |B|)) — dot product over intersection is proportional to the smaller vector's size |
| **Called by** | `_mmr_diversify()` — O(r²) times per query |

**Example:**
```python
# Doc A: {"right": 2, "education": 1, "fundamental": 1}
# Doc B: {"right": 1, "freedom": 2, "speech": 1}
# intersection = {"right"}
# dot = 2*1 = 2
# norm(A) = sqrt(4+1+1) = sqrt(6) ≈ 2.45
# norm(B) = sqrt(1+4+1) = sqrt(6) ≈ 2.45
# cos_sim = 2 / (2.45*2.45) = 2/6 ≈ 0.333
```
