# Deep Dive — File-by-File Analysis

Each file analyzed below follows the same structure: Purpose → Dependencies → Public API → Internal Structure → Main Algorithms → Important Functions → Design Decisions → Common Pitfalls.

Say "next" to proceed to the next file.

---

## File 1: `backend/src/core/document.py` (22 lines)

**Purpose:** Typed data container for a single constitutional provision in the flattened corpus. Every one of the ~700 documents in the corpus is an instance of this dataclass.

**Dependencies:** None — pure Python `dataclasses`.

**Public API:** The `Document` dataclass with 14 fields. All fields are positional constructor args.

**Internal structure:**
```
doc_id: str              — Unique key (e.g., "1_1_2" for Part 1, Article 1, Clause 2)
part_no: str             — Part number (as string, e.g., "1", "3")
article_no: str          — Article number
title: str               — Article title (e.g., "Right relating to education")
text: str                — Enriched provision text (includes header prefix)
citation: str            — Display citation (e.g., "Part 3, Article 31")
level: str               — "part", "article", "clause", or "subclause"
clause_no: Optional[str] — Clause identifier within an article
subclause_id: Optional[str]
is_primary: bool         — Is this the primary representation of the article?
parent_id: Optional[str]
raw_text: Optional[str]  — Original un-enriched text (if available)
citation_normalized: Optional[str]
boost: float             — Document-level relevance boost multiplier (default 1.0)
```

**Main algorithms:** None — pure data.

**Important functions:** None beyond the constructor.

**Design decisions:**
- `level` as a string rather than an enum — simpler but allows invalid values at runtime.
- `boost` has default 1.0 — documents are equal unless explicitly weighted.
- `raw_text` and `citation_normalized` are Optional — they may be missing from older corpus formats.

**Common pitfalls:**
- `doc_id` uniqueness is not enforced by the dataclass; duplicates in the corpus list cause silent overwrites during index building.
- Mixing string and optional types for `part_no`/`article_no` means consumers must handle type coercion (e.g., in sorting).

---

## File 2: `backend/src/core/text_processor.py` (110 lines)

**Purpose:** NLP pipeline for normalizing, lemmatizing, and filtering text. Two instances exist at runtime with different configurations (BM25 processor vs proximity processor).

**Dependencies:** `constants/contraction_map.py` (57 contractions), `constants/stopwords.py` (~120 stopwords), spaCy (`en_core_web_sm` with fallback to `blank("en")`).

**Public API:**
- `process_text(text: str) -> list[str]` — full pipeline: normalize → lemmatize (optional) → stopword removal (optional)
- `normalize_text(text: str) -> str` — lowercase, expand contractions, alphnumeric+whitespace only
- `lemmatize_tokens(tokens: list[str]) -> list[str]` — spaCy lemmatization
- `_filter_stopwords(tokens)`, `_expand_contractions(text)` — internal steps

**Internal structure:**
```
process_text():
  ├── normalize_text() → lowercase, contractions, char filter
  │     ├── _expand_contractions() → regex substitution from CONTRACTIONS_MAP
  │     └── ''.join(ch for ch if isalnum or isspace)
  ├── split()
  ├── [lemmatize_tokens()] → spaCy pipeline, pron→text fallback
  └── [_filter_stopwords()] → set lookup
```

**Main algorithms:**
- **Contraction expansion:** Compiled regex of 57 contractions sorted by descending length. `\b(couldn't've|...)\b` → lookup in map. Sorting by length ensures longer contractions match before their prefixes.
- **Lemmatization fallback:** If `en_core_web_sm` is not installed, uses `spacy.blank("en")` — tokenization still works but lemmas are identity (no actual lemmatization).

**Important functions:**
- `get_spacy_pipeline()` — module-level singleton. Loads once, caches in `_spacy_nlp`. This is called at app startup explicitly in `app.py:get_spacy_pipeline()` to avoid slow first-request latency.

**Design decisions:**
- Two-processor architecture: BM25 processor (lemmatize ON, stopwords REMOVED) vs proximity processor (lemmatize OFF, stopwords KEPT). This is the single most important design choice — it recognizes that BM25 benefits from conflation ("rights"→"right") while proximity matching needs exact token positions including stopwords to capture phrase structure.
- `-pron-` lemmas are mapped back to the original token text. spaCy uses `-pron-` for pronouns; mapping back preserves the original word.
- Module-level `_spacy_nlp` singleton avoids reloading the spaCy model per request or per TextProcessor instance.

**Common pitfalls:**
- `_expand_contractions` uses `str.replace` operations via regex, not a simple dict lookup. If `CONTRACTIONS_MAP` values contain punctuation, the subsequent `isalnum` filter may strip them.
- spaCy model download is an implicit dependency. If the user runs without `en_core_web_sm`, lemmatization silently degrades (tokens pass through unchanged).
- The static `_pattern` cache on `TextProcessor._build_contraction_pattern()` — it's shared across all instances, which is correct but unusual.

---

## File 3: `backend/src/core/bm25_scorer.py` (46 lines)

**Purpose:** Compute BM25 relevance scores between a query and a document. Primary ranking signal.

**Dependencies:** None — pure Python `math.log`.

**Public API:**
- `score(query_tokens, doc_id) -> float` — BM25 score for a document given query tokens
- `matched_terms(query_tokens, doc_id) -> list[str]` — which query terms exist in the document
- `idf(term) -> float` — inverse document frequency

