# Chapter 5: Implementation

## 5.1 Technology Stack

| Layer | Technology | Version | Justification |
|-------|------------|:-------:|---------------|
| Backend Runtime | Python | 3.13 | Rich NLP/IR library ecosystem |
| Web Framework | Flask | 3.x | Lightweight, Blueprint-based routing |
| Database | MongoDB | 8.0 | Flexible schema for legal data, mongoengine ODM |
| Frontend | React | 19.2.5 | Component model, hooks for state management |
| Build Tool | Vite | 8.0.9 | Fast HMR, native ESM |
| CSS | Tailwind CSS | 4.2.4 | Utility-first, consistent design |
| Routing | react-router-dom | 7.18.1 | Declarative routing, protected routes |
| LLM | Ollama | — | Local LLM hosting, standard API |
| NLP | spaCy | — | Tokenization, lemmatization |

## 5.2 Backend Implementation

### 5.2.1 Entry Point and Application Factory

The application is bootstrapped in `backend/app.py` using a Flask factory pattern:

```python
def create_app():
    app = Flask(__name__)
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    CORS(app)
    db = Database()
    db.connect(db_name="ECIRAS", host="mongodb://localhost:27017")
    return app
```

Key features:
- **Lazy initialization**: spaCy model and search indexes are loaded on the first API request, not at startup
- **Rotating file handler**: logs are written to `logs/backend.log` (10 MB per file, 5 backups)

### 5.2.2 Text Processing Pipeline

File: `backend/src/core/text_processor.py`

The `TextProcessor` class provides configurable text normalization:

```python
class TextProcessor:
    def __init__(self, use_lemmatization=True, remove_stopwords=True):
        self._nlp = get_spacy_pipeline()

    def process_text(self, text):
        tokens = self.normalize_text(text)  # lowercase → contractions → alpha-only
        tokens = self.lemmatize_tokens(tokens)  # if use_lemmatization
        tokens = self._filter_stopwords(tokens)  # if remove_stopwords
        return tokens
```

**Normalization pipeline:**
1. Convert to lowercase
2. Expand 57 English contractions (e.g., "can't" → "cannot", "won't" → "will not")
3. Filter to keep only alphabetic characters and whitespace

**Lemmatization:** Uses spaCy `en_core_web_sm`. Falls back to `spacy.blank("en")` if the model is not installed — tokenization still works but lemmas become identity forms.

**Stopwords:** 125 English stopwords defined in `src/constants/stopwords.py`.

**Two instances** are created with different configurations:
- `bm25_processor`: lemmatization=ON, stopwords=REMOVED
- `proximity_processor`: lemmatization=OFF, stopwords=KEPT

### 5.2.3 BM25 Scoring

File: `backend/src/core/bm25_scorer.py`

The BM25Scorer implements the standard BM25 formula:

```python
class BM25Scorer:
    def __init__(self, tf_index, doc_lengths, avgdl, k1=1.5, b=1.0):
        self.tf_index = tf_index
        self.doc_lengths = doc_lengths
        self.avgdl = avgdl
        self.k1 = k1
        self.b = b
        self.N = len(doc_lengths)

    def idf(self, term):
        df = len(self.tf_index.get(term, {}))
        if df == 0:
            return 0.0
        return math.log((self.N - df + 0.5) / (df + 0.5) + 1)

    def score(self, query_tokens, doc_id):
        doc_len = self.doc_lengths.get(doc_id, 0)
        if doc_len == 0:
            return 0.0
        total = 0.0
        for term in query_tokens:
            tf = self.tf_index.get(term, {}).get(doc_id, 0)
            if tf == 0:
                continue
            idf = self.idf(term)
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
            total += idf * (numerator / denominator)
        return total
```

**Edge case handling:**
- Zero-length documents return 0.0 immediately
- Terms with zero document frequency return 0.0 IDF
- Terms with zero term frequency in a document are skipped

### 5.2.4 Proximity Scoring

File: `backend/src/core/proximity.py`

The ProximityScorer measures the closeness of query term pairs within documents:

