# Call Graph — Most Important Execution Paths

---

## Path 1: Synchronous Q&A — `POST /api/v1/ask`

The primary path, exercised on every search or answer request.

```
routes/api_routes.py:30       ask_route()
                                │
controllers/decorators.py:30   decorated()          ← @token_required
  ├── request.headers.get('Authorization')           extracts Bearer token
  ├── jwt.decode(token, JWT_SECRET)                  validates signature + expiry
  ├── _get_user(payload.user_id)                     MongoDB: User.objects(id=...)
  │     └── User.objects(id=user_id).first()         token_version check
  └── request.user = payload                         attaches identity
                                │
controllers/api_controller.py:62  ask()
  ├── _parse_ask_request()                           validates JSON, query ≤ 500 chars
  ├── QAService.answer_query(query, use_llm=True)    ← phase boundary: HTTP → domain
  │     │
  │     services/qa_service.py:84  answer_query()
  │       └── QAService._get_workflow()              returns module-global RAGWorkflow
  │             │
  │             src/llm/rag_workflow.py:53  ask()
  │               │
  │               ├── _prepare_articles(query)
  │               │     │
  │               │     ├── repo.retrieve(query, top_k=8)
  │               │     │     │
  │               │     │     src/llm/rag_repository.py:213  retrieve()
  │               │     │       └── self.retrieval.retrieve(query, top_k=8)
  │               │     │             │
  │               │     │             src/workflows/retrieval_workflow.py:23  retrieve()
  │               │     │               │
  │               │     │               ├── engine.search(query, top_k=50)
  │               │     │               │     │
  │               │     │               │     src/core/search_engine.py:79  search()
  │               │     │               │       │
  │               │     │               │       ├── bm25_processor.process_text(query)
  │               │     │               │       │     └── src/core/text_processor.py:93
  │               │     │               │       │           process_text()
  │               │     │               │       │             ├── normalize_text()     lowercase + contractions + alnum filter
  │               │     │               │       │             ├── lemmatize_tokens()   spaCy (cached pipeline)
  │               │     │               │       │             └── _filter_stopwords()  120-word list
  │               │     │               │       │
  │               │     │               │       ├── synonym_expander.expand(tokens, query)
  │               │     │               │       │     └── src/core/query_expander.py:38  expand()
  │               │     │               │       │           44 groups → expanded token list
  │               │     │               │       │
  │               │     │               │       ├── prox_processor.process_text(query)
  │               │     │               │       │     └── TextProcessor.process_text()   no lemmatize, keeps stopwords
  │               │     │               │       │
  │               │     │               │       ├── ProximityScorer.generate_query_pairs(raw_tokens)
  │               │     │               │       │     └── src/core/proximity.py:29
  │               │     │               │       │           ≤5 tokens → all pairs, >5 → adjacent only
  │               │     │               │       │
  │               │     │               │       ├── _generate_candidates(bm25_tokens)
  │               │     │               │       │     union of tf_index[token].keys()
  │               │     │               │       │
  │               │     │               │       └── for each candidate doc:
  │               │     │               │             _score_document(doc, tokens, pairs)
  │               │     │               │               ├── BM25Scorer.score(tokens, doc_id)     ← src/core/bm25_scorer.py:27
  │               │     │               │               ├── title_match_count × 5.0
  │               │     │               │               ├── ProximityScorer.score(doc_id, pairs)  ← src/core/proximity.py:67
  │               │     │               │               └── final = bm25 + title_bonus + 1.0 × prox
  │               │     │               │
  │               │     │               │         sort by final DESC → return top 50
  │               │     │               │
  │               │     │               └── reranker.rerank(initial_results, top_k=8)
  │               │     │                     │
  │               │     │                     src/core/reranker.py:164  rerank()
  │               │     │                       │
  │               │     │                       ├── _rrf_fuse(results)
  │               │     │                       │     rank by BM25 + rank by proximity + rank by title
  │               │     │                       │     rrf = Σ 1/(60 + rank) for each signal
  │               │     │                       │
  │               │     │                       ├── _mmr_diversify(results)
  │               │     │                       │     λ=0.5, cosine similarity on sparse TF vectors
  │               │     │                       │     iteratively selects max-mmr candidate
  │               │     │                       │       └── _cosine_similarity(vec_a, vec_b)
  │               │     │                       │       └── _get_tf_vector(doc_id)    ← lazy-built cache
  │               │     │                       │
  │               │     │                       └── _apply_boost(results)
  │               │     │                             score × boost × part_rules[part] × level_rules[level]
  │               │     │
  │               │     └── repo.promote_to_articles(raw_results)
  │               │           │
  │               │           src/llm/rag_repository.py:175  promote_to_articles()
  │               │             ├── group by article_no
  │               │             ├── merge clause docs → full article text
  │               │             ├── deduplicate (first occurrence wins)
  │               │             └── track matched clauses per article
  │               │
  │               ├── repo.check_ollama_connection()        ← cached, may be no-op
  │               │     └── self.client.list()              HTTP GET to Ollama
  │               │
  │               ├── repo.check_model_availability()
  │               │     └── "qwen3:8b" in self._available_models
  │               │
  │               ├── formatter.format_context(articles)    ← src/llm/rag_formatter.py:5
  │               ├── formatter.build_system_prompt()       ← src/llm/rag_formatter.py:19
  │               ├── formatter.build_user_prompt(query, ctx) ← src/llm/rag_formatter.py:44
  │               │
  │               └── repo.call_llm(messages, stream=False)
  │                     │
  │                     src/llm/rag_repository.py:320  call_llm()
  │                       └── for attempt in 1..3:           ← retry loop
  │                             client.chat(model, messages,
  │                               keep_alive="30m",
  │                               options={"num_ctx": 4096})
  │                                                     ← HTTP POST to Ollama /api/chat
  │
  ├── QAService.persist_message(user_id, query, payload)
  │     │
  │     services/qa_service.py:43  persist_message()
  │       │
  │       ├── for each article in payload:
  │       │     ArticleService.create_article(...)
  │       │       │
  │       │       services/article_service.py:11  create_article()
  │       │         ├── ReferencedArticle.objects(doc_id=...).first()
  │       │         ├── existing.save()  OR  ReferencedArticle(...).save()
  │       │         └── return {success, data}
  │       │
  │       └── MessageService.create_message(user_id, query, answer, article_ids)
  │             │
  │             services/message_service.py:16  create_message()
  │               ├── User.objects.get(id=user_id)
  │               ├── ReferencedArticle.objects.get(id=...) for each ref
  │               └── Message(query, answer, user, articles).save()
  │
  └── jsonify(payload), 200                                ← phase boundary: domain → HTTP
```