**Internal structure:**
The constructor takes:
- `tf_index`: `dict[term → dict[doc_id → term_frequency]]`
- `doc_lengths`: `dict[doc_id → token_count]`
- `avgdl`: average document length across the corpus
- `k1` (1.5), `b` (1.0)

**Main algorithms:**

BM25 formula:
```
score(D, Q) = Σ idf(t) * (tf(t,D) * (k1+1)) / (tf(t,D) + k1 * (1 - b + b * |D|/avgdl))

idf(t) = log((N - df(t) + 0.5) / (df(t) + 0.5) + 1)
```

All components are standard BM25 Okapi. Notable: `b=1.0` means full document length normalization — the uncommon choice that penalizes long documents proportionally.

**Important functions:**
- `score()` — iterates query terms, skips terms with tf=0, accumulates with IDF
- `idf()` — edge-case guard: if df==0 returns 0.0 (unseen terms contribute nothing)

**Design decisions:**
- `b=1.0` rather than the conventional 0.75. Legal documents vary hugely in length (titles: 3 words, multi-clause articles: 500+ words). Full normalization prevents verbose articles from dominating short dense provisions purely by term volume.
- No `get_scores()` or batch scoring — each document is scored individually in SearchEngine. This is O(n * m) where n = candidates, m = query terms, but with recall_k=30 it's fast enough.

**Common pitfalls:**
- `doc_len=0` returns 0.0 — division by zero guard.
- `tf=0` is skipped, not added as zero — avoids unnecessary IDF lookups.
- `matched_terms()` uses `get(doc_id, 0) > 0` — checks presence, not count.

---

## File 4: `backend/src/core/proximity.py` (119 lines)

**Purpose:** Score document relevance by how close query term pairs appear in the document text. Captures phrase-level signal that BM25 cannot see.

**Dependencies:** `json`, `pathlib.Path` (for load/save helpers).

**Public API:**
- `score(doc_id, pairs, max_window=30, ordered=True) -> float` — average quadratic inverse proximity score
- `generate_query_pairs(tokens) -> list[tuple[str,str]]` — pair generation heuristic
- `generate_all_pairs(tokens)`, `generate_adjacent_pairs(tokens)` — pair generators
- `load_index(path)`, `save_index(path)` — serialization

**Internal structure:**
The positional index is a nested dict: `term → doc_id → list[positions]`. Each position is a 0-indexed token offset in the document.

**Main algorithms:**

**Pair generation heuristic:**
- ≤ 5 query tokens: all unordered pairs (O(n²/2))
- > 5 query tokens: adjacent pairs only (O(n-1))
This prevents O(n²) blowup for long queries where distant pairs contribute negligible signal.

**Minimum ordered distance (two-pointer sweep):**
```
i=0, j=0
while i < len(pos1) and j < len(pos2):
  if pos1[i] < pos2[j]:
    dist = pos2[j] - pos1[i]
    i++
  else:
    j++
```
Finds the minimum distance where term1 appears *before* term2. For unordered, take `abs(pos1[i] - pos2[j])` and advance the smaller pointer.

**Score per pair:** `1 / (distance + 1)²` — quadratic inverse: close pairs contribute much more than far pairs. A pair at distance 0 scores 1.0; distance 9 scores 0.01.

Average over all valid pairs (pairs where both terms appear in the document within `max_window` tokens).

**Important functions:**
- `_min_ordered_distance()` — the core algorithm. Used by default (ordered=true).
- `_min_distance()` — unordered variant, used when ordered=false.

**Design decisions:**
- **Ordered distance:** By default, term1 must appear before term2. This captures phrase order naturally: "right to education" matches, "education right" does not (unless both orders exist in the text).
- **Max window = 30 tokens:** Pairs separated by more than 30 tokens are discarded. In legal text, related terms rarely appear more than 30 tokens apart within a clause.
- **Pair heuristic threshold at 5 tokens:** Empirical choice. Short queries benefit from full cross-product; beyond 5, adjacent pairs are sufficient.

**Common pitfalls:**
- Equal terms in a pair (`term1 == term2`) are skipped — prevents self-pair scoring.
- If a term is missing from the positional index, the pair is silently skipped (no error).
- `max_window` check happens after distance computation — for very distant pairs, this is wasted work.

---

## File 5: `backend/src/core/query_expander.py` (71 lines)

**Purpose:** Expand query tokens with synonyms from 44 legal synonym groups to improve recall.

**Dependencies:** `json` (loads `data/synonyms.json`).

**Public API:**
- `expand(tokens, raw_query="") -> list[str]` — expanded token list preserving order and uniqueness

**Internal structure:**
Synonym groups are loaded as `data["groups"]` — each group is a list of terms (e.g., `["arrest", "detention", "custody"]`).

`_build_lookup()` creates:
- `self.lookup`: `word → group_idx → set[synonyms]`
- `self.multi_word_entries`: `group_idx → list[multi-word phrases]`

**Main algorithms:**

**Expansion:**
```
for each token:
  add token to result (if not seen)
  if token in lookup:
    for each group containing token:
      if group has multi-word phrases and raw_query doesn't contain them:
        skip this group (don't expand multi-word without evidence)
      add all synonyms from group to result (if not seen)
```

**Multi-word phrase guard:** If a synonym group contains phrases like "right to information", but the user's raw query doesn't contain any such phrase, the group is not expanded. This prevents over-expansion (e.g., expanding "right" to include "right to information" when the user just asked about "rights").