```python
class ProximityScorer:
    @staticmethod
    def generate_query_pairs(tokens):
        if len(tokens) <= 5:
            # All unordered pairs
            return [(tokens[i], tokens[j])
                    for i in range(len(tokens))
                    for j in range(i + 1, len(tokens))]
        else:
            # Adjacent pairs only
            return [(tokens[i], tokens[i + 1])
                    for i in range(len(tokens) - 1)]

    def score(self, doc_id, query_pairs, max_window=30, ordered=True):
        if not query_pairs:
            return 0.0
        total = 0.0
        count = 0
        for t1, t2 in query_pairs:
            if t1 == t2:  # skip self-pairs
                continue
            positions1 = self.index.get(t1, {}).get(doc_id, [])
            positions2 = self.index.get(t2, {}).get(doc_id, [])
            if not positions1 or not positions2:
                continue
            dist = self._min_ordered_distance(positions1, positions2)
            if dist is not None and dist <= max_window:
                total += 1.0 / ((dist + 1) ** 2)
                count += 1
        return total / count if count > 0 else 0.0

    @staticmethod
    def _min_ordered_distance(pos1, pos2):
        """Minimum distance where term1 occurs BEFORE term2 (two-pointer sweep)."""
        i = j = 0
        min_dist = float('inf')
        while i < len(pos1) and j < len(pos2):
            if pos1[i] < pos2[j]:
                dist = pos2[j] - pos1[i]
                if dist < min_dist:
                    min_dist = dist
                i += 1
            else:
                j += 1
        return min_dist if min_dist != float('inf') else None
```

### 5.2.5 Search Engine

File: `backend/src/core/search_engine.py`

The SearchEngine orchestrates the first phase of retrieval:

```python
def search(self, query, top_k=None):
    # 1. Prepare query tokens
    base_tokens = self.bm25_processor.process_text(query)
    bm25_tokens = base_tokens[:]
    if self.synonym_expander:
        bm25_tokens = self.synonym_expander.expand(bm25_tokens, query)

    raw_tokens = self.proximity_processor.process_text(query)
    query_pairs = ProximityScorer.generate_query_pairs(raw_tokens)

    # 2. Generate candidates
    candidates = set()
    for token in bm25_tokens:
        if token in self.bm25_scorer.tf_index:
            candidates.update(self.bm25_scorer.tf_index[token].keys())

    # 3. Score all candidates
    scored = []
    for doc in self.documents:
        if doc.doc_id not in candidates:
            continue
        bm25 = self.bm25_scorer.score(bm25_tokens, doc.doc_id)
        if bm25 == 0.0:
            continue
        title_matches = len(set(bm25_tokens) & set(self.title_tokens[doc.doc_id]))
        boosted = bm25 + title_matches * self.title_boost
        prox = self.proximity_scorer.score(doc.doc_id, query_pairs, self.max_window)
        scored.append((boosted + self.proximity_weight * prox, bm25, prox, title_matches, doc, ...))

    scored.sort(key=lambda x: x[0], reverse=True)
    return self._format_results(scored[:top_k])
```

**Constants (from source code):**
| Parameter | Value |
|-----------|:-----:|
| `DEFAULT_PROXIMITY_WEIGHT` | 1.0 |
| `DEFAULT_TITLE_BOOST` | 5.0 |
| `DEFAULT_MAX_WINDOW` | 30 |
| `default_top_k` | 5 (constructor default) |

### 5.2.6 Synonym Expansion

File: `backend/src/core/query_expander.py`

The QueryExpander loads 44 synonym groups from `data/synonyms.json`:

```python
class QueryExpander:
    def expand(self, tokens, raw_query=""):
        result = []
        seen = set()
        for token in tokens:
            self._add_if_new(result, seen, token)
            if token in self.lookup:
                for group_idx, synonyms in self.lookup[token].items():
                    # Multi-word phrases only included if present in raw query
                    if group_idx in self.multi_word_entries:
                        found = any(phrase in raw_norm for phrase in self.multi_word_entries[group_idx])
                        if not found:
                            continue
                    for syn in synonyms:
                        self._add_if_new(result, seen, syn)
        return result
```

Example synonym groups:
- `["arrest", "detention", "custody"]`
- `["right", "entitlement", "prerogative"]`
- `["election", "poll", "ballot"]`

### 5.2.7 Reranker

File: `backend/src/core/reranker.py`

Three-stage reranking pipeline:

```python
def rerank(self, results, top_k=8, boost_rules=None):
    if not results:
        return results
    results = self._rrf_fuse(results)          # Stage 1
    results = self._mmr_diversify(results)      # Stage 2
    results = self._apply_boost(results, boost_rules)  # Stage 3
    return results[:top_k]
```

**Stage 1 — RRF Fusion (k=60):**
```python
def _rrf_fuse(self, results):
    k = self.rrf_k
    bm25_ranks = dict(_ranked("bm25_score"))
    prox_ranks = dict(_ranked("proximity_score"))
    title_ranks = dict(_ranked("title_match_count"))
    for result in results:
        doc_id = result["doc_id"]
        rrf = 1.0/(k + bm25_ranks.get(doc_id, n))
        rrf += 1.0/(k + prox_ranks.get(doc_id, n))
        rrf += 1.0/(k + title_ranks.get(doc_id, n))
        result["rrf_score"] = rrf
    results.sort(key=lambda x: x["rrf_score"], reverse=True)
    return results
```

