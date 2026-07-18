# Chapter 8: Conclusion and Future Work

## 8.1 Summary

This project developed a Retrieval-Augmented Generation (RAG) system for the Constitution of Nepal (2072 / 2015). The system combines a custom hybrid search engine — blending BM25 scoring, term proximity analysis, and title boost — with a three-stage algorithmic reranking pipeline (RRF fusion, MMR diversity, rule-based boost) to retrieve and rank constitutional provisions relevant to natural language queries.

The key accomplishments are:

1. **Custom Hybrid Search Engine**: A BM25 scorer (`k1=1.5`, `b=1.0`) combined with an ordered proximity scorer and a title boost mechanism produces ranked results that capture both lexical relevance and phrase-level term proximity.

2. **Synonym Expansion**: 44 legal term synonym groups (e.g., "arrest/detention/custody") are applied at query time to improve recall for legal vocabulary variants.

3. **Three-Stage Reranking**: Reciprocal Rank Fusion (k=60) combines BM25, proximity, and title-match signals; Maximal Marginal Relevance (λ=0.5) ensures result diversity; and rule-based boost prioritizes full articles over sub-clauses.

4. **Article-Level Promotion**: Clause/sub-clause results are automatically merged into full articles with matched-clause tracking and context truncation for efficient LLM prompting.

5. **RAG Integration**: Ollama-hosted LLMs generate citation-anchored answers with strict grounding instructions, 3-attempt retry logic, and a 4096-token context window.

6. **Graceful Degradation**: The system handles three LLM availability states — connected and available (full RAG), connected but model missing (retrieval-only with status), and unreachable (HTTP 503 with clear error).

7. **Full-Stack Web Application**: A React 19 single-page application with JWT authentication, SSE streaming responses, expandable result cards with term highlighting, chat history management, and a responsive design.

8. **MongoDB Persistence**: Every Q&A exchange is saved with full scoring metadata, enabling chat history review and per-user message management.

## 8.2 Limitations

### 8.2.1 Current Limitations

| Limitation | Impact |
|------------|--------|
| **Single model support** | No automatic fallback if `qwen3:8b` is unavailable |
| **No dedicated retrieval endpoint** | `/ask?use_llm=false` works but no `/api/v1/search` |
| **Permissive CORS** | `CORS(app)` with no restrictions |
| **No admin API routes** | `UserService.list_users()` and `delete_user()` exist but no admin blueprint |
| **No rate limiting** | API is unprotected against abuse |

### 8.2.2 Design Trade-offs

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| BM25 `b=1.0` (full length normalization) | Short, dense provisions should not be overshadowed by verbose articles | Longer documents are penalized heavily |
| No neural embeddings for retrieval | Avoids GPU dependency and embedding model maintenance | May miss semantic matches that are lexically distant |
| Rule-based lemmatization for corpus | No spaCy dependency for indexing | Less accurate than spaCy for edge cases |

## 8.3 Future Work

### 8.3.1 Short-Term Improvements

1. **Multi-model LLM Fallback**: Implement automatic fallback chain — if the primary model is unavailable, try alternative models from the Ollama model list.

2. **Dedicated Search Endpoint**: Add `GET /api/v1/search` for retrieval-only queries without the LLM abstraction.

3. **CORS Hardening**: Configure specific allowed origins instead of permissive `CORS(app)`.

4. **Admin Dashboard**: Expose admin API routes for user management with role-based access control.

### 8.3.2 Medium-Term Enhancements

1. **Dense Retrieval Integration**: Add optional neural reranking using sentence transformers or cross-encoders as a fourth reranking stage, configurable at runtime.

2. **Multi-Language Support**: Extend the system to handle Nepali-language queries and the Nepali version of the constitution.

3. **Feedback Loop**: Allow users to mark results as relevant/irrelevant and use this signal for personalized reranking.

4. **Evaluation Dataset**: Curate a set of query-relevant document pairs for the Constitution of Nepal to enable quantitative IR evaluation.

### 8.3.3 Long-Term Vision

1. **Cross-Document Retrieval**: Extend beyond a single constitution to support retrieval across multiple legal documents (acts, regulations, precedents).

2. **Citation Graph**: Build a citation network between constitutional provisions and related legislation.

3. **Fine-Tuned Legal LLM**: Fine-tune a small language model specifically on Nepali legal text for improved answer quality and reduced computational requirements.

## 8.4 Project Repository

The complete source code is available at:

**Repository:** https://github.com/anomalyco/Constitution_assistant

**Authors:** Ronish Ghimire, Devraj Khatiwada, Nayan Nepal

**License:** MIT
