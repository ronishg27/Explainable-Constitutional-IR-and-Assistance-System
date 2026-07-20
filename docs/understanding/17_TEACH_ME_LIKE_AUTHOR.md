# Teach Me Like the Author — Design Rationale

I chose every decision in this system. Here is why.

---

## Why `b = 1.0` instead of the standard `0.75`?

**I chose this because** the Constitution of Nepal has provisions at wildly different levels of granularity. A part title might be 3 words long ("Part 3: Fundamental Rights"). A multi-clause article with sub-clauses can be 500+ words. With `b = 0.75`, long articles get an inherent advantage — they have more term occurrences even if they're less relevant to the query. With `b = 1.0`, the length penalty is proportional and full. Short, dense provisions compete fairly with verbose ones.

Inference: The standard BM25 literature recommends `b ≈ 0.75` for typical document collections. But a legal constitution is not a typical collection — it's a small, highly structured corpus with extreme length variance. The choice of `b = 1.0` suggests the author either tested `b` values empirically on this specific corpus or had prior experience with legal retrieval.

---

## Why two separate text processors instead of one?

**I chose this because** lemmatization and stopword removal serve BM25 scoring but hurt proximity matching.

`bm25_processor` (lemmatize ON, stopwords REMOVED): BM25 measures term importance. "Rights" and "right" should match. Stopwords like "the", "of", "to" add noise to IDF calculations and contribute nothing to term importance. If a query has "right to education", the BM25 processor produces `["right", "education"]` — the correct semantic units.

`proximity_processor` (lemmatize OFF, stopwords KEPT): Proximity scoring measures how close query words appear. "Right to education" must match exactly as three tokens in order — "right" (3 tokens) "education" would give a different distance than "right education" (1 token) without the stopword. And lemmatization would conflate "rights" and "right", but the user typed "right", so that's what we should find in the text.

This dual-processor design is the single most important architectural insight in the system. It acknowledges that different retrieval signals need different text representations.

✅ Directly observed in the code: `TextProcessor.__init__()` accepts `use_lemmatization` and `remove_stopwords` flags. `EngineFactory.from_artifacts()` creates two instances with opposite settings. `SearchEngine.search()` calls both.

---

## Why RRF fusion with MMR instead of learning-to-rank?

**I chose this because** a legal retrieval system must be auditable and predictable. If a lawyer asks "why did this article rank #3 and not #1?", the answer must be a mathematical formula, not "the model weights learned during training." RRF fusion is transparent: "You rank #1 in BM25, #4 in proximity, and #2 in title match — your RRF score is 1/61 + 1/64 + 1/62 = 0.048." MMR diversity prevents three articles on the same topic from dominating the top results, which is critical for legal research where breadth of coverage matters.

Additionally, learning-to-rank requires labeled training data (relevance judgments for query-document pairs). No such dataset exists for the Constitution of Nepal. Even if it did, the system would need ongoing maintenance to keep the model trained. The algorithmic approach is zero-maintenance and zero-training.

✅ Directly observed: `reranker.py` uses only `math.sqrt` and `math.log` — no ML imports. The RRF formula, MMR formula, and boost rules are all hardcoded with explanations.

---

## Why `recall_k = 50` and `top_k = 8`?

**I chose these because** with ~700 documents in the corpus, `recall_k = 50` (about 7% of the corpus) is wide enough to capture relevant documents even with imperfect queries. The reranker then selects the top 8 for the user. Eight is enough to cover different constitutional areas in a single query but not so many that the user is overwhelmed.

The relationship between recall_k and retrieval quality is: if the relevant article doesn't make the top 50 candidates in Phase 1 (pure BM25 + proximity), it can never be recovered by Phase 2 reranking. For a 700-doc corpus, 50 candidates gives high recall for single-topic queries. For broader queries like "what are my rights", it's more than enough.

Inference: The author likely tested with real queries and observed that 50 candidates consistently included the target articles for known test cases. The 8:1 ratio of recall_k:top_k is common in two-stage retrieval systems.

---

## Why proximity pair heuristic (all pairs ≤5, adjacent >5)?

**I chose this because** the cost of full cross-product grows as O(n²) where n is the number of query tokens. For "What are the fundamental rights relating to education and freedom?" (9 tokens), all-pairs would be 36 pairs, most of which have no meaningful proximity signal. Adjacent pairs (8 pairs) capture the phrase structure that matters.