---

## Path 2: Streaming Q&A — `POST /api/v1/ask-stream`

Same retrieval path, different response delivery.

```
controllers/api_controller.py:116  ask_stream()
  ├── _parse_ask_request()                            same validation
  ├── QAService.answer_query_streaming(query, use_llm=True)
  │     └── services/qa_service.py:90  answer_query_streaming()
  │           └── workflow.ask_streaming(query, use_llm=True)
  │                 │
  │                 src/llm/rag_workflow.py:122  ask_streaming()   ← GENERATOR
  │                   │
  │                   ├── _prepare_articles(query)    same retrieval as sync path
  │                   │     └── repo.retrieve → ... → search → rerank → promote
  │                   │
  │                   ├── yield {"type": "articles", articles: [...]}
  │                   │         ← SSE event sent to client immediately
  │                   │
  │                   ├── check_ollama_connection()
  │                   ├── check_model_availability()
  │                   │
  │                   ├── format_context / build_system_prompt / build_user_prompt
  │                   │
  │                   └── repo.call_llm(messages, stream=True)
  │                         │
  │                         rag_repository.py:320  call_llm()
  │                           └── client.chat(model, messages, stream=True)
  │                                 │                ← Ollama returns generator
  │                                 for part in response:          ← token loop
  │                                   yield {"type": "token", "content": ...}
  │                                                   ← SSE event per token
  │
  └── Response(stream_with_context(_stream_events(...)),
               mimetype="text/event-stream")
        │
        controllers/api_controller.py:90  _stream_events()   ← consumer of upstream generator
          ├── for event in events:
          │     if type == "articles": store articles_data
          │     if type == "token":    append to full_answer
          │     if type == "done":
          │       QAService.persist_message(...)           persistence after stream ends
          │     yield f"data: {json.dumps(event)}\n\n"     ← SSE-serialized event
          │
          └── Response closes when generator is exhausted
```

---

## Path 3: Login — `POST /api/v1/auth/login`

```
routes/auth_routes.py:14      login_user()
  │
controllers/auth_controller.py:42  login()
  │
  ├── request.get_json(), validate email + password
  │
  ├── UserService.authenticate(email, password)
  │     │
  │     services/user_service.py:20  authenticate()
  │       ├── User.objects.get(email=email)              MongoDB query
  │       ├── user.check_password(password)              bcrypt.checkpw
  │       └── return user
  │
  ├── jwt.encode(payload={user_id, token_version, exp}, JWT_SECRET)
  │
  └── jsonify({token, user})
      + set_cookie('token', ..., httpOnly=True, SameSite='Strict')
```

