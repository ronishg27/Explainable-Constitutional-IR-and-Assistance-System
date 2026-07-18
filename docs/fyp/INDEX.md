# Constitution Assistant — Final Year Project Report

**Project:** Explainable Constitutional IR and Assistance System
**Authors:** Ronish Ghimire, Devraj Khatiwada, Nayan Nepal
**Domain:** Legal Information Retrieval — Constitution of Nepal (2072 / 2015)

---

## Document Structure

This directory contains the chapters of the Final Year Project report, organized for compilation into a single document.

| # | File | Chapter | Pages (approx) |
|:-:|------|---------|:--------------:|
| 1 | [01_introduction.md](01_introduction.md) | Introduction | 3 |
| 2 | [02_literature_review.md](02_literature_review.md) | Literature Review | 5 |
| 3 | [03_system_analysis.md](03_system_analysis.md) | System Analysis | 3 |
| 4 | [04_system_design.md](04_system_design.md) | System Design & Architecture | 6 |
| 5 | [05_implementation.md](05_implementation.md) | Implementation | 10 |
| 6 | [06_testing.md](06_testing.md) | Testing and Evaluation | 3 |
| 7 | [07_deployment.md](07_deployment.md) | Deployment and User Manual | 4 |
| 8 | [08_conclusion.md](08_conclusion.md) | Conclusion and Future Work | 3 |

## Compilation

To compile into a single PDF, use pandoc:

```bash
pandoc docs/fyp/0*.md -o fyp_report.pdf --toc --number-sections
```

Or to generate a single markdown file:

```bash
type docs\fyp\0*.md > fyp_report.md
```

## Key Technical Details (from source code)

| Aspect | Value |
|--------|-------|
| BM25 k1 | 1.5 |
| BM25 b | 1.0 |
| Proximity weight | 1.0 |
| Title boost | 5.0 per match |
| Max proximity window | 30 tokens |
| RRF k | 60 |
| MMR lambda | 0.5 |
| Recall k (Phase 1) | 30 |
| Top k (final) | 8 |
| LLM model | qwen3:8b |
| LLM retries | 3 (0.5s delay) |
| LLM context window | 4096 |
| Query max length | 500 chars |
| JWT expiry | 12 hours |
| Database | MongoDB 8 (`ECIRAS`) |

## Data Flow Summary

```
User Query → [TextProcessor × 2] → [Synonym Expansion] → [BM25 Scoring]
→ [Proximity Scoring] → [Title Boost] → [Top-30 Candidates] → [RRF Fusion]
→ [MMR Diversity] → [Rule Boost] → [Top-8 Articles] → [Article Promotion]
→ [Context Truncation] → [LLM Prompt] → [Answer + Citations] → [MongoDB Persist]
```
