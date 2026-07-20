# Data Flow — The User Query

## Chosen Data: A Single User Query

We trace `"What are the fundamental rights?"` from the moment the user types it until it reaches storage as a persisted message.

---

## Flow Map

```
Frontend input field
  │
  ▼  React state (useState)
  │
  ▼  HTTP POST (JSON body)
  │
  ▼  Flask parser → request object
  │
  ▼  Validation → query string
  │
  ├──▶ BM25 processor → lemmatized stopword-free tokens
  │    └──▶ Synonym expander → expanded tokens
  │
  ├──▶ Proximity processor → raw tokens with stopwords
  │    └──▶ Pair generator → term pairs
  │
  ├──▶ BM25 scorer → per-doc BM25 scores
  ├──▶ Title boost → per-doc title match bonus
  ├──▶ Proximity scorer → per-doc pair proximity scores
  │
  ├──▶ Hybrid score fusion → 50 scored documents
  │
  ├──▶ RRF fusion → combined rank signal
  ├──▶ MMR diversity → diversified order
  ├──▶ Rule-based boost → final multipliers
  │    └──▶ Top 8 results
  │
  ├──▶ Article promotion → 8 full articles with matched clauses
  │
  ├──▶ LLM context formatting → structured prompt string
  ├──▶ Ollama chat → LLM response text
  │
  ├──▶ Response assembly → JSON payload
  │    ├──▶ to HTTP response
  │    └──▶ to MongoDB (persistence)
  │
  └──▶ Frontend renders → user sees answer + article cards
```

---

## Step-by-Step Data Transformations

### Step 1 — User Input (Frontend)

**File:** `frontend/src/components/mainsearchbar.jsx`
**Object:** React state variable
**Transformation:** Raw keystrokes → controlled input value

```javascript
const [query, setQuery] = useState("");
// User types "What are the fundamental rights?"
// → query = "What are the fundamental rights?"
```

**Purpose:** Capture user input before submission.

---

### Step 2 — HTTP Serialization (Frontend)

**File:** `frontend/src/api/client.js`
**Object:** `apiClient()` → fetch options
**Transformation:** React state → JSON HTTP body

```javascript
// mainsearchbar.jsx calls:
apiClient("/api/v1/ask", {
  method: "POST",
  body: JSON.stringify({ query: "What are the fundamental rights?", use_llm: true }),
})
// apiClient.js adds Authorization: Bearer <jwt> header, 100s timeout
```

**Purpose:** Serialize the query into an HTTP POST request with JWT auth.

---

### Step 3 — HTTP Deserialization (Backend)

**File:** `backend/controllers/api_controller.py:40-59`
**Function:** `_parse_ask_request()`
**Transformation:** Flask `request` object → Python string

| Input | `request` (Flask) — JSON body bytes |
|-------|--------------------------------------|
| Validation | `request.is_json`, `request.get_json(silent=True)`, `data.get("query")`, type check, ≤500 chars |
| Output | `data = {"query": "What are the fundamental rights?", "use_llm": true}` |
| Failures | 400 with `{"error": "..."}` for missing content-type, unparseable JSON, missing query, wrong type, or too long |

**Purpose:** Extract and validate the query from the HTTP request.

---

### Step 4 — BM25 Tokenization

**File:** `backend/src/core/text_processor.py:93-110`
**Function:** `TextProcessor.process_text(text)` — called via `SearchEngine.search()`
**Object:** `TextProcessor` instance configured with `use_lemmatization=True, remove_stopwords=True`

| Input | `"What are the fundamental rights?"` |
|-------|--------------------------------------|
| `normalize_text()` | → `"what are the fundamental rights"` (lowercase, contractions expanded, non-alphanumeric stripped) |
| `lemmatize_tokens()` via spaCy | → `["what", "be", "the", "fundamental", "right"]` |
| `_filter_stopwords()` | → `["fundamental", "right"]` (what/be/the removed) |
| Output | `["fundamental", "right"]` |