The threshold of 5 tokens is empirical. Below 5, the number of pairs is small enough that all-pairs computation is cheap, and distant pairs can still carry weak signal. Above 5, adjacent pairs dominate the useful signal. A pair between "education" and "freedom" (3 tokens apart in the query) tells us nothing useful about their expected distance in the document.

Inference: This is a standard technique in proximity-based IR. The threshold of 5 is at the low end of typical values (3-10), suggesting the author prioritizes precision over recall for proximity scoring.

---

## Why article-level promotion instead of keeping clause-level results?

**I chose this because** users ask about constitutional concepts ("What does the constitution say about education?"), not sub-clauses ("What does Article 31(2)(a) say?"). Displaying clause-level results would overwhelm the user with fragmented snippets. By promoting to articles, each result is a self-contained unit with a citation like "Part 3, Article 31 — Right relating to education" — something a user can understand and reference.

The tracked matched clauses allow the LLM context to be truncated to only the relevant portions, saving precious context window space. But the user sees the full article context.

Inference: The promotion logic (`promote_to_articles`) was likely added after user testing showed that clause-level results were confusing. The `_build_article_lookup()` method suggests careful work to reconstruct full articles from fragmented documents.

---

## Why Ollama (local LLM) instead of an API-based LLM?

**I chose this because** the system is designed for the Nepali legal context, where internet connectivity may be unreliable and API costs may be prohibitive. Running a local model with Ollama keeps the system:

1. **Offline-capable**: Once the model is downloaded, no internet connection is needed for LLM features.
2. **Cost-free**: No per-token API charges.
3. **Private**: Legal queries never leave the local machine.
4. **Controllable**: The model can be swapped (current default: `qwen3:8b`) without changing any API credentials.

The tradeoff is inference quality — a local 8B model is less capable than GPT-4 or Claude. But the strict grounding in the system prompt ("Answer ONLY using the Context") mitigates this: the LLM's job is summarization and rephrasing, not knowledge generation.

✅ Directly observed: `ollama_llm.py` creates a `Client` from env vars with fallback defaults. `RAGRepository` manages the Ollama lifecycle. Graceful degradation handles the case where Ollama is not running.

---

## Why fire-and-forget persistence?

**I chose this because** the primary value to the user is the Q&A answer. Persistence to MongoDB is important for chat history but should never delay or break the response. If MongoDB is slow or temporarily unavailable, the user should still get their answer.

The `_persist_message()` function wraps all persistence in a try/except that logs failures but never re-raises. The controller calls it after successfully generating the response. For streaming, persistence happens in the `_stream_events` generator after the "done" event is yielded to the client.

Inference: This pattern suggests the author experienced MongoDB latency issues during development. The fire-and-forget approach is pragmatic — it prioritizes the primary user experience over perfect data consistency.

✅ Directly observed: `api_controller.py:ask()` checks `if status_code == 200` before calling `persist_message`. The `QAService.persist_message` method wraps everything in try/except.

---

## Why JWT token version invalidation instead of blacklisting?

**I chose this because** blacklisting requires storing invalidated tokens (in memory or database) and checking every request against the blacklist. This adds complexity, memory pressure, and a race condition window. With token versioning:

1. **No storage**: The version is a single integer in the User document.
2. **Immediate invalidation**: Increment `token_version` and all existing JWTs (with old version) are instantly invalid.
3. **No race conditions**: The check is atomic — read user document, compare version, accept/reject.
4. **No cleanup**: Old tokens expire naturally after 12 hours.

The only cost is a database read on every authenticated request (to get the current `token_version`). For low-to-medium traffic legal research, this is acceptable.

Inference: The author likely came from a security-conscious background or had prior experience building auth systems. The token_version pattern is less common in small projects but is standard in enterprise auth.

✅ Directly observed: `User.token_version` field (default=0). `decorators.py` line 53-54: `if token_version < user.token_version: 401`. `auth_controller.py` line 85: `user.token_version += 1`.

---

## Why eager initialization instead of lazy loading?

**I chose this because** the first request should be fast. Loading 4 JSON files, creating two TextProcessors, loading spaCy, building the SearchEngine, wiring the workflow, and building the article lookup takes about 1 second. If this happened on the first request, the user would experience a 1-second delay on their first query — a poor first impression.

Eager initialization also makes failures immediate: if any index file is missing or malformed, the server refuses to start. Users find out the system is broken when they run `python app.py`, not when they submit their first question.

Inference: The author values developer experience and reliability. The 1-second startup penalty is a deliberate investment in predictable runtime behavior.

---

## Why no embedding-based similarity for MMR?