**Design decisions:**
- Only applied to BM25 tokens (not proximity tokens). Synonyms improve recall for BM25 scoring but would break the positional signal if applied to proximity matching.
- Deduplication in `_add_if_new()` uses a set for O(1) lookup while maintaining insertion order.
- Multi-word phrase check is against the *raw query*, not the tokenized version — phrases with stopwords like "right to information" must match the unprocessed query.

**Common pitfalls:**
- `_normalize()` applies the same alpha-only filter as `TextProcessor.normalize_text()` — if a synonym contains digits or special chars, they are stripped.
- Synonym expansion can increase the token count significantly (one token may expand to 10+ synonyms). This expands the candidate set but also increases scoring work.

---

## File 6: `backend/src/core/engine_factory.py` (105 lines)

**Purpose:** Assembles a fully-wired `SearchEngine` from disk artifacts.

**Dependencies:** All `src.core` modules — `Document`, `TextProcessor`, `BM25Scorer`, `ProximityScorer`, `SearchEngine`, `QueryExpander`.

**Public API:**
- `EngineFactory.from_artifacts(documents_path, index_dir, proximity_weight=1.0, title_boost=5.0, synonyms_path=None) -> SearchEngine`

**Internal structure:**
1. Load flattened documents JSON → list of `Document` objects
2. Load `tf_index.json`, `pos_index.json`, `doc_stats.json` from index_dir
3. Extract `doc_lengths` and `avgdl` from stats
4. Create two `TextProcessor` instances (BM25 config, proximity config)
5. Optionally create `QueryExpander` from synonyms
6. Create `BM25Scorer` and `ProximityScorer`
7. Construct and return `SearchEngine`

**Main algorithms:** Linear assembly — no complex algorithms.

**Important functions:**
- `_load_json(path, label)` — loads JSON with error messages for FileNotFoundError and JSONDecodeError. Used by both the documents file and the three index files.

**Design decisions:**
- Static factory pattern — all methods are static. No state, no need for instantiation. This is the purest form of Factory Method in the codebase.
- Errors are propagated (not swallowed). If any index file is missing, the server fails at startup rather than at request time.
- The caller is responsible for providing correct paths — no path discovery or convention-based lookup.

**Common pitfalls:**
- If the documents file contains duplicate `doc_id` values, `Document` objects are created but duplicates are not detected.
- The `synonyms_path` is optional; without it, no synonym expansion occurs and the system queries the raw BM25 tokens only.
- The `SearchEngine` constructor parameter order must match — 10 positional arguments.

---

## File 7: `backend/src/core/search_engine.py` (204 lines)

**Purpose:** The central retrieval pipeline — orchestrates BM25 scoring, title boosting, proximity scoring, candidate generation, and result formatting.

**Dependencies:** `BM25Scorer`, `ProximityScorer`, `TextProcessor`, `QueryExpander`, `Document`.

**Public API:**
- `search(query, top_k=None, proximity_weight=None, title_boost=None) -> list[dict]`

**Internal structure:**

```
search(query):
  1. base_tokens = bm25_processor.process_text(query)
     bm25_tokens = base_tokens + synonym_expander.expand(base_tokens)
  2. raw_tokens = proximity_processor.process_text(query)  # no lemmatization, no stopword removal
  3. query_pairs = ProximityScorer.generate_query_pairs(raw_tokens)
  4. candidates = union of tf_index[t].keys() for each t in bm25_tokens
  5. for each doc where doc.doc_id in candidates:
       bm25 = BM25Scorer.score(bm25_tokens, doc.doc_id)
       if bm25 == 0: skip
       title_bonus = len(set(bm25_tokens) ∩ title_tokens[doc.doc_id]) * 5.0
       prox = ProximityScorer.score(doc.doc_id, query_pairs, max_window=30, ordered=True)
       final = bm25 + title_bonus + 1.0 * prox
  6. sort DESC, return top-k
```

**Important functions:**
- `_score_document()` — computes the triple-signal score for one document. Returns a tuple of `(final, bm25, prox, title_matches, doc, matched_terms, exact_matched_terms)`.
- `_generate_candidates()` — set union of all doc_ids that contain any query token in the BM25 index.
- `_prepare_proximity_query()` — delegates to proximity processor (no lemmatization, stopwords preserved).
- `_format_results()` — converts internal tuples into API-ready dicts.

**Design decisions:**
- **Title tokens pre-computed** in `__init__` (`self.title_tokens`). For every doc, title is tokenized with the BM25 processor once at startup. This avoids per-query tokenization of all document titles.
- **Synonym expansion only on BM25 tokens.** Proximity tokens are never expanded — synonyms would create artificial pairs that don't exist in the text.
- **Matched terms tracked at two levels:** `matched_terms` (lemmatized BM25 tokens) for backend analysis, `exact_matched_terms` (original query tokens) for frontend highlighting.
- **Zero-score results are excluded** (line 122: `if result[0] > 0`). This means documents that match via synonyms but have zero BM25 score are excluded — though this shouldn't happen since synonym expansion only adds tokens already in the BM25 index.

**Common pitfalls:**
- Title tokens are pre-computed with the BM25 processor. If `synonym_expander` is present, it's applied to the query during search but NOT to the title tokens. So title boost is computed on base tokens + synonyms, matched against pre-lemmatized title tokens.
- The `top_k` parameter in `search()` is typically `recall_k` (30-50), not the final number of results — final truncation happens in `Reranker`.
- `_score_document` returns 0.0 for all signals if BM25 score is 0.0 — early exit skip.