**Purpose:** Produce clean, lemmatized tokens for BM25 scoring. Stopwords are removed because they add noise to IDF.

---

### Step 5 — Synonym Expansion

**File:** `backend/src/core/query_expander.py:38-65`
**Function:** `QueryExpander.expand(tokens, raw_query)`

| Input | `["fundamental", "right"]` |
|-------|----------------------------|
| Lookup | `"fundamental"` → no synonym group; `"right"` → group with `entitlement`, `prerogative`, etc. |
| Expansion | `["fundamental", "right", "entitlement", "prerogative"]` |
| Multi-word guard | Multi-word phrases only included if present in raw query string |
| Output | `["fundamental", "right", "entitlement", "prerogative"]` |

**Purpose:** Improve recall by matching documents that use synonym variants (e.g., "prerogative" instead of "right").

---

### Step 6 — Proximity Tokenization

**File:** `backend/src/core/text_processor.py:93-110`
**Function:** `TextProcessor.process_text(text)` — `TextProcessor` with `use_lemmatization=False, remove_stopwords=False`

| Input | `"What are the fundamental rights?"` |
|-------|--------------------------------------|
| `normalize_text()` | → `"what are the fundamental rights"` |
| No lemmatization | tokens pass through unchanged |
| No stopword removal | all tokens kept |
| Output | `["what", "are", "the", "fundamental", "rights"]` |

**Purpose:** Preserve original word order and stopwords for proximity scoring. "right to education" ≠ "education right" — ordering matters.

---

### Step 7 — Proximity Pair Generation

**File:** `backend/src/core/proximity.py:29-33`
**Function:** `ProximityScorer.generate_query_pairs(tokens)`

| Input | `["what", "are", "the", "fundamental", "rights"]` |
|-------|----------------------------------------------------|
| Length check | 5 tokens → ≤5, so use **all-pairs** |
| Pairs generated | 10 pairs: (what,are), (what,the), (what,fundamental), (what,rights), (are,the), (are,fundamental), (are,rights), (the,fundamental), (the,rights), (fundamental,rights) |
| Output | `[("what","are"), ("what","the"), ..., ("fundamental","rights")]` |

**Purpose:** For short queries (≤5 tokens), all cross-term pairs are meaningful. For longer queries, only adjacent pairs are used to avoid O(n²) blowup.

---

### Step 8 — Candidate Generation

**File:** `backend/src/core/search_engine.py:134-140`
**Function:** `SearchEngine._generate_candidates(bm25_tokens)`

| Input | `["fundamental", "right", "entitlement", "prerogative"]` |
|-------|----------------------------------------------------------|
| Operation | For each token, look up `tf_index[token].keys()` → union all doc IDs |
| Output | `set` of ~200-400 document IDs (from ~700 total) containing at least one expanded token |

**Purpose:** Narrow the corpus from 700 documents to a candidate set of documents that contain any query-related term.

---

### Step 9 — BM25 Scoring

**File:** `backend/src/core/bm25_scorer.py:27-41`
**Function:** `BM25Scorer.score(query_tokens, doc_id)`

**Applied once per candidate document.**

| Input | `["fundamental", "right", "entitlement", "prerogative"]`, doc_id=`"31"` |
|-------|-------------------------------------------------------------------------|
| Per term | `tf = tf_index[term][doc_id]`; if tf=0 skip; `idf = ln((N-df+0.5)/(df+0.5)+1)` |
| Per doc | `doc_len = doc_lengths[doc_id]`, `avgdl` from stats |
| Formula | `score = Σ idf(t) × tf(t)×(1.5+1) / (tf(t) + 1.5×(1-1.0+1.0×doc_len/avgdl))` |
| Output | `float` — e.g., `6.12` |

**Purpose:** Compute term-frequency-based relevance using the BM25 algorithm. `k1=1.5` controls TF saturation, `b=1.0` applies full length normalization.

---

### Step 10 — Title Boost

