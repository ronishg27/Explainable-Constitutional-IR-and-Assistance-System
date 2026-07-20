# Domain Model

## Business Context

We build a **constitutional Q&A system** for the Constitution of Nepal (2072 / 2015). Citizens, legal researchers, and students ask questions in plain English about constitutional provisions, and the system returns the most relevant articles with citations — optionally augmented by an LLM-generated answer grounded strictly in those articles.

This is an **information retrieval** system with a **RAG** layer, not a legal advice platform. The system retrieves what the constitution says; it does not interpret, argue, or apply law to specific cases.

---

## Core Domain Entities

### User

A person who registers, logs in, and asks questions.

```
User
├── fullname (3-50 chars, required)
├── email (unique, required)
├── password_hash (bcrypt, 60 chars)
├── role (user | admin)
└── token_version (integer, incremented on logout)
```

**Business rules:**
- Email must be unique — no two users can share an email
- Password is never stored in plaintext; only the bcrypt hash is kept
- `token_version` is a monotonic counter: incrementing it invalidates all existing JWTs for that user
- Role defaults to `user`; admin routes are not yet exposed

**Identity:** identified by a MongoDB ObjectId; authenticated via JWT

---

### Message

A single Q&A exchange between a user and the system.

```
Message
├── query (string, required, ≤500 chars)
├── answer (string, optional — empty if LLM was not used)
├── user (reference → User, required)
├── articles (list of references → ReferencedArticle)
├── created_at
└── updated_at
```

**Business rules:**
- Every message belongs to exactly one user (ownership)
- Deleting a user CASCADE-deletes their messages
- A message can reference zero or more articles (retrieval-only mode has articles but no answer)
- `answer` is empty when `use_llm=false`
- The `query` is the user's original question — never modified after creation

**Identity:** MongoDB ObjectId

---

### ReferencedArticle

A constitutional provision that was retrieved and presented to the user as part of an answer. This is a **snapshot** — the article's text and scores are frozen at query time.

```
ReferencedArticle
├── title (e.g., "Right relating to education")
├── citation (e.g., "Part 3, Article 31")
├── doc_id (unique, from the flattened corpus)
├── relevance_score (combined final score after reranking)
├── bm25_score
├── proximity_score
├── title_match_count
├── article_no
├── clause_no
├── subclause_id
├── level (article | clause | subclause)
├── part_no
├── text (truncated context for LLM)
├── full_text (complete provision text)
├── content (cleaned body, without enriched-text headers)
├── matched_terms (lemmatized query terms that matched)
├── exact_matched_terms (raw query terms that matched)
├── created_at
└── updated_at
```

**Business rules:**
- `doc_id` is unique across the corpus — used for upsert deduplication
- `relevance_score` is the canonical ranking signal after all reranking stages
- Matched terms drive frontend highlighting in `ArticleCard.jsx`
- Articles can be shared across messages (many-to-many via reference list)
- Deleting an article NULLIFIES the reference (messages keep working, the article data remains in the referenced_articles collection)

**Identity:** MongoDB ObjectId

---

### Document (IR Engine Internal)

The IR engine's representation of a single row in the flattened constitution corpus. This is an **internal domain entity** — it is never exposed to the API or frontend.

```
Document (dataclass)
├── doc_id (unique string)
├── part_no
├── article_no
├── title
├── text (enriched with Part/Article/Clause headers)
├── citation (human-readable, e.g. "Part 3, Article 16")
├── level (part | article | clause | subclause)
├── clause_no (optional)
├── subclause_id (optional)
├── is_primary
├── parent_id
├── raw_text (optional — original text without enrichment)
├── citation_normalized (optional)
└── boost (float, default 1.0 — per-document scoring multiplier)
```

**Business rules:**
- One Document per line in the flattened JSON corpus (~700 documents)
- `boost` is authored per document and influences the rule-based reranking stage
- `level` determines how the document is treated during article promotion (clause/sub-clause docs get merged into full article texts)
- `doc_id` ties back to the `ReferencedArticle.doc_id` for persistence

---

## Supporting Domain Concepts

### SearchEngine + Reranker (The Retrieval Pipeline)

Not entities — these are **domain services** that execute the core business logic.

- **SearchEngine** — accepts a query, returns scored candidate documents using BM25 + title boost + proximity scoring
- **Reranker** — refines candidate list through RRF fusion, MMR diversity, and rule-based boost
- **RetrievalWorkflow** — composes SearchEngine + Reranker into a single pipeline step

### RAGWorkflow