---

## File 8: `backend/src/core/reranker.py` (180 lines)

**Purpose:** Three-stage reranking: RRF signal fusion → MMR diversity → rule-based boost. Pure math — no ML or embeddings.

**Dependencies:** `math` (for sqrt).

**Public API:**
- `rerank(results, top_k=8, boost_rules=None) -> list[dict]`

**Internal structure:**

```
rerank():
  res = _rrf_fuse(results)
  res = _mmr_diversify(res)
  res = _apply_boost(res, boost_rules)
  return res[:top_k]
```

**Stage 1 — RRF Fusion (`_rrf_fuse`):**
- Rank the top `recall_k` results independently by `bm25_score`, `proximity_score`, and `title_match_count`.
- For each result: `rrf_score = 1/(k+rank_bm25) + 1/(k+rank_prox) + 1/(k+rank_title)`
- `k=60` (inverse rank penalty — larger k means ranks matter less).
- Sort by `rrf_score DESC`.

**Stage 2 — MMR Diversity (`_mmr_diversify`):**
- Start with the highest-RRF result.
- For each remaining candidate: `mmr = λ·score - (1-λ)·max_similarity_to_selected`
- Cosine similarity on BM25 TF vectors (sparse, computed from `tf_index`).
- `λ=0.5` — equal weight for relevance and diversity.
- Pick the highest-MMR candidate, add to selected, repeat.

**Stage 3 — Rule-Based Boost (`_apply_boost`):**
- `final_score = original_score × boost × part_rules[part_no] × level_rules[level]`
- Default level multipliers: `part=1.0`, `article=0.98`, `clause=0.95`, `subclause=0.90`.
- `boost` comes from the Document (default 1.0).
- `part_rules` can be injected to boost/suppress specific parts (e.g., Part 3 on Fundamental Rights).

**Important functions:**
- `_get_tf_vector(doc_id)` — builds/caches sparse TF vectors for cosine similarity. Cache lasts the lifetime of the Reranker instance.
- `_cosine_similarity(vec_a, vec_b)` — dot product over intersection, normalized by L2 norms.
- `_ranked(signal_key)` — helper that produces `[(rank, doc_id), ...]` sorted descending by a signal.

