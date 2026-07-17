# Chapter 2: Literature Review

## 2.1 Information Retrieval Foundations

### 2.1.1 The Probabilistic Relevance Framework

The BM25 ranking function, introduced by Robertson and Zaragoza (2009), remains one of the most widely used term-weighting schemes in information retrieval. BM25 computes a relevance score between a query Q and a document D as:

$$
\text{score}(D, Q) = \sum_{t \in Q} \text{IDF}(t) \cdot
\frac{\text{tf}(t, D) \cdot (k_1 + 1)}
     {\text{tf}(t, D) + k_1 \cdot \left(1 - b + b \cdot \dfrac{|D|}{\text{avgdl}}\right)}
$$

Where:
- $tf(t,D)$ is the term frequency of term $t$ in document $D$
- $IDF(t) = \log(\frac{N - df(t) + 0.5}{df(t) + 0.5} + 1)$ is the inverse document frequency
- $k_1$ controls term frequency saturation (default 1.5)
- $b$ controls document length normalization (0 to 1)

Our implementation uses $k_1 = 1.5$ and $b = 1.0$ (full length normalization). The use of $b = 1.0$ is deliberate for legal text: constitutional provisions vary widely in length (from single-sentence rights to multi-clause articles), and full normalization ensures concise provisions are not overshadowed by verbose ones.

### 2.1.2 Term Proximity in Retrieval

Standard BM25 treats a document as a bag of words, ignoring term order. However, in legal texts, phrase structure carries significant meaning — "right to education" and "education right" are not equivalent. Proximity scoring addresses this by measuring how closely query terms appear in a document.

The proximity scoring function used in this system computes:

$$ score_{prox}(doc, Q) = \frac{1}{|P|} \sum_{(t_1,t_2) \in P} \frac{1}{(distance(t_1,t_2) + 1)^2} $$

Where $P$ is the set of query term pairs and distance is measured as the minimum number of tokens between ordered occurrences of $t_1$ and $t_2$. The quadratic inverse ensures that close pairs contribute significantly more than distant ones. A window cap of 30 tokens discards pairs that are too far apart to indicate meaningful phrase structure.

### 2.1.3 Two-Processor Architecture

A key design decision is the use of two separate text processors:

| Processor | Lemmatization | Stopwords | Purpose |
|-----------|:-------------:|:---------:|---------|
| BM25 Processor | ON | REMOVED | Term frequency matching benefits from morphological normalization (e.g., "rights" → "right") |
| Proximity Processor | OFF | KEPT | Phrase-level matching requires original word order; stopwords carry positional information |

This dual-processor approach is supported by IR research showing that lemmatization improves recall for bag-of-words models while degrading proximity signals by merging distinct terms.

## 2.2 Term Proximity Heuristics

For queries longer than 5 tokens, generating all unordered term pairs results in O(n²) complexity with diminishing returns. This system employs an adaptive heuristic:

| Query Length | Pair Strategy | Complexity | Rationale |
|:------------:|---------------|:----------:|-----------|
| ≤ 5 tokens | All unordered pairs | O(n²/2) | Short queries benefit from full cross-term proximity |
| > 5 tokens | Adjacent pairs only | O(n−1) | Distant term pairs in long queries contribute negligible signal |

This approach empirically balances computational cost with retrieval effectiveness for legal queries, which tend to be moderately long (e.g., "What are the fundamental rights guaranteed to citizens?").

## 2.3 Reciprocal Rank Fusion (RRF)

RRF is a method for combining multiple ranking signals without training data. Given $m$ ranked lists, RRF computes a fused score for each document as:

$$ RRF(doc) = \sum_{i=1}^{m} \frac{1}{k + rank_i(doc)} $$

Where $k$ is a constant (default 60) that controls the influence of high ranks versus low ranks. This system fuses three signals:
1. BM25 score rank
2. Proximity score rank
3. Title match count rank

RRF is chosen over linear interpolation because it does not require tuning per-signal weights — each signal contributes through its rank position rather than its raw score magnitude.

## 2.4 Maximal Marginal Relevance (MMR)

MMR balances relevance and diversity in ranked results:

$$ MMR = \lambda \cdot score_{rel}(doc) - (1-\lambda) \cdot \max_{d \in S} sim(doc, d) $$

Where $\lambda = 0.5$ in our implementation, $score_{rel}$ is the candidate's RRF score, and $sim(doc, d)$ is the cosine similarity between BM25 term-frequency vectors. The first document is selected purely by RRF score; subsequent selections trade relevance for novelty. Cosine similarity is computed on sparse TF vectors directly from the term frequency index, avoiding the need for external embeddings.

## 2.5 Retrieval-Augmented Generation (RAG)

RAG (Lewis et al., 2020) addresses a fundamental limitation of LLMs: they cannot reliably cite sources and are prone to hallucination, particularly in factual domains like law. A RAG system retrieves relevant documents from a knowledge base and conditions the LLM's generation on those documents.

The standard RAG pipeline consists of:
1. **Retrieval**: Search a document collection for passages relevant to the query
2. **Augmentation**: Format retrieved passages as context for the LLM
3. **Generation**: Produce an answer grounded in the provided context

Our implementation extends this with:
- **Article promotion**: clause/sub-clause results are merged into full articles with matched-clause tracking
- **Context truncation**: only matched clause texts are included in the LLM prompt for efficiency
- **Strict grounding**: the system prompt explicitly instructs the LLM to answer only from provided articles and to decline if the question is not addressed
- **Retry logic**: 3 attempts with 0.5s delay, 4096 context window

## 2.6 Legal Information Retrieval

Legal IR presents unique challenges compared to general web search:
- **Hierarchical document structure**: Legal texts have nested organization (parts → articles → clauses → sub-clauses) that must be preserved in retrieval
- **Synonymy**: Legal language uses multiple synonymous terms for the same concept (e.g., "arrest", "detention", "custody")
- **Precision requirements**: Answers must include exact citations
- **Domain-specific vocabulary**: Legal terms have precise meanings that differ from everyday usage

Our system addresses these challenges through:
1. **Synonym expansion**: 44 synonym groups (e.g., "arrest/detention/custody", "right/entitlement/prerogative") loaded from `data/synonyms.json` and applied to BM25 tokens at query time
2. **Article-level promotion**: results from clause/sub-clause searches are merged into full article citations
3. **Citation-anchored responses**: the LLM is instructed to cite precisely as `[Part X, Article Y(Z)]`

## 2.7 Related Systems

Several legal IR systems have been documented in the literature:

- **CaseLaw (BR)** — A benchmark for legal information retrieval in Portuguese, focusing on court decisions rather than constitutional text
- **COLIEE** — Annual competition on legal information extraction and entailment, primarily for Japanese and Canadian case law
- **Legal-BERT** — Domain-adapted BERT models for legal text, demonstrating the value of domain-specific language models

This project differs from existing systems in its focus on the Constitution of Nepal specifically, its hybrid BM25 + proximity + RRF/MMR approach (avoiding neural embeddings for retrieval), and its strict RAG grounding for answer generation.

## References

- Robertson, S., & Zaragoza, H. (2009). The Probabilistic Relevance Framework: BM25 and Beyond. *Foundations and Trends in Information Retrieval*, 3(4), 333-389.
- Lewis, P., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *NeurIPS 2020*.
- Carbonell, J., & Goldstein, J. (1998). The Use of MMR, Diversity-Based Reranking for Reordering Documents and Producing Summaries. *SIGIR 1998*.
- Cormack, G. V., et al. (2009). Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods. *SIGIR 2009*.
