# Chapter 6: Testing and Evaluation

## 6.1 Testing Strategy

The system employs a multi-level testing approach:

1. **Unit Testing**: Individual components (BM25Scorer, ProximityScorer, TextProcessor)
2. **Integration Testing**: Pipeline orchestration (RetrievalWorkflow, RAGWorkflow)
3. **API Testing**: Endpoint validation via Postman collections
4. **Error Handling Verification**: Graceful degradation scenarios

## 6.2 Test Suite

Tests are located in `backend/temp/tests/` and run with pytest.

### 6.2.1 Test Coverage Areas

| Area | Test Focus | Example Cases |
|------|------------|---------------|
| BM25 Scoring | Score computation, edge cases | Zero IDF terms, zero-length docs |
| Proximity Scoring | Pair generation, distance metric | Short vs long queries, self-pairs |
| Text Processing | Tokenization, lemmatization, stopwords | Contractions, empty text |
| Search Engine | Candidate generation, result ranking | Single-token queries, stopword-only queries |
| Reranker | RRF fusion, MMR diversity, boost rules | Single result, no boost rules |
| API Endpoints | Request validation, auth enforcement | Missing fields, expired tokens |
| Auth | Registration, login, logout, token expiry | Invalid credentials, duplicate email |

### 6.2.2 Example Test Cases

**BM25Scorer Edge Cases:**

| Test Case | Expected Result |
|-----------|-----------------|
| Query term not in any document | Score = 0.0 |
| Document with zero length | Score = 0.0 |
| Term with df=0 (term not in index) | IDF = 0.0, contributes nothing |
| Single matching term | Correct BM25 score computed |

**ProximityScorer Edge Cases:**

| Test Case | Expected Result |
|-----------|-----------------|
| Single-token query | `generate_query_pairs` returns `[]`, score = 0.0 |
| Same-term pair ("right", "right") | Self-pair skipped |
| No co-occurrence in document | Pair contributes 0 to average |
| Distance > max_window (30) | Pair discarded |

**Search Engine Edge Cases:**

| Test Case | Expected Result |
|-----------|-----------------|
| Empty query | Caught at controller, never reaches engine |
| Stopword-only query ("the and of") | BM25 processor removes all tokens → empty results |
| Query with no matching documents | Empty results list |

**Authentication:**

| Test Case | Expected Result |
|-----------|-----------------|
| Missing Authorization header | 401 "Token is missing!" |
| Expired JWT | 401 "Token has expired!" |
| Invalid JWT signature | 401 "Invalid token!" |
| Token with stale token_version | 401 "Token has been invalidated. Please log in again." |

**Error Handling:**

| Test Case | Expected Result |
|-----------|-----------------|
| Ollama not running + use_llm=true | HTTP 503 "Ollama service is unavailable." |
| Model not pulled + use_llm=true | HTTP 200 + ollama_status.model_available=false |
| LLM fails after 3 retries | HTTP 200 + error text in response field |
| Database persistence failure | Logged, never breaks response |

## 6.3 Evaluation Metrics

### 6.3.1 Retrieval Quality

The retrieval quality can be evaluated using standard IR metrics:

| Metric | Description |
|--------|-------------|
| Precision@k | Fraction of relevant documents in top-k results |
| Recall@k | Fraction of relevant documents retrieved in top-k |
| Mean Reciprocal Rank (MRR) | Reciprocal rank of first relevant result |
| Normalized Discounted Cumulative Gain (nDCG) | Rank-weighted relevance score |

### 6.3.2 Retrieval Performance

The three-stage reranking pipeline provides measurable improvements:

| Stage | Purpose | Metric Impact |
|-------|---------|---------------|
| RRF Fusion (k=60) | Combine BM25 + proximity + title signals | Smoother ranking than any single signal |
| MMR Diversity (λ=0.5) | Balance relevance and novelty | Prevents near-duplicate results |
| Rule-Based Boost | Structural preference | Promotes full articles over sub-clauses |

### 6.3.3 LLM Quality

RAG quality is assessed on:

| Criterion | Description |
|-----------|-------------|
| Grounding | Does the answer reference only the provided articles? |
| Citation Accuracy | Are cited provisions correctly identified? |
| Completeness | Does the answer address all aspects of the query? |
| Conciseness | Is the answer appropriately brief? |

## 6.4 Test Results Summary

| Test Category | Tests | Status |
|---------------|:-----:|:------:|
| BM25Scorer unit tests | 8 | ✅ All passed |
| ProximityScorer unit tests | 6 | ✅ All passed |
| TextProcessor unit tests | 10 | ✅ All passed |
| SearchEngine integration tests | 5 | ✅ All passed |
| Reranker unit tests | 4 | ✅ All passed |
| Auth endpoint tests | 8 | ✅ All passed |
| API validation tests | 6 | ✅ All passed |
| Error handling tests | 5 | ✅ All passed |

## 6.5 Known Limitations

| Limitation | Impact | Status |
|------------|--------|--------|
| No dedicated retrieval-only endpoint | `/ask?use_llm=false` works but no `/api/v1/search` | Open |
| CORS is permissive | `CORS(app)` with no restrictions | Open |
| Async def with sync mongoengine | Functionally correct but misleading signatures | Open |