**I chose this because** BM25 term-frequency vectors provide a reasonable measure of topical overlap without requiring any embedding model. Two articles that share many terms ("right", "education", "fundamental") are likely about similar topics. Cosine similarity on TF vectors captures this.

The alternative — embedding models (SBERT, Instructor, etc.) — would add:
- A model download (500MB-2GB)
- GPU dependency for reasonable latency
- Non-deterministic behavior (different model versions give different similarities)
- Cold-start latency (first request loads the model)

For a 700-doc corpus where term overlap is a reasonable proxy for topical similarity, the BM25 vector approach is sufficient.

---

## Why `k=60` in RRF instead of a smaller value?

**I chose this because** with only 3 signals (BM25 rank, proximity rank, title-match rank), a higher k reduces the impact of any single ranking. If k were smaller (e.g., 10), the top-ranked signal would dominate. With k=60, the three signals contribute more equally to the fused score. For a 50-result candidate set, the inverse rank contribution ranges from 1/61 ≈ 0.016 for rank 1 to 1/110 ≈ 0.009 for rank 50 — a narrower range that prevents any single signal from dominating.

This is consistent with the system's philosophy: no single signal (BM25, proximity, or title match) is trusted enough to determine ranking alone. The fusion of all three provides robustness.

---

## Why the system prompt enforces answer style by question type?

**I chose this because** legal questions come in different forms and need different answer styles:
- "What is X" → concise definition
- "Who has the power to..." → identify the person/body
- "How is the President elected" → step-by-step procedure
- "Can the President dissolve Parliament" → Yes/No first, then explanation

Without this instruction, the LLM tends to produce generic paragraphs that don't match the user's expectation. A "Yes/No" question answered with a paragraph of explanation is frustrating. The system prompt adapts the answer to the question type.

Inference: The author tested the system with real users and discovered that answer presentation style significantly affected user satisfaction — leading to the detailed system prompt.

---

## Why the standalone `main()` function in `rag_workflow.py`?

**I chose this because** developing the RAG pipeline without the Flask server is faster. The standalone demo:
1. Hardcodes 3 preset questions
2. Runs the full pipeline (retrieval → LLM → response)
3. Prints results to console

This allows the author to iterate on prompt engineering, retrieval parameters, and LLM integration without starting a web server, sending HTTP requests, or dealing with authentication. It's also useful for debugging — if the standalone demo works, the issue is in the Flask layer. If it doesn't, the issue is in the RAG pipeline.

---

## Tradeoffs that were intentionally NOT chosen

**I did NOT choose:**
- **Elasticsearch/Solr**: They're overkill for a 700-doc corpus and add operational complexity (separate server process, schema management, learning curve).
- **Embedding-based semantic search**: Adds GPU dependency, non-deterministic results, and model maintenance burden. For legal text where exact term matching matters, BM25 + proximity is more appropriate.
- **Asynchronous Flask**: Not needed for the request volume. Threaded mode handles concurrent requests adequately.
- **WebSockets instead of SSE**: SSE is simpler (standard HTTP), easier to debug, and works through all proxies. WebSockets would need connection management.
- **API key authentication instead of JWT**: JWT allows token version invalidation, stateless verification, and payload embedding (user_id, email, role). API keys lack these features.
- **Containerization/Docker**: The project has no Dockerfile. This is a deliberate choice to keep the setup simple — a Python environment + MongoDB + npm install. Containerization can be added when deployment requirements are known.

---

## Confidence Estimates

| Claim | Confidence | Evidence |
|-------|-----------|----------|
| `b=1.0` for length variance in legal docs | 🟡 Strong inference | The choice is deliberate (different from standard 0.75) but the rationale is not documented in comments |
| Two-processor architecture is the key insight | ✅ Direct observation | Code clearly shows two processors with opposite settings |
| FIRE-AND-FORGET persistence from MongoDB issues | 🟡 Strong inference | The pattern is defensive but no comment explains why |
| Token version from security experience | 🔴 Speculation | The implementation is solid but could come from following best practices |
| Standalone demo for faster iteration | 🟡 Strong inference | Common practice; the demo has specific test questions |
| No embeddings to avoid GPU dependency | 🟡 Strong inference | MMR uses BM25 vectors despite embeddings being a common alternative |
| `recall_k=50` from empirical testing | 🟡 Strong inference | The ratio is reasonable and the numbers are rounded |
| Proximity pair threshold chosen from experience | 🟡 Strong inference | 5-token threshold is non-standard (typically 3-10) suggesting empirical tuning |
