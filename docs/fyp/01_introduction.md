# Chapter 1: Introduction

## 1.1 Background

The Constitution of Nepal (2072 / 2015) is the supreme law of Nepal, comprising over 300 articles across 35 parts. It defines the fundamental rights, duties, structure of government, and legal principles governing the country. For citizens, legal professionals, and students, finding relevant constitutional provisions for a specific legal question is a non-trivial task. Manual browsing through the lengthy document is time-consuming, and keyword-based search often fails to capture the semantic relationships between legal concepts.

Information Retrieval (IR) systems have traditionally addressed document search through lexical matching techniques such as BM25. However, legal texts present unique challenges: synonymy (e.g., "arrest" vs. "detention" vs. "custody"), varying levels of specificity (articles, clauses, sub-clauses), and the need for precise citation-backed answers.

Retrieval-Augmented Generation (RAG) has emerged as a promising paradigm that combines the factual grounding of IR with the natural language understanding of Large Language Models (LLMs). By retrieving relevant documents before generating an answer, RAG systems can provide responses that are both contextually appropriate and verifiable against source material.

## 1.2 Problem Statement

Despite the availability of the Constitution of Nepal in digital form, there is no dedicated system that:

1. Provides ranked retrieval of constitutional provisions based on semantic and lexical relevance
2. Generates concise, citation-anchored answers to natural language questions about the constitution
3. Handles the hierarchical nature of legal documents (parts → articles → clauses → sub-clauses)
4. Degrades gracefully when LLM services are unavailable

This project addresses these gaps by building a hybrid IR + RAG system purpose-built for the Constitution of Nepal.

## 1.3 Objectives

The primary objectives of this project are:

1. **Design a hybrid search engine** combining BM25 scoring, term proximity analysis, and title boost for constitution-specific retrieval
2. **Implement a reranking pipeline** using Reciprocal Rank Fusion (RRF), Maximal Marginal Relevance (MMR), and rule-based boost to optimize result quality and diversity
3. **Integrate Retrieval-Augmented Generation** using Ollama-hosted LLMs to produce citation-anchored answers
4. **Provide a web-based user interface** with streaming responses, result expandability, and chat history
5. **Ensure graceful degradation** when LLM services are unavailable, maintaining retrieval-only functionality

## 1.4 Scope

**In scope:**
- Custom BM25 + term proximity + title boost search engine
- Three-stage reranking pipeline (RRF → MMR → rule-based boost)
- Article-level result promotion from clause/sub-clause matches
- Synonym expansion using 44 legal term groups
- RESTful API with authentication (JWT), pagination, and SSE streaming
- React-based single-page application frontend
- MongoDB-backed persistence for users, messages, and referenced articles
- Offline ingestion pipeline for building search indexes

**Out of scope:**
- Multi-language support (English only)
- Full-text search in Nepali or other languages
- Document upload or live constitution editing
- Multi-model LLM fallback chains
- Production-grade CI/CD, containerization, or horizontal scaling

## 1.5 Methodology

The system follows a modular layered architecture:

1. **Offline Ingestion**: Raw constitution JSON is flattened into individual document units (articles, clauses, sub-clauses). Term frequency indexes, positional indexes, and document statistics are pre-computed and stored as JSON artifacts.

2. **Online Retrieval**: User queries are processed through two text processors (one lemmatized without stopwords for BM25, one raw with stopwords for proximity). Candidates are generated from the BM25 index, scored with the hybrid formula, and reranked through three stages.

3. **RAG Generation**: Retrieved articles are promoted to article level, truncated to matched clauses for context efficiency, formatted into a strict grounding prompt, and sent to an Ollama-hosted LLM with retry logic.

4. **Persistence**: Every Q&A exchange is saved to MongoDB, including full scoring metadata for each referenced article.

## 1.6 Organization of the Report

- **Chapter 2**: Literature review of IR techniques, RAG, and legal information retrieval
- **Chapter 3**: System analysis including requirements and use cases
- **Chapter 4**: System design and architecture
- **Chapter 5**: Implementation details of all components
- **Chapter 6**: Testing and evaluation
- **Chapter 7**: Deployment and user manual
- **Chapter 8**: Conclusion and future work