**Stage 2 — MMR Diversity (λ=0.5):**
```python
def _mmr_diversify(self, results):
    selected = [results[0]]
    candidates = results[1:]
    while candidates:
        best_idx = 0
        best_mmr = -float("inf")
        for i, cand in enumerate(candidates):
            score = cand.get("rrf_score", cand.get("score", 0.0))
            max_sim = max(cosine_similarity(vec_c, vec_s) for vec_s in vec_selected)
            mmr = self.mmr_lambda * score - (1 - self.mmr_lambda) * max_sim
            if mmr > best_mmr:
                best_mmr = mmr
                best_idx = i
        selected.append(candidates.pop(best_idx))
    return selected
```

**Stage 3 — Rule-Based Boost:**
Default level multipliers:
- `part`: 1.0
- `article`: 0.98
- `clause`: 0.95
- `subclause`: 0.90

$$
\text{final} = \text{score} \times \text{doc.boost} \times \text{part\_rules}[\text{part\_no}] \times \text{level\_rules}[\text{level}]
$$

### 5.2.8 Article Promotion

File: `backend/src/llm/rag_repository.py`

After retrieval, clause/sub-clause results are promoted to article level. The `_build_article_lookup()` method pre-computes the mapping:

```python
def _build_article_lookup(self):
    """Group documents by article_no.
    Articles with lettered sub_clauses keep their text directly.
    Numbered clauses are concatenated with \n---\n separators.
    """
    groups = defaultdict(lambda: {"article_doc": None, "clause_docs": [], ...})
    for doc in self.retrieval.engine.documents:
        key = doc.article_no
        if doc.level == "article":
            groups[key]["article_doc"] = doc
        elif doc.level in ("clause", "sub-clause"):
            groups[key]["clause_docs"].append(doc)
    # Build lookup from groups...
```

The `build_truncated_text()` method returns only matched clause texts for LLM context:

```python
def build_truncated_text(self, article):
    article_no = article["article_no"]
    structure = self._clause_structure.get(article_no)
    if not structure or not structure.get("clauses"):
        return article["text"]
    matched = article.get("matched_clauses", [])
    if not matched:
        return article["text"]
    # Return only matched clause texts
```

### 5.2.9 RAG Workflow

File: `backend/src/llm/rag_workflow.py`

The RAGWorkflow orchestrates retrieval + generation:

```python
def ask(self, query, retrieve_only=False):
    retrieved_articles = self.repo.retrieve(query, top_k=self.max_context_articles)
    promoted_articles = self.repo.promote_to_articles(retrieved_articles)
    result = {"query": query, "retrieved_articles": [...]}

    if retrieve_only:
        return result

    context = self.formatter.format_context(promoted_articles)
    system_prompt = self.formatter.build_system_prompt()
    user_prompt = self.formatter.build_user_prompt(query, context)

    try:
        response = self.repo.call_llm(messages, stream=False)
        result["answer"] = response.message.content
    except Exception as exc:
        result["answer"] = f"Error querying LLM: {str(exc)}"

    return result
```

**LLM call with retry** (`rag_repository.py`):
```python
def call_llm(self, messages, stream=False):
    last_exc = None
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            return self.client.chat(self.model, messages=messages,
                                    stream=stream, keep_alive="30m",
                                    options={"num_ctx": 4096})
        except Exception as exc:
            last_exc = exc
            if attempt < RETRY_ATTEMPTS:
                time.sleep(RETRY_DELAY)
    raise last_exc
```

### 5.2.10 Authentication

File: `backend/controllers/decorators.py`

The `@token_required` decorator:

```python
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
        if not token:
            token = request.cookies.get('token')

        if not token:
            return jsonify({"error": "Token is missing!"}), 401

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            user = _get_user(payload['user_id'])
            if user and payload.get('token_version', -1) < user.token_version:
                return jsonify({"error": "Token has been invalidated."}), 401
            request.user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token!"}), 401

        return f(*args, **kwargs)
    return decorated
```

**Token version invalidation** is implemented in the logout endpoint:

```python
def logout():
    user_id = request.user.get('user_id')
    user = User.objects.get(id=user_id)
    user.token_version += 1
    user.save()
    resp = make_response(jsonify({"message": "Logout successful."}))
    resp.set_cookie('token', '', expires=0, max_age=-1)
    return resp
```

## 5.3 Frontend Implementation

### 5.3.1 API Client

File: `frontend/src/api/client.js`