**File:** `backend/src/core/search_engine.py:168`
**Inline in `_score_document()`**

| Input | `["fundamental", "right", "entitlement", "prerogative"]` ∩ `title_tokens[doc_id]` |
|-------|-----------------------------------------------------------------------------------|
| Operation | Count intersection size; multiply by 5.0 |
| Example | For Article 31 "Right relating to education": title tokens include `"right"` → `title_match_count=1` → `boosted_bm25 = 6.12 + 1×5.0 = 11.12` |
| Output | `float` — BM25 + title bonus |

**Purpose:** Documents whose titles contain query terms get a significant boost. "Right relating to education" ranks higher for "rights" queries because the title directly matches.

---

### Step 11 — Proximity Scoring

**File:** `backend/src/core/proximity.py:67-103`
**Function:** `ProximityScorer.score(doc_id, pairs, max_window=30, ordered=True)`

| Input | doc_id=`"31"`, 10 query pairs |
|-------|--------------------------------|
| Per pair | Look up positions of both terms in `pos_index`; compute minimum ordered distance via two-pointer sweep |
| If distance ≤ 30 | `score += 1/(distance+1)²` |
| Average | `total / valid_pairs` (if no valid pairs, returns 0.0) |
| Output | `float` — e.g., `2.35` |

**Purpose:** Reward documents where query terms appear close together. "fundamental rights" appearing in sequence scores higher than "fundamental" on page 1 and "rights" on page 5.

---

### Step 12 — Hybrid Score Fusion

**File:** `backend/src/core/search_engine.py:115-127`
**Inline in `search()` loop**

| Input | BM25 score + title bonus + proximity score |
|-------|--------------------------------------------|
| Formula | `final = boosted_bm25 + 1.0 × proximity_score` |
| Example | `11.12 + 2.35 = 13.47` |
| Sort | All scored documents sorted DESC by `final` |
| Output | Top 50 scored results as `list[dict]` with full metadata |

**Purpose:** Combine three independent relevance signals into a single sortable score.

---

### Step 13 — RRF Fusion

**File:** `backend/src/core/reranker.py:54-84`
**Function:** `Reranker._rrf_fuse(results)`

| Input | 50 scored documents from SearchEngine |
|-------|---------------------------------------|
| Rank 1 | Sort by `bm25_score` DESC → each doc gets BM25 rank |
| Rank 2 | Sort by `proximity_score` DESC → each doc gets proximity rank |
| Rank 3 | Sort by `title_match_count` DESC → each doc gets title rank |
| Fusion | `rrf_score = 1/(60+bm25_rank) + 1/(60+prox_rank) + 1/(60+title_rank)` |
| Output | Same 50 documents, now with `rrf_score` field, sorted by RRF DESC |

**Purpose:** Fuse three independent rankings without tuning weights. RRF automatically balances signals — a document that ranks moderately on all three signals may outrank one that ranks very high on only one.

---

### Step 14 — MMR Diversity

**File:** `backend/src/core/reranker.py:89-126`
**Function:** `Reranker._mmr_diversify(results)`

| Input | 50 documents sorted by RRF |
|-------|----------------------------|
| Seed | Pick highest-RRF document first |
| Loop | For each remaining candidate: `mmr = 0.5×rrf_score - 0.5×max_similarity(to already selected)` |
| Similarity | Cosine similarity on sparse BM25 TF vectors |
| Pick | Move highest-MMR candidate to selected list |
| Output | 50 documents reordered for diversity |

**Purpose:** Prevent all top-8 results from being about the same topic. If the query is "fundamental rights", MMR ensures you also see results from other parts of the constitution, not just Part 3.

---

### Step 15 — Rule-Based Boost

**File:** `backend/src/core/reranker.py:132-159`
**Function:** `Reranker._apply_boost(results)`

| Input | 50 diversified documents |
|-------|--------------------------|
| Per doc | `final_score = score × doc.boost × part_rules[part_no] × level_rules[level]` |
| Default multipliers | `part: 1.0, article: 0.98, clause: 0.95, subclause: 0.90` |
| Output | Top 8 documents taken after boost |