---

## Path 4: Registration — `POST /api/v1/auth/register`

```
controllers/auth_controller.py:8  register()
  │
  ├── validate fullname (3-50), email (regex), password (≥6), role
  │
  ├── UserService.create_user(fullname, email, password, role)
  │     │
  │     services/user_service.py:8  create_user()
  │       ├── User(fullname, email, role)
  │       ├── user.set_password(password)                bcrypt.gensalt + hashpw
  │       ├── user.save()                                MongoDB insert
  │       └── return user.to_json()
  │
  └── jsonify({success, data: user})
```

---

## Path 5: Chat History — `GET /api/v1/messages`

```
controllers/api_controller.py:143  list_messages()
  │
  ├── request.args.get("limit", 20, type=int)
  ├── request.args.get("skip", 0, type=int)
  │
  └── MessageService.get_user_messages(user_id, limit, skip)
        │
        services/message_service.py:75  get_user_messages()
          ├── User.objects.get(id=user_id)
          ├── Message.objects(user=user)
          │         .order_by('-created_at')
          │         .skip(skip)
          │         .limit(limit)
          └── return {success, data: [msg.to_json()], pagination: {total, limit, skip, has_more}}
```

---

## Path 6: Ingestion (Offline) — `python -m preprocessing_scripts.run_ingestion`

```
preprocessing_scripts/run_ingestion.py
  │
  ├── flatten_constitution.py:flatten_constitution()
  │     └── reads data/nepal_constitution_new.json
  │         → yields ~700 Document objects
  │         → writes data/output/flattened_nepal_constitution.json
  │
  └── IngestionWorkflow.build_indexes(flat_path, output_dir)
        │
        src/workflows/ingestion_workflow.py
          │
          ├── load flat JSON → list[Document]
          │
          ├── IndexBuilder(bm25_processor, prox_processor)
          │     │
          │     src/core/index_builder.py
          │       ├── build_tf_index(documents)
          │       │     per doc: BM25 process → count term frequencies
          │       ├── build_positional_index(documents)
          │       │     per doc: prox process → record positions
          │       └── compute_doc_stats(documents)
          │             doc lengths + avgdl
          │
          └── save_json(tf_index, "data/output/tf_index.json")
              save_json(pos_index, "data/output/pos_index.json")
              save_json(doc_stats, "data/output/doc_stats.json")
```

---

## Cross-Cutting Concerns

### Async Boundaries

| Boundary | Type | Details |
|----------|------|---------|
| `answer_query_streaming()` | **Generator** (not async) | Uses Python generators with `yield`, not `async def`. The streaming pipeline is synchronous — each token blocks the thread. |
| `_stream_events()` | **Generator consumer** | Reads from an upstream generator, wraps events in SSE format. No true async I/O. |
| `ArticleService.create_article() async def` | **Misleading async** | Declared `async def` but calls sync mongoengine internally. The `async` keyword is a no-op — there is no `await` anywhere. |

### Retry Loops

| Location | Attempts | Delay | Trigger |
|----------|:--------:|:-----:|---------|
| `RAGRepository.call_llm()` | 3 | 0.5s | Ollama HTTP failure or timeout |
| `_perform_ollama_check()` | 1 | — | Checked on first LLM request (cached afterward) |

### Callbacks

None. The codebase uses no callback-based patterns. All orchestration is synchronous and sequential.

### Background Jobs

None. Every operation runs inline in the request thread. The only approximation is the **fire-and-forget persistence** in `QAService.persist_message()` — MongoDB failures are logged but never break the HTTP response.

### Recursion

None. All loops are iterative (`for`, `while`) or generator-based (`yield from`).

---

## Call Graph Summary Statistics

| Metric | Value |
|--------|-------|
| Deepest call chain (sync `/ask`) | ~25 nested calls |
| Distinct functions invoked per `/ask` | ~40 |
| Network calls per `/ask` (LLM) | 1–3 (Ollama /api/chat with retry) |
| Network calls per `/ask` (no LLM) | 0 |
| MongoDB queries per `/ask` | 3 (token_version user lookup + N article upserts + 1 message create) |
| Generators | 2 (`ask_streaming`, `_stream_events`) |
| Retry loops | 1 (`call_llm`) |
| Recursion depth | 0 |
| Async/await usage | 0 (all sync) |
| Background threads | 0 |