```javascript
export const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000';

export async function apiClient(endpoint, options = {}) {
    const token = localStorage.getItem('token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${BASE_URL}${endpoint}`, {
        ...options, headers,
        signal: AbortSignal.timeout(100000),
    });
    // ...
}
```

### 5.3.2 Streaming Hook

File: `frontend/src/hooks/useAskStream.js`

```javascript
export function useAskStream() {
    const [articles, setArticles] = useState([]);
    const [response, setResponse] = useState('');
    const [loading, setLoading] = useState(false);
    const controllerRef = useRef(null);

    const startStream = useCallback(async (query, useLlm) => {
        const controller = new AbortController();
        controllerRef.current = controller;
        setLoading(true);

        const res = await fetch(`${BASE_URL}/api/v1/ask-stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}` },
            body: JSON.stringify({ query, use_llm: useLlm }),
            signal: controller.signal,
        });

        const reader = res.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const text = decoder.decode(value);
            // Parse SSE data: lines
            for (const line of text.split('\n')) {
                if (line.startsWith('data: ')) {
                    const event = JSON.parse(line.slice(6));
                    // Handle event types: articles, token, done, error, status
                }
            }
        }
    }, []);
    // ...
}
```

### 5.3.3 UI Components

The frontend uses 9 reusable UI primitives in `frontend/src/components/ui/`:

| Component | Purpose |
|-----------|---------|
| `Button` | Variants: primary/secondary/danger/ghost; sizes: sm/md/lg; loading state |
| `Input` | Floating label, error state, helper text, auto-generated ID |
| `Toggle` | Switch toggle with keyboard support |
| `Card` | Container with optional header/footer |
| `Alert` | Notification banner (error/success/warning/info) with dismiss |
| `Badge` | Inline colored badge |
| `Spinner` | Animated loading spinner |
| `Pagination` | Previous/Next page navigation |
| `Dialog` | Modal confirmation with overlay, Escape key, focus trap |

## 5.4 Offline Ingestion Pipeline

### 5.4.1 Flatten Constitution

File: `backend/preprocessing_scripts/flatten_constitution.py`

Handles two input formats:

**Format 1 — Nested (default):** `nepal_constitution_new.json` with `parts[]` → `articles[]` → `text`/`provision`/`explanation`/`sub_clauses[]`/`clauses[]`

**Format 2 — Flat list:** `nepal_constitution.json` as a list with `article_number`, `part_number`, `title`, `content[]`

Each output document is enriched with:
- **`enriched_text`**: Prepended header with part/article/clause info
- **`title_tokens`**: Pre-tokenized title (BM25-processed)
- **`body_tokens`**: Pre-tokenized enriched text
- **`citation`**: Human-readable citation (e.g., "Part 3, Article 31")
- **`citation_normalized`**: Machine-parseable citation
- **`boost`**: 1.5 for clauses/sub-clauses, 1.0 for articles

### 5.4.2 Build Indexes

File: `backend/src/core/index_builder.py`

```python
class IndexBuilder:
    def build_tf_index(self, documents):
        tf_index = {}
        for doc in documents:
            for token in doc.body_tokens:
                tf_index.setdefault(token, {}).setdefault(doc.doc_id, 0)
                tf_index[token][doc.doc_id] += 1
        return tf_index

    def build_positional_index(self, documents):
        pos_index = {}
        for doc in documents:
            tokens = self.proximity_processor.process_text(doc.enriched_text)
            for pos, token in enumerate(tokens):
                pos_index.setdefault(token, {}).setdefault(doc.doc_id, [])
                pos_index[token][doc.doc_id].append(pos)
        return pos_index

    def compute_doc_stats(self, documents):
        doc_lengths = {doc.doc_id: len(doc.body_tokens) for doc in documents}
        avgdl = sum(doc_lengths.values()) / len(doc_lengths) if doc_lengths else 0.0
        return doc_lengths, avgdl
```

## 5.5 System Constants Summary

| Constant | Value | File |
|----------|:-----:|------|
| BM25 k1 | 1.5 | `bm25_scorer.py:10` |
| BM25 b | 1.0 | `bm25_scorer.py:11` |
| Proximity weight | 1.0 | `search_engine.py:31` |
| Title boost | 5.0 | `search_engine.py:32` |
| Max window | 30 | `search_engine.py:33` |
| RRF k | 60 | `reranker.py:17` |
| MMR λ | 0.5 | `reranker.py:18` |
| Recall k | 30 | `retrieval_workflow.py:15` |
| Reranker top_k | 8 | `retrieval_workflow.py:16` |
| Max context articles | 8 | `rag_workflow.py:17` |
| LLM retry attempts | 3 | `rag_repository.py:13` |
| LLM retry delay | 0.5s | `rag_repository.py:14` |
| LLM context window | 4096 | `rag_repository.py:285` |
| Default LLM model | qwen3:8b | `rag_repository.py:12` |
| Query max length | 500 chars | `api_controller.py:100` |
| JWT expiry | 12h (43200s) | `auth_controller.py:70` |
| MongoDB pool | min=2, max=10 | `db_connect.py:21-22` |
| MongoDB timeout | 5s | `db_connect.py:23-24` |