**Purpose:** Authorial and hierarchical boosts. Part-level rules can promote specific parts of the constitution. Level rules ensure full articles rank above clauses/sub-clauses by default.

---

### Step 16 — Article Promotion

**File:** `backend/src/llm/rag_repository.py:175-208`
**Function:** `RAGRepository.promote_to_articles(results)`

| Input | 8 document-level results (possibly clauses/sub-clauses) |
|-------|---------------------------------------------------------|
| Group | Aggregate by `article_no` |
| Merge | For articles stored as clauses → concatenate with `\n---\n`; for articles with direct text → use as-is |
| Dedup | First occurrence of each `article_no` keeps its score |
| Track | `matched_clauses` list per article for context truncation |
| Output | 8 promoted article dicts with `content`, `citation`, `matched_clauses` |

**Purpose:** Users should see full articles, not fragments. A search matching "Clause 2 of Article 31" should return the entire Article 31.

---

### Step 17 — LLM Context Formatting

**File:** `backend/src/llm/rag_formatter.py:5-16`
**Function:** `RAGFormatter.format_context(articles)`

| Input | 8 article dicts with `citation`, `title`, `text`, `score` |
|-------|-----------------------------------------------------------|
| Per article | `"{citation}: {title}\n{text}\n(Relevance Score: {score:.2f})\n"` |
| Output | Single string with all 8 articles concatenated, separated by blank lines |

**Purpose:** Convert structured article data into a flat text block the LLM can consume in its context window.

---

### Step 18 — LLM Prompt Assembly

**File:** `backend/src/llm/rag_formatter.py:19-55`
**Functions:** `build_system_prompt()`, `build_user_prompt(query, context)`

| Input | `query`, formatted context string |
|-------|----------------------------------|
| System prompt | Grounding instructions: cite articles, answer from context only, adapt style by question type, decline if not found |
| User prompt | `"Context:\n{context}\n\nQuestion:\n{query}\n\nTask:\nFind the exact answer..."` |
| Messages | `[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]` |
| Output | `list[dict]` — 2 messages ready for Ollama API |

**Purpose:** Structure the LLM conversation with strict grounding instructions and the retrieved articles as context.

---

### Step 19 — LLM Call

**File:** `backend/src/llm/rag_repository.py:320-338`
**Function:** `RAGRepository.call_llm(messages, stream=False)`

| Input | 2 messages, model=`"qwen3:8b"`, stream=`False` |
|-------|-------------------------------------------------|
| Transport | HTTP POST to `ollama.Client.chat()` at `http://127.0.0.1:11434/api/chat` |
| Config | `keep_alive="30m"`, `options={"num_ctx": 4096}` |
| Retry | 3 attempts with 0.5s delay between failures |
| Output | `response.message.content` (string) — e.g., `"The Constitution of Nepal guarantees..."` |

**Purpose:** Generate a natural language answer grounded in the retrieved articles.

---

### Step 20 — Response Assembly

**File:** `backend/src/llm/rag_workflow.py:104-119`
**Inline in `ask()`**

| Input | query, promoted articles, LLM response |
|-------|----------------------------------------|
| Build | `result = {"query": query, "articles": [...], "response": "...", "citations": [...], "ollama_status": {...}}` |
| `articles` | Filtered through `_build_article_dict()` — only fields the frontend needs |
| `citations` | `[{"article": citation, "title": title, "doc_id": doc_id}]` for each article |
| Output | `dict` — the complete JSON payload |

**Purpose:** Assemble the final response payload that the frontend will render.

---

### Step 21 — HTTP Serialization (Backend)

**File:** `backend/controllers/api_controller.py:84`
**Inline in `ask()`**

| Input | Python dict |
|-------|-------------|
| Flask | `jsonify(payload)` → serializes to JSON string, sets Content-Type: application/json |
| Output | HTTP response with status 200 and JSON body |

