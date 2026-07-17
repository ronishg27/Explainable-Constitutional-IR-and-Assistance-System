# Constitution Assistant — Retrieval Algorithm

## Notation

| Symbol | Meaning |
|--------|---------|
| `recall_k` | Number of candidates recalled in Phase 1 (default **30**) |
| `top_k` | Number of final results (default **8**) |
| `k1` | BM25 term-frequency saturation (default **1.5**) |
| `b` | BM25 length normalization (default **1.0**) |
| `TITLE_BOOST` | Bonus per matching query token in the article title (default **5.0**) |
| `PROXIMITY_WEIGHT` | Factor applied to the proximity score (default **1.0**) |
| `MAX_WINDOW` | Maximum token distance for proximity pairs (default **30**) |
| `rrf_k` | RRF rank-fusion constant (default **60**) |
| `mmr_lambda` | MMR diversity / relevance trade-off (default **0.5**) |

---

## Phase 1 — High-Recall Search (`SearchEngine`)

```
INPUT:  query (string), recall_k (int)
OUTPUT: top recall_k scored documents with metadata

 1. bm25_tokens  ← TextProcessor.process(query, lemmatize=true,  remove_stopwords=true)
 2. base_tokens  ← copy(bm25_tokens)
 3. IF synonym_expander is configured:
 4.     bm25_tokens ← synonym_expander.expand(bm25_tokens, raw_query=query)
 5. raw_tokens    ← TextProcessor.process(query, lemmatize=false, remove_stopwords=false)
 6. query_pairs   ← ProximityScorer.generate_query_pairs(raw_tokens)
 7. candidates    ← {}
 8. FOR token IN bm25_tokens:
 9.     candidates ← candidates ∪ tf_index[token].keys()
10. scored        ← []
11. FOR doc IN documents WHERE doc.doc_id ∈ candidates:
12.     bm25       ← BM25Scorer.score(bm25_tokens, doc.doc_id)
13.     IF bm25 == 0: CONTINUE
 14.     matched    ← BM25Scorer.matched_terms(bm25_tokens, doc.doc_id)
 15.     exact_matched ← BM25Scorer.matched_terms(base_tokens, doc.doc_id)
 16.     title_match_count ← |bm25_tokens ∩ title_tokens[doc.doc_id]|
 17.     title_bonus ← title_match_count × TITLE_BOOST
 18.     prox ← ProximityScorer.score(doc.doc_id, query_pairs,
 19.                                   max_window=MAX_WINDOW, ordered=true)
 20.     final      ← bm25 + title_bonus + PROXIMITY_WEIGHT × prox
 21.     scored.append((final, bm25, prox, title_match_count, doc, matched, exact_matched))
 22. SORT scored BY final DESC
 23. RETURN top recall_k entries with full metadata
```

### BM25 Formula (`bm25_scorer.py`)

$$
\text{score}(D, Q) = \sum_{t \in Q} \text{IDF}(t) \times
\frac{\text{tf}(t, D) \times (k_1 + 1)}
     {\text{tf}(t, D) + k_1 \times \left(1 - b + b \times \dfrac{|D|}{\text{avgdl}}\right)}
$$

$$
\text{IDF}(t) = \log\left(\frac{N - \text{df}(t) + 0.5}{\text{df}(t) + 0.5} + 1\right)
$$

| Parameter | Value | Effect |
|-----------|:-----:|--------|
| `k1` | 1.5 | Moderate TF saturation |
| `b` | 1.0 | Full length normalization — longer docs penalized fully |

### Proximity Pair Heuristic (`proximity.py`)

| Query Length | Strategy | Complexity |
|:------------:|----------|:----------:|
| ≤ 5 tokens | All unordered pairs | O(n²/2) |
| > 5 tokens | Adjacent pairs only | O(n−1) |

- Distance metric: minimum ordered distance (term1 precedes term2)
- Score per pair: quadratic inverse

$$
\text{score}_{\text{pair}}(a, b) = \frac{1}{(d(a, b) + 1)^2}
$$
- Document score: average over all valid pairs
- Pairs ≥ 30 tokens are discarded

### Edge Cases (Phase 1)