The **orchestrator** that wires retrieval, article promotion, and LLM generation into the Q&A answer.

### QueryExpander

A **domain service** that expands query tokens with synonyms (44 groups) to improve recall across legal terminology variants (e.g., "right" ↔ "entitlement" ↔ "prerogative").

---

## Relationships

```
User (1) ── owns ──→ Message (0..*)
Message (0..*) ── references ──→ ReferencedArticle (0..*)

Document (~700) ── flattened_from ──→ Constitution JSON (1)
ReferencedArticle.snapshot_of ──→ Document (N:1 via doc_id)

RAGWorkflow
  ├── uses ──→ RetrievalWorkflow
  │             ├── uses ──→ SearchEngine
  │             │             ├── uses ──→ BM25Scorer
  │             │             ├── uses ──→ ProximityScorer
  │             │             └── uses ──→ QueryExpander
  │             └── uses ──→ Reranker
  ├── uses ──→ RAGFormatter
  └── uses ──→ OllamaClient (via RAGRepository)
```

---

## Aggregates

### Aggregate Root: User

```
User Aggregate
├── User (root)
│   └── Messages (owned entities — CASCADE delete)
│       └── ReferencedArticles (referenced, not owned)
```

- Deleting a User deletes all their Messages
- Messages survive if their ReferencedArticles are deleted (NULLIFY)

### Aggregate Root: ReferencedArticle (standalone)

- No child entities
- Referenced by zero or more Messages
- Lifecycle independent of any User

---

## Business Rules (Invariants)

| Rule | Enforced At | Rationale |
|------|-------------|-----------|
| Query ≤ 500 characters | Controller (`_parse_ask_request`) | Prevents abuse and keeps latency predictable |
| JWT must match user's current `token_version` | Decorator (`token_required`) | Logout must invalidate all existing sessions immediately |
| LLM answer must cite article(s) | RAGFormatter prompts (not programmatically enforced) | Legal answers need traceability to source text |
| LLM must say "not found" if context lacks answer | System prompt instruction (not programmatically enforced) | Prevents hallucination of non-constitutional content |
| Article scores are frozen at query time | `ReferencedArticle.to_json()` captures scores | Historical accuracy — old messages reflect old ranking |
| Email uniqueness | MongoDB unique index on `User.email` | No duplicate accounts |
| Synonym expansion only for BM25, not proximity | `SearchEngine.search()` code logic | Proximity needs original ordering; synonyms would corrupt it |
| Two text processors (BM25 + proximity) | EngineFactory | BM25 needs lemmatized + stopword-free; proximity needs raw tokens with stopwords preserved |
| Short queries use all term pairs; long queries use adjacent only | `ProximityScorer.generate_query_pairs()` | O(n²) blowup protection for long queries |
| spaCy `en_core_web_sm` preferred, blank `en` fallback | `get_spacy_pipeline()` | Graceful degradation if model not installed |

---

## Terminology

| Term | Definition |
|------|------------|
| **Article** | A numbered section of the Constitution (e.g., Article 16 — "Right to live with dignity") |
| **Part** | A group of related articles (e.g., Part 3 — "Fundamental Rights") |
| **Clause** | A numbered subsection within an article (e.g., Article 16(1)) |
| **Sub-clause** | A lettered sub-division within a clause (e.g., Article 16(1)(a)) |
| **Level** | One of `part`, `article`, `clause`, `subclause` — determines how the document is scored and promoted |
| **Flattened corpus** | The nested constitution JSON transformed into a flat list of ~700 Documents, one per leaf node |
| **Article promotion** | The process of merging clause/sub-clause search results into full article texts for user display |
| **Score** | The combined relevance signal after BM25 + proximity + title boost + RRF + MMR + rule boost |
| **Citation** | Human-readable reference string (e.g., "Part 3, Article 31") |
| **Matched terms** | Lemmatized query tokens that had non-zero tf in the BM25 index for a given document |
| **Enriched text** | Document text with "Part X Article Y\nClause Z" headers prepended by the flattening script |
| **Token version** | A counter on each User document; incrementing it invalidates all existing JWTs for that user |

---

## What the Domain is NOT

- **Not a legal reasoning system** — no case law, no precedent, no statutory interpretation
- **Not a document management system** — the constitution corpus is static, not user-editable
- **Not a citation graph** — articles are standalone, not linked to each other
- **Not a chatbot** — each query is independent, no conversation state beyond history persistence
- **Not an embedding/vector search system** — all retrieval is algorithmic (BM25 + proximity + RRF/MMR); no dense embeddings