**Purpose:** Send the structured response back to the client over HTTP.

---

### Step 22 — MongoDB Persistence (Articles)

**File:** `backend/services/article_service.py:11-73`
**Function:** `ArticleService.create_article(...)`
**Collection:** `referenced_articles`

| Input | Each article dict from the response payload |
|-------|---------------------------------------------|
| Lookup | `ReferencedArticle.objects(doc_id=doc_id).first()` |
| If exists | Update: title, citation, scores, text, matched_terms → `save()` |
| If new | `ReferencedArticle(...)` → `save()` — create new document |
| Output | `{"success": true, "data": {"id": ObjectId, ...}}` |

**Transformation:** `ArticleService.create_article(article_no=31, title="Right relating to education", score=8.47, ...)` → MongoDB document in `referenced_articles` collection.

---

### Step 23 — MongoDB Persistence (Message)

**File:** `backend/services/message_service.py:16-72`
**Function:** `MessageService.create_message(...)`
**Collection:** `messages`

| Input | user_id, query, answer, list of article ObjectIds |
|-------|---------------------------------------------------|
| Resolve | `User.objects.get(id=user_id)` |
| Resolve | `ReferencedArticle.objects.get(id=...)` for each article id |
| Create | `Message(query=query, answer=answer, user=user, articles=refs).save()` |
| Output | `{"success": true, "data": message.to_json()}` |

**Transformation:** `MessageService.create_message(user_id, query="What are the fundamental rights?", answer="The Constitution guarantees...", articles=[ObjectId("...")])` → MongoDB document in `messages` collection.

---

### Step 24 — HTTP Deserialization (Frontend)

**File:** `frontend/src/api/client.js`
**Function:** `apiClient()` — response handler

```javascript
const data = await response.json();
```

**Transformation:** HTTP response body (JSON bytes) → JavaScript object.

---

### Step 25 — State Update & Render (Frontend)

**File:** `frontend/src/components/mainsearchbar.jsx`

The response object flows into React state:

```javascript
setResult(data);  // data = {query, response, articles, citations, ollama_status}
```

This triggers re-render of `Resultdisplay`, which passes articles to `ArticleCard`, which uses `HighlightText` to mark matched terms.

**Transformation:** JavaScript object → DOM nodes via React rendering.

---

## Data Shape Summary

| Stage | Shape | Size |
|-------|-------|------|
| User input | `"What are the fundamental rights?"` | ~35 chars |
| HTTP request | `{"query": "What...", "use_llm": true}` | ~60 bytes |
| BM25 tokens | `["fundamental", "right"]` | 2 tokens |
| Expanded tokens | `["fundamental", "right", "entitlement", "prerogative"]` | 4 tokens |
| Proximity tokens | `["what", "are", "the", "fundamental", "rights"]` | 5 tokens |
| Query pairs | `[("what","are"), ..., ("fundamental","rights")]` | 10 pairs |
| Candidates | `set` of doc IDs | ~200-400 IDs |
| Per-doc score tuple | `(final, bm25, prox, title_count, doc, matched, exact_matched)` | 7 fields |
| Phase 1 results | `list[dict]` of 50 scored docs | ~50 KB |
| Phase 2 results | `list[dict]` of 8 reranked docs | ~8 KB |
| Promoted articles | `list[dict]` of 8 full-article dicts | ~16 KB |
| LLM context | Single formatted string | ~4096 tokens |
| LLM response | Natural language string | ~100-500 words |
| Final JSON payload | `{query, response, articles[8], citations[8], ollama_status}` | ~20 KB |
| HTTP response | JSON body | ~20 KB |
| MongoDB `referenced_articles` | 8 documents | ~4 KB each |
| MongoDB `messages` | 1 document with 8 refs | ~2 KB |
| React state | JavaScript object | ~20 KB |
| Rendered DOM | Answer markdown + 8 article cards | ~200 DOM nodes |
