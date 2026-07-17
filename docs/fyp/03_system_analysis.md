# Chapter 3: System Analysis

## 3.1 Requirements Analysis

### 3.1.1 Functional Requirements

| ID | Requirement | Priority | Source Component |
|:--:|-------------|:--------:|------------------|
| FR1 | The system shall accept natural language queries in English | High | API Controller |
| FR2 | The system shall retrieve ranked constitutional provisions relevant to the query | High | SearchEngine |
| FR3 | The system shall support optional LLM-based answer generation | Medium | RAGWorkflow |
| FR4 | The system shall provide streaming responses for real-time display | Medium | SSE endpoint |
| FR5 | The system shall persist Q&A history per user | High | MessageService |
| FR6 | The system shall support user registration and authentication | High | Auth Controller |
| FR7 | The system shall allow users to view, search, and delete chat history | Medium | MessageService |
| FR8 | The system shall expand queries with legal synonyms to improve recall | Low | QueryExpander |
| FR9 | The system shall promote clause/sub-clause results to article level | High | RAGRepository |
| FR10 | The system shall rerank results for diversity and relevance | High | Reranker |

### 3.1.2 Non-Functional Requirements

| ID | Requirement | Target | Verification |
|:--:|-------------|:------:|--------------|
| NFR1 | Retrieval-only response time | < 2 seconds | Measured from request to JSON response |
| NFR2 | Graceful LLM degradation | HTTP 503 or retrieval-only fallback | Test with Ollama stopped |
| NFR3 | Query validation | Max 500 characters | Controller validation |
| NFR4 | Authentication expiry | 12-hour JWT lifetime | Token expiration check |
| NFR5 | Pagination | 20 items per page default | Query parameter handling |
| NFR6 | Database connection resilience | 5-second timeout | MongoDB connection config |

## 3.2 Use Case Diagram

The system has two primary actors:

**Authenticated User** — Can submit queries, view results, manage chat history
**System Admin** — Can manage users (future scope; admin API routes not exposed)

### 3.2.1 Use Cases

| UC# | Use Case | Actor | Description |
|:---:|----------|-------|-------------|
| UC1 | Register Account | User | Create account with fullname, email, password |
| UC2 | Login | User | Authenticate and receive JWT |
| UC3 | Logout | User | Invalidate current session |
| UC4 | Submit Query (Retrieval-Only) | User | Ask question without LLM |
| UC5 | Submit Query (RAG) | User | Ask question with LLM-generated answer |
| UC6 | Stream Query Response | User | Receive real-time streaming answer |
| UC7 | View Chat History | User | Browse past Q&A sessions |
| UC8 | View Message Detail | User | See full answer with article cards |
| UC9 | Delete Message | User | Remove single Q&A entry |
| UC10 | Clear All Messages | User | Remove all Q&A history |

## 3.3 Data Flow

### 3.3.1 Online Q&A Flow

```
User → React Frontend → HTTP POST /api/v1/ask (JWT Bearer)
  → Flask API (validate JSON, query length, auth)
  → QAService (orchestration)
  → SearchEngine (recall_k=50 hybrid scoring)
  → Reranker (RRF + MMR + rule boost → top_k=8)
  → RAGRepository (article promotion, context truncation)
  → RAGWorkflow (format prompt, call Ollama with 3× retry)
  → Response (JSON or SSE stream)
  → _persist_message() (save to MongoDB)
```

### 3.3.2 Offline Ingestion Flow

```
Raw Constitution JSON (data/nepal_constitution_new.json)
  → flatten_constitution.py → flattened_nepal_constitution.json
  → IngestionWorkflow:
      → build_tf_index() → tf_index.json
      → build_positional_index() → pos_index.json
      → compute_doc_stats() → doc_stats.json
```

## 3.4 Feasibility Analysis

### 3.4.1 Technical Feasibility

The system uses well-established technologies:
- **Python 3.13 + Flask**: Mature web framework with extensive library support
- **React 19 + Vite 8**: Industry-standard frontend tooling
- **MongoDB 8**: Document database suitable for heterogeneous legal data
- **Ollama**: Local LLM hosting with standard API

### 3.4.2 Operational Feasibility

The system runs entirely on localhost with no external API dependencies:
- MongoDB runs locally on port 27017
- Ollama (optional) runs locally on port 11434
- The Flask server runs on port 5000
- The Vite dev server runs on port 5173

This makes the system self-contained and deployable on a single machine.

### 3.4.3 Data Requirements

The constitution data consists of:
- ~700 flattened documents
- ~5 MB total index files (tf_index, pos_index, doc_stats)
- 44 synonym groups for query expansion
- Rule-based lemma dictionary (~1000 entries)