- **Empty query**: caught by controller before SearchEngine — never reaches this phase.
- **Query with only stopwords** (e.g. "the and of"): BM25 processor removes all tokens → empty `bm25_tokens` → empty candidate set → empty results.
- **Single-token query**: `generate_query_pairs` returns `[]` → `prox = 0.0`. Final = BM25 + title bonus only.
- **Document with BM25 = 0**: skipped (line 13). The term exists in the index but has zero TF for this specific doc.
- **DF = 0**: `idf` returns 0.0 via explicit guard → contributes nothing to score.

---

## Phase 2 — Reranking (`Reranker`)

```
INPUT:  results (list of dicts from Phase 1), top_k (int)
OUTPUT: top_k results after fusion, diversification, and boost

--- Stage 2a — RRF Fusion ---
 1. rank_bm25   ← sort results by bm25_score DESC   → assign ranks
 2. rank_prox   ← sort results by proximity_score DESC → assign ranks
 3. rank_title  ← sort results by title_match_count DESC → assign ranks
 4. FOR each result:
 5.     rrf ← 1/(rrf_k + rank_bm25) + 1/(rrf_k + rank_prox) + 1/(rrf_k + rank_title)
 6.     result.rrf_score ← rrf
 7. SORT results BY rrf_score DESC

--- Stage 2b — MMR Diversity ---
 8. selected   ← [results[0]]          (pick highest RRF)
 9. candidates ← results[1:]
10. WHILE candidates not empty:
11.     FOR each c ∈ candidates:
12.         vec_c ← BM25_tf_vector(c.doc_id)
13.         max_sim ← max(cosine_similarity(vec_c, vec_s) FOR s ∈ selected)
14.         mmr ← mmr_lambda × c.rrf_score - (1 - mmr_lambda) × max_sim
15.     MOVE candidate with highest mmr TO selected
16. results ← selected

--- Stage 2c — Rule-Based Boost ---
17. FOR each result:
18.     multiplier ← 1.0
19.     multiplier ×= result.boost           (per-document boost from source data)
20.     multiplier ×= part_rules[result.part_no]   (if present in boost_rules)
21.     multiplier ×= level_rules[result.level]    (default: part=1.0, article=0.98, clause=0.95, subclause=0.90)
22.     result.score ← result.score × multiplier
23.     result.boost_multiplier ← multiplier
24. SORT results BY score DESC
25. RETURN top top_k entries
```

### RRF Fusion Details (`reranker.py`)

- Three signals fused: **BM25 rank**, **proximity rank**, **title-match count rank**
- Documents missing a signal get rank = `n` (total count), ensuring they still contribute minimally
- `rrf_k = 60` provides a gentle rank discount

$$
\text{RRF}(d) = \frac{1}{k + \text{rank}_{\text{BM25}}(d)} +
               \frac{1}{k + \text{rank}_{\text{prox}}(d)} +
               \frac{1}{k + \text{rank}_{\text{title}}(d)}
$$

### MMR Details

- Cosine similarity computed on **BM25 term-frequency vectors** (sparse, from `tf_index`)
- `mmr_lambda = 0.5` balances relevance and diversity equally
- First result is always the highest-RRF document; subsequent picks trade score for novelty

$$
\text{MMR}(c) = \lambda \cdot \text{RRF}(c) - (1 - \lambda) \cdot \max_{s \in S} \, \text{sim}(c, s)
$$

### Rule-Based Boost Defaults

| Level | Multiplier |
|-------|:----------:|
| `part` | 1.0 |
| `article` | 0.98 |
| `clause` | 0.95 |
| `subclause` | 0.90 |

These are the **hard-coded defaults** in `reranker.py` and can be overridden via the `boost_rules` parameter.

---

## Article Promotion (`rag_repository.py`)

After Phase 2, clause/sub-clause results are merged into article-level results:

1. **Group** all documents by `article_no`
2. **For articles with an article-level Document** (e.g. articles with lettered sub_clauses): use its text directly
3. **For articles stored only as individual clauses**: concatenate all clause texts with `\n---\n` separators
4. **Deduplicate** by `article_no` — the first occurrence (highest score) determines the result's final score
5. **Track matched clauses** — only matched clause texts are included in the LLM context (via `build_truncated_text`)