**Design decisions:**
- **rrf_k=60** is higher than the typical default of 60. This means the fusion is less sensitive to individual ranks — consistent with having only 3 signals (vs. many systems that fuse dozens of rankers).
- **MMR with BM25 cosine similarity** rather than embedding similarity. This is a deliberate choice to avoid a dependency on embedding models. BM25 TF vectors provide a reasonable measure of topical overlap.
- **Vector cache** (`_vector_cache`) is unbounded — a long-running server processes queries across different users/documents, and the cache accumulates all doc_id TF vectors ever requested. For 700 documents this is negligible, but if the corpus grows it could become a memory concern.
- Static `_apply_boost` method — can be called without a Reranker instance if needed (though currently it isn't).

**Common pitfalls:**
- The `_vector_cache` is never cleared. For a static corpus of 700 docs this is fine, but if documents are added at runtime (which they aren't), stale vectors could accumulate.
- `_mmr_diversify` re-computes TF vectors for all candidates on every iteration of the while loop. The helper variables `vec_candidates` and `vec_selected` are re-computed each iteration because the candidate list shrinks.
- If `rrf_score` key is present (set by RRF) it's used for MMR; otherwise falls back to `score`. This is a safety fallback for when `rerank()` is called with results that already have `rrf_score`.

---

## File 9: `backend/src/llm/rag_repository.py` (337 lines)

**Purpose:** Data-access layer for the LLM module. Owns the Ollama client, connectivity checks, retry logic, article promotion, and context truncation.

**Dependencies:** `ollama.Client`, `RetrievalWorkflow`, `re`, `time`, `logging`.

**Public API:**
- `retrieve(query, top_k, boost_rules) -> list[dict]` — delegates to `RetrievalWorkflow`
- `promote_to_articles(results) -> list[dict]` — clause→article promotion
- `check_ollama_connection() -> (bool, str)` — cached connectivity
- `check_model_availability(model_name) -> (bool, str, list)` — cached model check
- `call_llm(messages, stream) -> response` — LLM call with 3-attempt retry
- `build_truncated_text(article) -> str` — context for LLM (matched clauses only)

**Internal structure:**
```
__init__():
  - store retrieval_workflow, model, Ollama Client (with optional API key header)
  - _ollama_available = None (lazy, first request triggers check)
  - _available_models = []
  - _build_article_lookup()  ← called in constructor, builds lookup from documents
```

**Main algorithms:**

**Article Promotion (`promote_to_articles`):**
1. Iterate results, collect `matched_clauses` per `article_no` (set of clause_no values)
2. Deduplicate by `article_no` (first occurrence wins — preserves original ranking order)
3. For each unique article:
   - If an article-level Document exists → use its text directly
   - If only clause-level docs exist → concatenate with `\n---\n` separator
   - Build `Citation` string (e.g., "Part 3, Article 31")

**Article Lookup (`_build_article_lookup`):**
Groups all documents by `article_no`. Two cases:
- Articles with their own Document (`level="article"`) — typically articles with lettered sub-clauses where the full text is already aggregated.
- Articles stored as individual clause Documents — concatenate all clause texts together.

**Context Truncation (`build_truncated_text`):**
If matched clauses are tracked, returns only the header + matched clause texts rather than the full article. This saves LLM context window for the most relevant portions.

**Ollama Retry (`call_llm`):**
3 attempts with 0.5s delay. Creates `keep_alive=30m` and `num_ctx=4096`. All exceptions are caught and retried.

**Important functions:**
- `_build_article_lookup()` — builds `_article_lookup` (article_no → full article) and `_clause_structure` (article_no → clause map). This is called once in the constructor and never rebuilt.
- `promote_to_articles()` — the main article promotion entry point. Called on every query.
- `call_llm()` — Ollama call with retry. Raises the last exception if all 3 attempts fail.
- `_extract_model_names()` — handles two response shapes from the Ollama API (dict vs object), making the code resilient to API version changes.
- `_ensure_ollama_checked()` — lazy initialization with caching. Only checks once per process lifetime (or re-checks if the first check failed).

**Design decisions:**
- Article lookup is built in the constructor from `RetrievalWorkflow.engine.documents`. This ties RAGRepository to having access to the full document list. The `_build_article_lookup` method has a guard that checks if `self.retrieval.engine.documents` exists.
- Ollama connectivity is cached per process lifetime. The first query triggers the check; subsequent queries use the cached result. This avoids a `/api/tags` call on every request but means that if Ollama restarts, the server won't detect it until the process restarts.
- Context truncation only works for articles with tracked clause structure. For single-block articles or articles where no clause was matched, the full text is returned.
- `promote_to_articles` handles the "no article lookup" case gracefully — if `_article_lookup` is empty, it returns the raw results unchanged.

**Common pitfalls:**
- The `_article_lookup` is built once. If new documents are added to the corpus at runtime (they aren't), the lookup would be stale.
- `_build_promoted_item` receives a `result` dict and optionally enriches it with `article` data from the lookup. If `article` is None, the result's fields are used as-is — this means partial data can flow through.
- The `_clean_body` function strips enriched-text headers using `_ENRICHED_RE` — this regex must match the output format of `flatten_constitution.py`. If the format changes, the body cleaning breaks silently.

---

## File 10: `backend/src/llm/rag_workflow.py` (216 lines)

**Purpose:** Thin orchestrator that composes `RAGRepository` + `RAGFormatter` into the public Q&A entry points. Handles the LLM decision matrix and response assembly.

**Dependencies:** `RAGRepository`, `RAGFormatter`.

**Public API:**
- `ask(query, use_llm=False) -> dict` — synchronous Q&A
- `ask_streaming(query, use_llm=True) -> generator` — streaming Q&A (SSE event dicts)
- `retrieve(query, top_k=None) -> list[dict]` — convenience wrapper

**Internal structure:**
```
ask(query, use_llm):
  1. _prepare_articles(query) → retrieve + promote
  2. If !use_llm → return {query, articles}
  3. check_ollama_connection() → if not connected → return {..., ollama_status: connected=false}
  4. check_model_availability() → if not available → return {..., model_available=false}
  5. format_context(promoted_articles)
  6. build_system_prompt() + build_user_prompt(query, context)
  7. call_llm(messages, stream=False)
  8. return {query, articles, response, citations, ollama_status}
```

**Main algorithms:**

**Decision matrix:**
| Condition | Response includes |
|-----------|------------------|
| `use_llm=false` | query + articles |
| LLM disconnected | query + articles + ollama_status.connected=false |
| Model missing | query + articles + ollama_status.model_available=false |
| LLM succeeds | query + articles + response + citations + ollama_status |
| LLM fails after retries | query + articles + response (error text) + error field |

**Streaming variant:** Same logic but yields SSE event dicts:
- `{"type": "articles", "articles": [...]}` — immediately
- `{"type": "token", "content": "partial"}` — per LLM chunk
- `{"type": "done"}` — completion
- `{"type": "error", "content": "..."}` — on failure

**Important functions:**
- `_prepare_articles(query)` — retrieve + promote, also sets `full_text` = `text` for persistence
- `_build_article_dict(article)` — filters to only the fields defined in `_ARTICLE_FIELDS`

**Design decisions:**
- `_ARTICLE_FIELDS` constant at module level defines the exact response contract. Adding or removing fields here changes the API response shape.
- Articles are retrieved with `max_context_articles = 8`, then all 8 are sent to the LLM in context. The `DEFAULT_MAX_CONTEXT` is 8 — matching the `DEFAULT_TOP_K` from retrieval.
- Standalone `main()` demo function runs 3 preset questions. Useful for testing without the Flask server.

**Common pitfalls:**
- `_prepare_articles` sets `art["full_text"] = art["text"]` — the same string assigned to two keys. The `text` field is later truncated by `build_truncated_text()` in the formatter, but `full_text` retains the original. This is intentional for persistence but can confuse readers.
- The standalone `main()` has hardcoded paths (`data/output/...`) — only works when run from the backend directory.

---

## File 11: `backend/src/llm/rag_formatter.py` (55 lines)

**Purpose:** Build LLM prompts — context formatting, system instructions, user query wrapper.

**Dependencies:** None — pure string builder.

**Public API:**
- `format_context(articles) -> str` — concatenates article citations and texts
- `build_system_prompt() -> str` — system-level instructions for the LLM
- `build_user_prompt(query, context) -> str` — user message with context and question

**Internal structure:**
- `format_context`: Joins `{citation}: {title}\n{text}` for each article, with relevance score appended.
- `build_system_prompt`: A multi-line instruction block that defines 6 answer-style adaptation rules (What→explain, Who→identify, When→date, etc.), plus grounding constraints ("Answer ONLY using the Context").
- `build_user_prompt`: Template with `{context}` and `{query}` placeholders.

**Design decisions:**
- All methods are static — no state, no instance needed.
- The system prompt is the most critical piece: it enforces strict grounding (no hallucination) and style adaptation by question type. This is where the "Explainable" in the project name is implemented.
- Relevance scores are included in the context — the LLM can see which articles are most relevant.

**Common pitfalls:**
- The score in `format_context` comes from `article["score"]` — this is the final score after reranking, promotion, and boost, not any raw score.
- If `use_llm=false`, the formatter is never called. It's only invoked for LLM-involved answers.

---

## File 12: `backend/app.py` (49 lines)

**Purpose:** Flask application factory and server entry point.

**Dependencies:** `Flask`, `flask-cors`, `python-dotenv`, `Database`, `log_config`, `init_workflow`, blueprints, `get_spacy_pipeline`.

**Public API:** `create_app() -> Flask`, `main()`.

**Internal structure:**
```
main():
  load_dotenv()
  setup_logging()
  init_workflow()        ← builds SearchEngine + Reranker + RAGWorkflow
  get_spacy_pipeline()   ← loads spaCy model (singleton)
  app = create_app()     ← Flask(), CORS(), Database().connect(), register_blueprints
  app.run()
```

**Important functions:**
- `create_app()` — factory. Creates Flask, enables CORS, connects MongoDB, registers blueprints.
- `main()` — entry point. Loads env, sets up logging, initializes workflow, starts spaCy, creates app, runs.

**Design decisions:**
- **Eager initialization:** `init_workflow()` and `get_spacy_pipeline()` run before the server starts. This adds ~1s startup latency but ensures zero slow-first-request penalty.
- **`create_app()` is separate from `main()`** — the factory pattern allows testing with different configurations and importing the app in WSGI servers.
- `CORS(app)` with no restrictions — no origin checking, no allowed methods. This is a production readiness gap.
- `threaded=True` — Flask's built-in threading for concurrent request handling. No async workers.

**Common pitfalls:**
- No environment validation — if `JWT_SECRET` is missing, it only fails when the first authenticated request arrives, not at startup.
- MongoDB connection is established in `create_app()` but the database singleton is loaded from `config/db_connect.py` — if MongoDB is unreachable, the app fails to start (by design).

---

## File 13: `backend/controllers/decorators.py` (69 lines)

**Purpose:** JWT authentication decorator. Extracts token, validates signature, checks token_version.

**Dependencies:** `jwt` (PyJWT), `flask.request`, `mongoengine.connection`, `User` model.

**Public API:**
- `token_required(f)` — decorator for protected routes

**Internal structure:**
```
token_required:
  1. Extract token from:
     a. Authorization: Bearer <token> header (primary)
     b. token cookie (fallback)
  2. If no token → 401
  3. If JWT_SECRET not configured → 500
  4. jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
  5. _get_user(user_id) → lookup user
     a. If user exists and payload.token_version < user.token_version → 401 (invalidated)
     b. If user is None (DB unavailable) → skip version check (pass)
  6. Attach payload to request.user
  7. Handle ExpiredSignatureError → 401
  8. Handle InvalidTokenError → 401
```

**Important functions:**
- `_get_user(user_id)` — tries to access the database; if `ConnectionFailure` is raised, returns None (graceful degradation — authentication still works, just skips token_version check).

**Design decisions:**
- **Token version invalidation:** On logout, user.token_version is incremented. All existing JWTs with the old `token_version` become invalid immediately. This is replay-attack protection.
- **Cookie fallback:** If the Authorization header is missing, checks for a `token` cookie. This allows both SPA (header-based) and server-rendered (cookie-based) clients.
- **DB-unavailable fallback:** If the database is unreachable, the decorator skips the `token_version` check but still validates the JWT signature. This means logged-in users can continue using the system even if MongoDB is temporarily down (but new logins would fail).
- Double-fault handling: `_get_user` wraps the lookup in a bare `except Exception`, so any DB error becomes a None return rather than a 500.

**Common pitfalls:**
- The `Bearer ` prefix check is case-sensitive. `Authorization: bearer <token>` (lowercase 'b') would fail the `startswith('Bearer ')` check and fall through to the cookie check.
- If both the header and cookie are absent, the decorator returns 401 immediately — no fallback to any other auth method.
- The cookie `SameSite=Strict` means the cookie is not sent on cross-origin requests, which is correct for APIs but can cause issues in embedded contexts.

---

## File 14: `backend/controllers/api_controller.py` (182 lines)

**Purpose:** HTTP handlers for all Q&A and message management endpoints. Input validation, response assembly, persistence.

**Dependencies:** `MessageService`, `QAService`, `flask`.

**Public API (handlers):**
- `home()` — GET /api/v1/ — endpoint list
- `health()` — GET /api/v1/health — liveness
- `ask()` — POST /api/v1/ask — synchronous Q&A
- `ask_stream()` — POST /api/v1/ask-stream — streaming Q&A via SSE
- `list_messages()` — GET /api/v1/messages — paginated history
- `get_message(message_id)` — GET /api/v1/messages/<id> — single message
- `delete_message(message_id)` — DELETE /api/v1/messages/<id>
- `delete_all_messages()` — DELETE /api/v1/messages

**Internal structure:**
```
ask():
  _parse_ask_request() → validate (JSON, query, length)
  → QAService.answer_query(query, use_llm)
  → if status==200: QAService.persist_message(user_id, query, payload)
  → return jsonify(payload), status_code

ask_stream():
  _parse_ask_request()
  → QAService.answer_query_streaming(query, use_llm)
  → Response(stream_with_context(_stream_events(...)), mimetype=text/event-stream)
```

**Important functions:**
- `_parse_ask_request()` — shared validation for both /ask and /ask-stream. Returns `(data, error)` tuple.
- `_stream_events()` — generator that wraps the QAService streaming generator, accumulates token events for persistence, and calls `persist_message` on the "done" event.

**Design decisions:**
- `_persist_message()` is fire-and-forget — failures are logged but never break the response. This ensures the user always gets their answer even if MongoDB is slow or unavailable.
- The same `_parse_ask_request` function is used for both endpoints, ensuring consistent validation.
- `ask_stream` defaults `use_llm=True` (different from `ask` which defaults to `False`). This makes sense: streaming is primarily for LLM answers; non-LLM retrieval is fast enough to be synchronous.
- Ownership checks in `get_message` and `delete_message` compare `result["data"]["user"]["id"]` to `request.user.get("user_id")` — string comparison.

**Common pitfalls:**
- `_stream_events` accumulates the full answer in memory before persisting. For very long answers with many tokens, this is fine; for indefinite streaming, it could be a memory concern.
- The **"X-Accel-Buffering": "no"** header is nginx-specific. Behind other proxies, SSE may be buffered and delayed.
- Error handling wraps the entire handler in a broad `except Exception` that returns 500 — no distinction between validation errors (4xx) and server errors (5xx).

---

## File 15: `backend/services/qa_service.py` (92 lines)

**Purpose:** Application service — owns pipeline initialization and persistence. Bridge between Flask controllers and domain layer.

**Dependencies:** `EngineFactory`, `Reranker`, `RetrievalWorkflow`, `RAGRepository`, `RAGWorkflow`, `ArticleService`, `MessageService`.

**Public API:**
- `init_workflow()` — global pipeline initialization (called once at startup)
- `QAService.answer_query(query, use_llm) -> (dict, int)` — Q&A response
- `QAService.answer_query_streaming(query, use_llm) -> generator`
- `QAService.persist_message(user_id, query, payload) -> None`

**Internal structure:**
```
init_workflow():
  engine = EngineFactory.from_artifacts(docs, index, synonyms)
  reranker = Reranker(engine.bm25_scorer.tf_index)
  retrieval_workflow = RetrievalWorkflow(engine, reranker)
  repository = RAGRepository(retrieval_workflow)
  _workflow = RAGWorkflow(repository, RAGFormatter())

persist_message():
  for each article → ArticleService.create_article() → upsert by doc_id
  collect article ObjectIds
  → MessageService.create_message() → save query + answer + article refs
```

**Design decisions:**
- **Module-global `_workflow` singleton:** Initialized once in `init_workflow()`, accessed via `_get_workflow()`. No locks, no lazy init — if `init_workflow()` hasn't been called, `_workflow` is None and the server crashes on first request (by design).
- Eager initialization means predictable response times — no slow cold start.
- `publish_message` is called from two places (in `ask` after response, in `_stream_events` after completion for streaming). Both fire-and-forget.

**Common pitfalls:**
- `ArticleService.create_article()` is called with `article.get("content")` but the `content` key may not exist in the article dict (it's set by `_build_promoted_item` but it depends on `_clean_body`). This is why there are fallback patterns throughout.
- The `_DEFAULT_*` paths are relative to the backend directory — they only work when the server is started from `backend/`.

---

## File 16: `backend/services/article_service.py` (134 lines)

**Purpose:** CRUD for `ReferencedArticle` MongoDB collection. Implements upsert-by-doc_id pattern.

**Dependencies:** `ReferencedArticle` model, mongoengine.

**Public API:**
- `create_article(...) -> dict` — create or update (upsert by doc_id)
- `get_article(article_id) -> dict`
- `list_articles() -> dict`
- `delete_article(article_id) -> dict`

**Main algorithms:**
- **Upsert:** Query by `doc_id`. If exists → update fields. If not → create new.
- Updated fields: `content`, `text`, `full_text`, `matched_terms`, `exact_matched_terms`, `relevance_score`, `bm25_score`, `proximity_score`, `title_match_count`.

**Design decisions:**
- Upsert-by-doc_id ensures deduplication: if the same constitution article appears in multiple queries, the existing document is updated rather than duplicated.
- All methods return a standard dict with `success`, `error`, and `data` keys — consistent with the rest of the service layer.
- `matched_terms` defaults to `[]` if None — prevents storing null values in MongoDB.

**Common pitfalls:**
- The constructor signature has 16 parameters, most of which are optional. Callers must match the parameter names carefully.
- `ValidationError` is caught generically — no detail about which field failed validation.
- Uses synchronous mongoengine calls within `async def` method signatures (see technical debt).

---

## File 17: `backend/services/message_service.py` (195 lines)

**Purpose:** CRUD for Q&A messages with pagination, ownership, and search.

**Dependencies:** `User`, `ReferencedArticle`, `Message` models, mongoengine.

**Public API:**
- `create_message(user_id, query, answer, articles=[]) -> dict`
- `get_user_messages(user_id, limit=20, skip=0) -> dict` (paginated)
- `get_message(message_id) -> dict`
- `update_message_answer(message_id, new_answer) -> dict`
- `search_messages(user_id, search_term) -> dict`
- `delete_message(message_id) -> dict`
- `delete_user_messages(user_id) -> dict`

**Internal structure:**
- `create_message`: Lookup user → lookup each article ref by id → create Message with article references → save.
- `get_user_messages`: Query `Message.objects(user=user).order_by('-created_at').skip(skip).limit(limit)` + count for pagination metadata.

**Design decisions:**
- Article references are stored as a list of `ObjectId` references. The `to_json()` method populates these on read.
- `search_messages` uses `query__icontains` which is a case-insensitive contains search in mongoengine. Note: the search term is regex-escaped, so it matches literally.
- Pagination returns `has_more: skip + limit < total_count` for the frontend to know if there are more pages.

**Common pitfalls:**
- `create_message` imports the article reference, but if an article id is invalid, it logs a warning and skips it — the message is still created without that article reference.
- Uses `async def` with synchronous mongoengine calls. Misleading but functionally correct.
- The `re.escape` in `search_messages` means the user can't use regex patterns in search (which is correct — search should be literal).

---

## File 18: `frontend/src/App.jsx` (58 lines)

**Purpose:** Frontend root — routing and auth provider setup.

**Dependencies:** `react-router-dom`, `AuthProvider`, `Navbar`, `ProtectedRoute`, all page components.

**Public API:** The `App` component (exported default).

**Internal structure:**
```
BrowserRouter
  AuthProvider
    Navbar
    div#main-content
      Routes
        /login → LoginPage
        /register → RegisterPage
        / → ProtectedRoute → HomePage
        /history → ProtectedRoute → HistoryPage
        /history/:id → ProtectedRoute → MessageDetailPage
        /about → AboutPage
        /how-it-works → HowItWorksPage
        * → NotFoundPage
```

**Design decisions:**
- `AuthProvider` wraps all routes including Navbar — auth state is available everywhere.
- `ProtectedRoute` wraps the authenticated pages. Unauthenticated users are redirected to `/login`.
- `/about` and `/how-it-works` are public (no auth required).
- Navbar is rendered outside the route switch — it's always visible.

**Common pitfalls:**
- The `#main-content` div is used for layout but has no explicit styling — layout depends on parent containers.
- Route changes are handled by `react-router-dom` v7 — no page reloads.

---

## File 19: `frontend/src/hooks/useAskStream.js`

**Purpose:** Custom hook for consuming the SSE streaming endpoint.

**Dependencies:** `apiClient` from `api/client.js`.

**Public API:**
`useAskStream()` returns `{ articles, response, loading, error, startStream, cancel }`

**Internal structure:**
```
startStream(query, useLlm):
  POST /api/v1/ask-stream via fetch (with Authorization header)
  → ReadableStream.getReader() → while loop reading chunks
  → parse "data: {...}\n\n" SSE lines
  → dispatch by event type: articles → setArticles, token → appendResponse, done → setLoading(false)
  → support AbortController for cancellation
```

**Design decisions:**
- Uses the Fetch API's `ReadableStream` directly rather than an EventSource wrapper. This gives more control over the SSE parsing and allows custom HTTP headers (Authorization).
- `AbortController` allows the user to cancel an in-flight stream — the Cancel button in MainSearchBar triggers this.
- State is managed with `useState` inside the hook — the consuming component re-renders on each state update.

**Common pitfalls:**
- The hook assumes `data: {...}\n\n` SSE format (single-line events). Multi-line SSE data would break the line-by-line parsing.
- If the connection drops mid-stream, the error state is set and `loading` becomes false — the user sees partial results.

---

## File 20: `backend/controllers/auth_controller.py` (108 lines)

**Purpose:** User registration, login, logout, and profile endpoints.

**Dependencies:** `UserService`, `User` model, `flask`.

**Public API (handlers):**
- `register()` — POST /api/v1/auth/register
- `login()` — POST /api/v1/auth/login
- `logout()` — POST /api/v1/auth/logout
- `get_current_user()` — GET /api/v1/auth/me

**Main algorithms:**

**Login:**
```
UserService.authenticate_user(email, password)
  → User.objects.get(email=email)
  → check_password(password)
  → jwt.encode({user_id, email, token_version}, JWT_SECRET, algorithm='HS256')
  → set httpOnly cookie + return JSON with token
```

**Logout:**
```
user.token_version += 1
user.save()
→ All existing JWTs become invalid
→ Clear cookie
```

**Design decisions:**
- Token version invalidation: logout increments `User.token_version`. Any JWT with a lower `token_version` is rejected by the `@token_required` decorator. This ensures logout is irreversible even if the JWT hasn't expired.
- Dual response: Return token in JSON body AND set it as httpOnly cookie. The frontend uses the body token; the decorator checks both.
- `SameSite=Strict` on the cookie — prevents CSRF attacks but means the cookie is not sent on cross-origin navigation.
- `register()` returns 201 on success, 400 on validation errors.

**Common pitfalls:**
- `login()` calls `current_app.config.get('PRODUCTION', False)` — production flag must be set properly for secure cookies.
- Error handling: if `User.objects.get(id=user_id)` fails in `logout()`, the exception is caught and a 500 is returned without invalidating the token.
- `get_current_user()` uses `UserService.get_user(user_id)` which returns a dict with `success`, `data`, `message` keys — the controller returns this directly, so the response shape is `{success: true, data: {...}, message: "..."}` rather than a flat user object.
