# Explainable Constitutional IR and Assistance System - Project Documentation

**Project Name:** Explainable Constitutional IR and Assistance System  
**Version:** 1.0.0  
**Created:** 2026  
**Purpose:** A smart search engine for Nepal's Constitution that allows users to ask natural language questions and retrieve relevant constitutional articles with explanations.

---

## 1. PROJECT OVERVIEW

### What the Project Does
This system is a **query-based information retrieval (IR) engine** designed specifically for Nepal's Constitution. It allows users to submit natural language questions (e.g., "What are my freedom rights?") and returns:
- Relevant constitutional articles, clauses, and subclauses
- Ranked results based on relevance
- Proper citations and explanations

### Problem It Solves
- **Accessibility:** Makes constitutional knowledge easily accessible to citizens
- **Search Efficiency:** Provides fast, relevant results instead of manual document browsing
- **Clarity:** Helps users find specific constitutional provisions without legal expertise
- **Explanation:** Returns exactly which article/clause matches the query

### Key Features
1. **Natural Language Query Processing** - Users can ask questions in plain English
2. **Multi-Algorithm Search** - Implements BM25, Boolean Search, and TF-IDF scoring
3. **Title Boosting** - Prioritizes results where query terms appear in article titles
4. **Lemmatization & Preprocessing** - Normalizes text for better matching (e.g., "rights" → "right")
5. **Efficient Indexing** - Pre-built indices for fast lookups
6. **REST API** - Clean HTTP interface for integration with frontends

### Technologies Used
- **Backend Framework:** Flask (Python)
- **Search Algorithms:** BM25, Boolean Search, TF-IDF
- **NLP Processing:** Custom tokenization, lemmatization, stopword removal
- **Data Format:** JSON
- **API Format:** REST with JSON payloads

---

## 2. SYSTEM ARCHITECTURE

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT / FRONTEND                        │
│                    (Postman / Web UI)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓ (HTTP POST)
┌──────────────────────────────────────────────────────────────┐
│                   FLASK REST API                              │
│              (app.py: /api/v1/ask endpoint)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ↓             ↓             ↓
    ┌─────────────────────────────────────┐
    │   QUERY PROCESSING & NLP LAYER      │
    │  - Tokenization (text_processing)   │
    │  - Lemmatization (src/core/nlp.py)  │
    │  - Stopword Removal                 │
    └─────────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ↓             ↓             ↓
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │   BM25   │  │ Boolean  │  │  TF-IDF  │
    │  Search  │  │  Search  │  │  Search  │
    │(bm25.py)│  │(bool...  │  │(ii_tf.py)│
    └────┬─────┘  └────┬─────┘  └────┬─────┘
         │             │             │
         └─────────────┼─────────────┘
                       ↓
    ┌──────────────────────────────────────────┐
    │       DATA & INDEXING LAYER              │
    │  - Constitutional Data (JSON)            │
    │  - Inverted Index (inverted_index.json)  │
    │  - BM25 Index (bm25_index.json)          │
    │  - Lemma Dictionary (lemma_dict_v3.json) │
    └──────────────────────────────────────────┘
                       │
                       ↓
    ┌──────────────────────────────────────────┐
    │    DATA STORAGE (/backend/data/)         │
    │  - constitution_combined.json            │
    │  - flattened_constitution.json           │
    │  - Various processed indices             │
    └──────────────────────────────────────────┘
                       ↓ (JSON Response)
    ┌──────────────────────────────────────────┐
    │          API RESPONSE                    │
    │  - Query (echoed back)                   │
    │  - Response (explanation)                │
    │  - Articles (matching results)           │
    └──────────────────────────────────────────┘
```

### Data Flow: Query → Response

```
User Query: "What are my freedom rights?"
        ↓
[1] RECEIVE & EXTRACT
    - Parse JSON request
    - Extract query string
        ↓
[2] PREPROCESS
    - Normalize: lowercase, remove punctuation
    - Tokenize: split into words
    - Remove stopwords: filter common words
    - Lemmatize: convert to base forms
    Result: [freedom, right]
        ↓
[3] SEARCH (Multiple Algorithms)
    ┌─→ BM25 Search
    │   - Calculate term frequency (TF) and inverse document frequency (IDF)
    │   - Score each matching document
    │   - Boost score if terms appear in title
    │
    ├─→ Boolean Search
    │   - Find documents containing ALL query terms
    │   - Apply TF-IDF scoring
    │
    └─→ TF-IDF Search
        - Create inverted index
        - Calculate TF-IDF scores
        - Retrieve top-K matching documents
        ↓
[4] RANK & FILTER
    - Combine scores from different algorithms
    - Keep top-K results (e.g., top 5)
    - Attach relevance scores
        ↓
[5] FORMAT RESPONSE
    - Extract article metadata (citation, title, text)
    - Include relevance scores & document IDs
    - Return JSON response
        ↓
[6] SEND TO CLIENT
    - Return HTTP 200 with results
    - Client displays articles with explanations
```

### How Different Parts Interact

| Component | Role | Connected To |
|-----------|------|--------------|
| **app.py** | Entry point, routes requests | text_processing, bm25, boolean_search, ii_tf |
| **text_processing.py** | Text normalization & tokenization | All search modules |
| **src/core/nlp.py** | Advanced NLP with lemmatization | Can be used by app.py |
| **bm25.py** | BM25-based relevance ranking | Ranking engine |
| **boolean_search.py** | AND-based boolean search | Alternative ranking |
| **ii_tf.py** | Inverted index + TF-IDF scoring | Alternative ranking |
| **Data files** | Preprocessed constitutional text | All search modules |

---

## 3. FOLDER & FILE STRUCTURE

### Directory Tree

```
backend/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── text_processing.py              # Text tokenization & normalization
├── bm25.py                         # BM25 search implementation
├── boolean_search.py               # Boolean AND search
├── ii_tf.py                        # Inverted index + TF-IDF search
│
├── src/                            # Source code modules
│   ├── constants/
│   │   ├── __init__.py
│   │   └── stopwords.py           # Curated list of stopwords for constitutional text
│   └── core/
│       └── nlp.py                  # NLP preprocessing with lemmatization
│
├── preprocessing_scripts/          # Data preparation utilities
│   ├── flatten_articles.py         # Convert nested JSON → flat document list
│   ├── filter_lemma_dict.py        # Filter lemma dict to constitution vocab
│   └── generate_safe_lemma_dict.py # Generate lemmatization rules
│
└── data/                           # All processed data & indices
    ├── Constitution-of-Nepal_2072.pdf
    ├── constitution_combined.json      # Original constitutional data (nested structure)
    ├── flattened_constitution.json    # Flat document list (main searchable corpus)
    ├── flattened_articles.json        # Similar to above
    ├── inverted_index.json            # Token → Document mapping
    ├── bm25_index.json                # Pre-computed BM25 index
    ├── lemma_dict_v1.json             # Early version of lemmatization dictionary
    ├── lemma_dict_v2.json             # Filtered version
    ├── lemma_dict_v3.json             # Final version (used by nlp.py)
    ├── nepal_constitution_mvp.json    # MVP version
    └── part3_combined.json            # Specific part of constitution
```

### File Purpose Mapping

| File | Purpose | Key Responsibility |
|------|---------|-------------------|
| `app.py` | REST API server | Handles HTTP requests, routes to search functions |
| `text_processing.py` | Basic text normalization | Tokenizes & removes stopwords (simple version) |
| `src/core/nlp.py` | Advanced NLP | Tokenization + lemmatization using lemma_dict_v3 |
| `bm25.py` | BM25 ranking | Implements BM25 algorithm with title boosting |
| `boolean_search.py` | AND-based search | Returns docs matching ALL query terms |
| `ii_tf.py` | Inverted index search | Uses TF-IDF with pre-built indices |
| `stopwords.py` | Word filtering | Lists 150+ common words to ignore |
| `flatten_articles.py` | Data preprocessing | Converts nested JSON to flat searchable documents |
| `filter_lemma_dict.py` | Lemmatization preprocessing | Filters lemma dict to constitution vocabulary |
| `generate_safe_lemma_dict.py` | Lemmatization rules | Generates lemmatization logic (suffix rules) |

---

## 4. CORE WORKFLOW (STEP-BY-STEP)

### Complete Query Processing Flow

#### **STEP 1: User Submits Query**
```
HTTP POST /api/v1/ask
Content-Type: application/json

{
  "query": "What are my freedom rights?"
}
```

#### **STEP 2: Flask Receives and Parses Request**
**Location:** `app.py` → `ask()` endpoint (lines 23-31)
```python
query = request.json.get("query")  # Extract query string
```
- Receives JSON payload
- Extracts the "query" field
- Validates input (currently minimal validation)

#### **STEP 3: Text Preprocessing**

**Phase 3A: Normalization**  
**Location:** `text_processing.py` → `tokenize()` (lines 7-14)
```
Input:  "What are my freedom rights?"
↓
Convert to lowercase:
        "what are my freedom rights?"
↓
Remove punctuation;
        "what are my freedom rights"
↓
Split on whitespace:
        ["what", "are", "my", "freedom", "rights"]
```

**Phase 3B: Stopword Removal**  
**Location:** `text_processing.py` or `src/core/nlp.py`
```
Input:  ["what", "are", "my", "freedom", "rights"]
↓
Filter using STOPWORDS set:
        ["freedom", "rights"]  ← These are content words
```
Note: `STOPWORDS` in `src/constants/stopwords.py` contains ~150 words like "the", "and", "are", "may", "shall", etc. that are filtered out.

**Phase 3C: Lemmatization** (Optional, via NLP)  
**Location:** `src/core/nlp.py` → `preprocess()` (lines 19-26)
```
Input:  ["freedom", "rights"]
↓
Apply lemma_dict_v3:
        "freedom" → "freedom" (already lemma)
        "rights" → "right" (plurals → singular)
↓
Output: ["freedom", "right"]
```

**Result:** Processed query tokens: `["freedom", "right"]`

#### **STEP 4: Search Algorithm Selection & Execution**

The system can use three different search methods (implementation currently shows placeholder):

##### **Option A: BM25 Search**
**Location:** `bm25.py` → `search_bm25_with_boost()`

1. **Build Inverted Index** (first time only)
   - For each document: tokenize text
   - For each token: map to document IDs
   ```
   "freedom" → {doc_1: 3, doc_5: 1, doc_22: 2}  (doc_id: frequency)
   "right" → {doc_1: 2, doc_15: 4, doc_22: 1}
   ```

2. **Calculate TF-IDF Scores**
   - For each query term in each document:
   - TF (Term Frequency): How often term appears in doc
   - IDF (Inverse Document Frequency): log(Total_Docs / Docs_with_term)
   - BM25 Formula:
     ```
     score = Σ IDF(t) × (freq(t) × (k1 + 1)) / (freq(t) + k1 × (1 - b + b × (doc_len / avg_doc_len)))
     ```
   where k1=1.5, b=0.75 (parameters for tuning)

3. **Apply Title Boost**
   - If query terms appear in document title: +5.0 per term
   - Makes documents with matching titles rank higher

4. **Rank and Return Top-K**
   - Sort by score descending
   - Return top 5 results (configurable)

**Example calculation:**
```
Query: ["freedom", "right"]
Document 1 (Article_1.2): "Freedom of movement"
  - Contains both "freedom" (3x) and derived terms
  - TF-IDF scores calculated
  - If title is "Freedom of Movement": +5 boost
  Final score: 12.3

Document 15 (Article_21): "Rights of minorities"
  - Contains "right" (4x)
  - Title boost: +5
  Final score: 8.7

Result: Document 1 ranked higher
```

##### **Option B: Boolean AND Search** (Strict Matching)
**Location:** `boolean_search.py` → `boolean_search()`

1. **Intersection-Based Matching**
   ```
   Query: ["freedom", "right"]
   
   Docs with "freedom": {1, 5, 22, 33}
   Docs with "right":   {1, 15, 22, 45}
   
   AND result: {1, 22}  ← Only these have BOTH terms
   ```

2. **Fallback to TF-IDF Scoring**
   - Rank the matching documents by TF-IDF
   - Each term contributes: TF × log(Total_Docs / Docs_with_term)

**Use case:** When you need documents mentioning all query concepts

##### **Option C: TF-IDF Only**
**Location:** `ii_tf.py` → `score_documents()`

1. **Simpler than BM25** (no document length normalization)
2. **Score Calculation:**
   ```
   score[doc] = Σ (TF[term, doc] × IDF[term])
   ```
3. **Useful for:** Baseline comparisons, lighter computations

---

#### **STEP 5: Rank & Filter Results**

Combined ranking process:
```
For each matched document:
  ├─ Base score from search algorithm
  ├─ Title boost (if title contains query terms)
  ├─ Relevance confidence (score normalized)
  └─ document metadata (citation, article number, etc.)

Sort by final score descending
Keep top-K (e.g., K=5)
```

---

#### **STEP 6: Format Response**

**Location:** `app.py` → `ask()` function (lines 28-31)

Each result includes:
```json
{
  "doc_id": "1.2.a",           // Document identifier (Article.Clause.Subclause)
  "article_no": 1,             // Article number
  "title": "Freedom of Movement", // Article title
  "text": "Full text of article...", // Actual constitutional text
  "citation": "Part 1, Article 1(2)(a)", // Proper legal citation
  "title_tokens": ["fundamental"],  // Tokenized title (for scoring)
  "body_tokens": ["freedom", "movement"], // Tokenized body
  "score": 12.34               // Relevance score
}
```

---

#### **STEP 7: Return API Response**

**Current Response Format:**
```json
{
  "query": "What are my freedom rights?",
  "response": "Response placeholder.",
  "articles": [
    {
      "doc_id": "1.2",
      "title": "Freedom of Movement",
      "citation": "Part 1, Article 1(2)",
      "text": "Every person shall have the right to move freely...",
      "score": 12.34
    },
    ... (more results)
  ]
}
```

**Status Code:** HTTP 200 OK

---

### Summary Table: Processing Pipeline

| Stage | Input | Process | Output | Location |
|-------|-------|---------|--------|----------|
| 1. Receive | Raw query | Parse JSON | Query string | app.py |
| 2. Normalize | Query string | Lowercase, remove punctuation | Clean text | text_processing.py |
| 3. Tokenize | Text | Split on whitespace | Token list | text_processing.py |
| 4. Filter | Tokens | Remove stopwords | Content tokens | stopwords.py |
| 5. Lemmatize | Tokens | Map to base forms | Normalized tokens | nlp.py |
| 6. Search | Tokens | Calculate scores | Scored results | bm25.py, boolean_search.py, ii_tf.py |
| 7. Rank | Scores | Sort & filter top-K | Ranked results | Search modules |
| 8. Format | Results | Add metadata | JSON docs | app.py |
| 9. Return | JSON | HTTP response | Client display | app.py |

---

## 5. KEY COMPONENTS & LOGIC

### Component 1: Text Processing Module
**File:** `text_processing.py`

**Purpose:** Converts raw user queries into processable tokens

**Key Function:** `tokenize(text)`
```python
def tokenize(text):
    """
    Normalize and tokenize text
    1. Convert to lowercase
    2. Remove non-alphanumeric characters (keep whitespace)
    3. Split into tokens
    4. Filter out stopwords
    """
    normalized = text.lower()
    normalized = re.sub(r'[^\w\s]', ' ', normalized)  # Remove punctuation
    tokens = normalized.split()
    return [t for t in tokens if t not in STOPWORDS]
```

**Connections:**
- Used by all search modules (`bm25.py`, `boolean_search.py`, `ii_tf.py`)
- Used during data flattening (`flatten_articles.py`)

---

### Component 2: NLP Core Module
**File:** `src/core/nlp.py`

**Purpose:** Advanced text preprocessing with lemmatization

**Key Function:** `preprocess(text)`
```python
def preprocess(self, text):
    """
    Complete preprocessing pipeline:
    1. normalize() - lowercase, remove punctuation
    2. tokenize() - split into words
    3. remove_stopwords() - filter common words
    4. lemmatize() - convert to base forms
    """
    normalized = self.normalize(text)
    tokens = self.tokenize(normalized)
    filtered = self.remove_stopwords(tokens)
    lemmatized = self.lemmatize(filtered)
    return lemmatized
```

**Lemmatization Logic:**
- Loads `lemma_dict_v3.json` (custom dictionary)
- Maps word forms to base forms:
  ```
  "rights" → "right"
  "freedoms" → "freedom"
  "applying" → "apply"
  ```

**Why Lemmatization?**
- Makes search more flexible (search "right" finds "rights", "rightly", etc.)
- Reduces vocabulary size
- Improves matching accuracy

**Connections:**
- Can be used in `app.py` for better query preprocessing
- Uses `lemma_dict_v3.json` from data folder

---

### Component 3: BM25 Search Module
**File:** `bm25.py`

**Purpose:** State-of-the-art relevance ranking algorithm

**Algorithm:** BM25 (Best Match 25)
- Standard information retrieval algorithm
- Proven effective for text search
- Parameters: k1=1.5 (term frequency saturation), b=0.75 (length normalization)

**Key Classes/Functions:**

1. **BM25 Class Constructor**
   ```python
   def __init__(self, documents, k1=1.5, b=0.75):
       self.avgdl = average document length
       self.index = inverted index built once
       self.doc_lengths = {doc_id: length}
   ```

2. **Inverted Index Building** `_build_index()`
   ```
   Converts: [doc1, doc2, ...]
   Into:     {term1: {doc1: freq, doc3: freq}, 
              term2: {doc1: freq, doc2: freq}}
   ```

3. **IDF Calculation** `idf(term)`
   ```python
   idf = log((N - df + 0.5) / (df + 0.5) + 1)
   where N = total docs, df = docs containing term
   ```
   - Rarer terms have higher IDF
   - Common terms have lower IDF

4. **Document Scoring** `score(query_tokens, doc_id)`
   ```python
   score = Σ idf(term) × (tf × (k1+1)) / (tf + k1 × (1-b + b×(doc_len/avgdl)))
   ```
   - Accumulates scores for all query terms
   - Normalizes by document length

5. **Title Boosting** `score_with_boost()`
   ```python
   # Count matching terms in title
   title_match = |query_tokens ∩ title_tokens|
   boost_score = base_score + (title_match × 5.0)
   ```
   - Documents with matching titles ranked higher
   - Weight: 5.0 per matching term

**Connections:**
- Uses `text_processing.tokenize()` for query tokenization
- Called from `app.py` to rank results
- Can accept pre-tokenized documents

---

### Component 4: Boolean Search Module
**File:** `boolean_search.py`

**Purpose:** Precise AND-based search (finds docs with ALL query terms)

**Key Functions:**

1. **Inverted Index Building** `build_inverted_index()`
   ```
   Similar to BM25, creates token → document mapping
   ```

2. **Boolean Search** `boolean_search(query, index, docs)`
   ```python
   # Start with docs containing first term
   result_set = index[query_tokens[0]].keys()
   
   # Intersect with docs containing each subsequent term
   for token in query_tokens[1:]:
       result_set = result_set ∩ index[token].keys()
   ```
   - Strict AND logic
   - Early termination if any term not found
   - Returns empty if not all terms present

3. **Scoring** `score_documents()`
   ```python
   score[doc] = Σ (tf[term, doc] × log(total_docs / docs_with_term))
   ```
   - TF-IDF ranking of matched documents

**Use Case:** When you want documents mentioning all query concepts

**Example:**
```
Query: ["freedom", "right"]
doc_1: mentions both → INCLUDED, score 10.5
doc_2: mentions only "freedom" → EXCLUDED
doc_3: mentions both → INCLUDED, score 8.2
Result: [doc_1, doc_3] sorted by score
```

**Connections:**
- Uses `text_processing.tokenize()` for query processing
- Alternative to BM25 for stricter matching
- Same inverted index structure used by other modules

---

### Component 5: Inverted Index + TF-IDF Module
**File:** `ii_tf.py`

**Purpose:** Duplicate of BM25/Boolean implementations with simplified TF-IDF

**Contains:**
- Own `BM25` class (similar to `bm25.py`)
- Own tokenization logic with embedded stopwords
- `build_inverted_index()` function
- `boolean_search()` and `score_documents()` functions
- Duplicate `search_bm25()` and `search_bm25_with_boost()` functions

**Note:** This file appears to be a development/testing version with redundant code. In production, should consolidate with `bm25.py`.

**Unique Features:**
- Extended stopword list (200+ words, including constitutional terminology)
- Same algorithms, different implementation

**Connections:**
- Can be used as alternative to `bm25.py`
- Self-contained with its own tokenization

---

### Component 6: Stopwords Management
**File:** `src/constants/stopwords.py`

**Purpose:** Defines words to ignore during search

**Content:** Set of ~150 constitutional stopwords:
```
{'the', 'and', 'of', 'to', 'in', 'is', 'be', 'may', 'shall', 
 'article', 'clause', 'section', 'provision', 'law', 'constitution', 
 'parliament', 'government', 'authority', ...}
```

**Why These Words?**
- Too common in constitutional text to be discriminative
- High frequency but low semantic value
- Removing them improves signal-to-noise ratio

**Customization:**
- Curated specifically for constitutional domain
- Different from general English stopwords
- Includes legal/structural terms (e.g., "article", "clause", "provision")

**Connections:**
- Used by `text_processing.tokenize()`
- Used by `src/core/nlp.py`
- Imported in both search modules

---

### Component 7: Data Preprocessing Scripts

#### **Script 1: flatten_articles.py**
**Purpose:** Convert nested JSON structure → flat document list

**Input Structure:**
```json
{
  "article_number": 1,
  "title": "Constitution as the fundamental law",
  "content": [
    {"clause_number": 1, "text": "This Constitution is..."},
    {"clause_number": 2, "text": "It shall be the duty..."}
  ]
}
```

**Output Structure:**
```json
{
  "doc_id": "1.1",
  "article_no": 1,
  "title": "Constitution as the fundamental law",
  "text": "This Constitution is...",
  "citation": "Part 1, Article 1(1)",
  "title_tokens": ["fundamental"],
  "body_tokens": ["fundamental", "law", ...]
}
```

**Process:**
1. Iterate through articles
2. For each article, iterate through clauses
3. For each clause, iterate through subclauses (if any)
4. Create flat document for each clause/subclause
5. Pre-tokenize title and body for efficiency

**Tokenization Feature:**
- Pre-tokenizes title and body → stored in document
- Saves CPU time during search (tokens pre-computed)
- Used by `score_with_boost()` for title matching

---

#### **Script 2: filter_lemma_dict.py**
**Purpose:** Reduce lemma dictionary size to constitution vocabulary

**Process:**
1. Extract text from Constitution PDF
2. Build vocabulary of unique words
3. Filter lemma_dict to only words in constitution
4. Save filtered version

**Why?**
- Original lemma dict is large (thousands of words)
- Many words irrelevant to constitution
- Faster lookup, smaller file size
- Improves relevance (only constitutional vocab)

**Output:** `lemma_dict_v2.json` (smaller than v1)

---

#### **Script 3: generate_safe_lemma_dict.py**
**Purpose:** Auto-generate lemmatization rules using suffix-based approach

**Rules Implemented:**
```python
- "ies" → "y" (studies → study)
- "es" → "" (boxes → box)
- "s" → "" (dogs → dog)
- "ing" → "" (running → run)
- "ed" → "" (jumped → jump)
- "er" → "" (runner → run)
- "est" → "" (fastest → fast)
+ Irregular mappings (went → go, etc.)
```

**Logic:**
- For each word, try applying rules
- Check if result exists in vocabulary
- If yes, that's the lemma; if no, try other rules

**Output:** `lemma_dict_v3.json` (final, used by `nlp.py`)

---

### Component 8: Flask REST API
**File:** `app.py`

**Purpose:** HTTP interface for external clients

**Endpoints:**

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1` | GET | API documentation | ✅ Implemented |
| `/api/v1/health` | GET | Health check | ✅ Implemented |
| `/api/v1/ask` | POST | Submit query, get results | 🔶 Skeleton only |

**Current Implementation:**
```python
@app.route("/api/v1/ask", methods=["POST"])
def ask():
    query = request.json.get("query")
    # TODO: Add actual search logic here
    
    return jsonify({
        "query": query,
        "response": "Response placeholder.",
        "articles": "Articles placeholder."
    })
```

**What's Missing:**
- Actual search logic (BM25, Boolean, or TF-IDF)
- Document loading
- Index building/loading
- Result formatting

**How to Complete:**
```python
def ask():
    query = request.json.get("query")
    
    # 1. Load documents
    with open("data/flattened_constitution.json") as f:
        documents = json.load(f)
    
    # 2. Initialize search
    bm25_instance = BM25(documents)
    
    # 3. Process query
    from text_processing import tokenize
    query_tokens = tokenize(query)
    
    # 4. Search
    results = search_bm25_with_boost(query, bm25_instance, documents, top_k=5)
    
    # 5. Format and return
    return jsonify({
        "query": query,
        "response": f"Found {len(results)} relevant articles",
        "articles": results
    })
```

**Connections:**
- Imports: `text_processing`, `bm25`, `boolean_search`, `ii_tf`, `nlp`
- Uses data from: `data/flattened_constitution.json`
- Returns JSON-formatted results

---

## 6. DATA HANDLING

### Data Storage Strategy

**Location:** `/backend/data/` directory

**Primary Data Sources:**

1. **Original Constitution PDF**
   - File: `Constitution-of-Nepal_2072.pdf`
   - Source: Official government document
   - Format: PDF (binary)
   - Purpose: Original source material

2. **Raw Constitution JSON**
   - File: `constitution_combined.json`
   - Format: Nested JSON structure
   - Parts: Multiple parts of Nepal's Constitution
   - Structure:
     ```json
     [
       {
         "article_number": 1,
         "part_number": 1,
         "title": "Constitution as the fundamental law",
         "content": [
           {"clause_number": 1, "text": "..."},
           {"clause_number": 2, "text": "..."}
         ]
       },
       ...
     ]
     ```

3. **Flattened Documents (PRIMARY CORPUS)**
   - Files: `flattened_constitution.json`, `flattened_articles.json`
   - Format: Flat JSON array of searchable documents
   - Total documents: ~550+ articles/clauses
   - Each document contains:
     ```json
     {
       "doc_id": "1.2",
       "article_no": 1,
       "title": "Constitution as the fundamental law",
       "text": "Full article text...",
       "citation": "Part 1, Article 1(2)",
       "title_tokens": ["token1", "token2"],
       "body_tokens": ["token1", "token2", ...]
     }
     ```

---

### Preprocessing Pipeline

```
PDF Document
    ↓
[Manual Extraction]
    ↓
Nested JSON (constitution_combined.json)
    ↓
[flatten_articles.py]
    ↓
Flattened Documents (flattened_constitution.json)
    ├─ Tokenization (pre-computed)
    ├─ Citation formatting
    └─ Searchable structure
    ↓
[bm25.py, boolean_search.py, ii_tf.py]
    ↓
Indices & Cached Results
    ├─ inverted_index.json
    └─ bm25_index.json
```

---

### Indexing Strategy

#### **Inverted Index**
- **File:** `inverted_index.json`
- **Structure:**
  ```json
  {
    "freedom": {
      "1.1": 2,
      "1.2": 1,
      "21.3": 3
    },
    "right": {
      "1.1": 4,
      "21.1": 2,
      "22.5": 1
    }
  }
  ```
- **Format:** `token → {doc_id: frequency}`
- **Purpose:** Fast document lookup by token
- **Build Time:** ~1-2 seconds (one-time, at startup)
- **Query Time:** O(k) where k = number of query terms

#### **BM25 Index**
- **File:** `bm25_index.json`
- **Contains:** Pre-computed IDF values
- **Purpose:** Accelerate BM25 calculations
- **Optimization:** Avoid recalculating IDF for every query

---

### Data Types & Schemas

#### **Document Schema**
```json
{
  "doc_id": "string",           // Unique identifier (article.clause.subclause)
  "article_no": "integer",      // Article number
  "title": "string",            // Article title
  "text": "string",             // Full text (searchable)
  "citation": "string",         // Legal citation format
  "title_tokens": ["array"],    // Pre-tokenized title
  "body_tokens": ["array"],     // Pre-tokenized body
  "score": "float" (optional)   // Added during search results
}
```

#### **Search Result Schema**
```json
{
  "query": "string",                    // Original query
  "response": "string",                 // Summary response
  "articles": [
    {
      ... (document schema above)
    }
  ]
}
```

---

### Lemmatization Data

#### **Lemma Dictionary (v3 - Final)**
- **File:** `lemma_dict_v3.json`
- **Format:** `word → lemma` mapping
- **Example:**
  ```json
  {
    "rights": "right",
    "freedoms": "freedom",
    "establishing": "establish",
    "applied": "apply",
    "citizen": "citizen"
  }
  ```
- **Size:** ~2000-3000 entries (constitutional vocabulary)
- **Generated by:** `generate_safe_lemma_dict.py`
- **Usage:** `src/core/nlp.py` → `lemmatize()` function

#### **Stopwords Set**
- **File:** `src/constants/stopwords.py`
- **Format:** Python set of strings
- **Size:** ~150 words
- **Examples:** "the", "and", "shall", "may", "article", "of", etc.
- **Domain:** Constitutional English (not general English)

---

### Data Flow: From PDF to Search

```
Constitution-of-Nepal_2072.pdf
         ↓
[Manual extraction + formatting]
         ↓
constitution_combined.json (nested structure)
         ↓
[flatten_articles.py]           // Run once during setup
    └─ Extract clauses & subclauses
    └─ Tokenize text
    └─ Format citations
         ↓
flattened_constitution.json (main corpus)
         ↓
At runtime:
    ├─ Load documents
    ├─ Build inverted index (BM25 class constructor)
    ├─ Build IDF cache
    └─ Ready for queries
         ↓
User Query
    ↓
[Search algorithm processes]
    ↓
Top-K results
    ↓
[Format as JSON]
    ↓
Send to client
```

---

## 7. MODELS / ALGORITHMS USED

### Search Algorithms

#### **Algorithm 1: BM25 (Best Match 25)**
- **Category:** Probabilistic relevance model
- **Year Introduced:** 1994
- **Status:** Industry standard (Google initially used it)

**How It Works:**
1. Calculates TF (Term Frequency) - how often term appears in document
2. Calculates IDF (Inverse Document Frequency) - rarity of term in corpus
3. Normalizes by document length (longer docs don't automatically score higher)
4. Combines into ranking score

**Formula:**
```
score(D, Q) = Σ IDF(qi) × (f(qi,D) × (k1+1)) / (f(qi,D) + k1×(1-b+b×(|D|/avgdl)))

where:
- D = document
- Q = query
- qi = query term i
- f(qi,D) = frequency of qi in D
- |D| = document length
- avgdl = average document length
- k1 = 1.5 (controls term frequency saturation)
- b = 0.75 (controls length normalization)
```

**Advantages:**
- ✅ Proven effective for text search
- ✅ Handles document length variation well
- ✅ Natural relevance ranking
- ✅ Computationally efficient

**Disadvantages:**
- ❌ No semantic understanding
- ❌ No query analysis (OR, AND, NOT operators)
- ❌ No concept matching across synonyms

**When to Use:**
- Main search algorithm
- General queries across constitutional text
- When you want natural ranking

**Implementation in Code:** `bm25.py`

---

#### **Algorithm 2: Boolean AND Search**
- **Category:** Set-based retrieval
- **Complexity:** Simpler than BM25

**How It Works:**
1. Find documents containing first query term
2. Intersect with documents containing second term
3. Intersect with documents containing third term (etc.)
4. Return documents matching ALL terms

**Formula:**
```
result = docs(term1) ∩ docs(term2) ∩ docs(term3) ∩ ...
```

**Example:**
```
Query: "freedom right"
docs("freedom") = {1, 5, 22, 100}
docs("right")   = {1, 22, 50, 200}

result = {1, 22}  ← Both terms present
```

**Advantages:**
- ✅ Precise (all terms must match)
- ✅ Very fast (early termination possible)
- ✅ No ranking parameters to tune

**Disadvantages:**
- ❌ Too strict (no partial matches)
- ❌ Relevance not distinguished
- ❌ Can return zero results easily

**When to Use:**
- Advanced power users
- Multi-concept queries
- When you need ALL concepts to be mentioned

**Implementation in Code:** `boolean_search.py`

---

#### **Algorithm 3: TF-IDF Scoring**
- **Category:** Vector space model
- **Simplicity:** Simpler than BM25 (no length normalization)

**How It Works:**
1. For each query term, calculate:
   - TF (Term Frequency): count occurrences in document
   - IDF (Inverse Document Frequency): log(total_docs / docs_with_term)
2. Sum up TF × IDF for all terms

**Formula:**
```
score(D, Q) = Σ (tf(qi, D) × idf(qi))

where:
- tf(qi, D) = raw frequency of term qi in document D
- idf(qi) = log(N / df(qi))
- N = total number of documents
- df(qi) = number of documents containing qi
```

**Comparison with BM25:**
```
BM25:   More sophisticated, includes length normalization
TF-IDF: Simpler, but ignores document length variation
```

**Advantages:**
- ✅ Simpler than BM25 (fewer parameters)
- ✅ Still effective for many tasks
- ✅ Easy to understand and explain

**Disadvantages:**
- ❌ Doesn't normalize by document length
- ❌ Longer documents may have unfair advantage
- ❌ Less proven than BM25

**When to Use:**
- Baseline comparisons
- Educational purposes
- When computational efficiency is critical

**Implementation in Code:** `ii_tf.py` → `score_documents()`

---

### Supporting Techniques

#### **Technique 1: Tokenization**

**Purpose:** Split text into processable units (words/tokens)

**Process:**
```
Input:  "What are my freedom rights?"
        ↓
Lowercase: "what are my freedom rights?"
        ↓
Remove punctuation: "what are my freedom rights"
        ↓
Split on whitespace: ["what", "are", "my", "freedom", "rights"]
        ↓
Output: Token list
```

**Why?**
- Enables individual word matching
- Allows flexible comparisons
- Foundation for all text algorithms

---

#### **Technique 2: Stopword Removal**

**Purpose:** Filter out low-information words

**Process:**
```
Input:  ["what", "are", "my", "freedom", "rights"]
        ↓
Filter against STOPWORDS: {'the', 'and', 'are', 'my', ...}
        ↓
Output: ["freedom", "rights"]
```

**Why?**
- Very common words add noise
- Reduces index size
- Improves matching precision

**Constitutional Stopwords:** ~150 words specific to legal texts

---

#### **Technique 3: Lemmatization**

**Purpose:** Reduce words to their base form

**Process:**
```
"rights" → lookup lemma_dict → "right"
"freedoms" → lookup lemma_dict → "freedom"
"establishing" → lookup lemma_dict → "establish"
```

**Why?**
- Makes search flexible (find "right" when searching for "rights")
- Reduces vocabulary size
- Improves recall (fewer misses)

**Approach:** Dictionary-based (pre-built lemma_dict)
- NOT using full NLP parsers (too heavy)
- Simple, fast, effective for domain

---

#### **Technique 4: Title Boosting**

**Purpose:** Give higher relevance to documents where query terms appear in titles

**Process:**
```
Base score = BM25_score(query, document)
Title boost = count(query_terms ∩ title_tokens) × 5.0
Final score = base_score + title_boost

Example:
Query: "freedom right"
Document A title: "Freedom of Movement" → 1 match → +5.0
Document B title: "Constitutional Rights" → 1 match → +5.0
Document C body only → 0 matches → +0.0
```

**Why?**
- Titles are more specific/focused
- Signal stronger relevance
- Boost factor (5.0) is tunable

---

### Libraries & Dependencies

From `requirements.txt`:
```
Flask==1.9.0              # Web framework
click==8.0               # CLI utility (dependency of Flask)
```

**Python Standard Library Used:**
- `json` - Loading/saving JSON data
- `math` - Logarithm calculations (IDF)
- `re` - Regular expressions (text normalization)
- `sys` - System utilities (path management)
- `pathlib` - File path handling

**No ML Libraries:**
- ❌ No scikit-learn
- ❌ No spaCy
- ❌ No transformers
- ✅ Pure algorithmic implementation

**Why No Heavy Libraries?**
- Keep system lightweight
- Full control over algorithms
- Educational clarity
- Faster startup time
- Easier deployment

---

## 8. API / INTERFACE

### REST API Specification

**Base URL:** `http://localhost:5000/api/v1` (default Flask dev server)

### Endpoint 1: Home

**Request:**
```http
GET /api/v1
```

**Response (200 OK):**
```json
{
  "message": "Welcome to the API!",
  "endpoints": {
    "/api/v1/health": "Check the health of the API.",
    "/api/v1/ask": "Submit a query to get a response."
  },
  "version": "1.0.0"
}
```

**Purpose:** API documentation & discovery

---

### Endpoint 2: Health Check

**Request:**
```http
GET /api/v1/health
```

**Response (200 OK):**
```json
{
  "status": "healthy"
}
```

**Purpose:** Verify API is running

**Use Case:** Uptime monitoring, load balancer health checks

---

### Endpoint 3: Ask Query (MAIN ENDPOINT)

**Request:**
```http
POST /api/v1/ask
Content-Type: application/json

{
  "query": "What are my freedom rights?"
}
```

**Response (200 OK):**
```json
{
  "query": "What are my freedom rights?",
  "response": "Found 5 relevant articles",
  "articles": [
    {
      "doc_id": "1.2",
      "article_no": 1,
      "title": "Constitution as the fundamental law",
      "text": "It shall be the duty of every person to observe this Constitution.",
      "citation": "Part 1, Article 1(2)",
      "score": 12.34
    },
    {
      "doc_id": "21.1",
      "article_no": 21,
      "title": "Right to freedom",
      "text": "Every person shall have the following rights...",
      "citation": "Part 3, Article 21(1)",
      "score": 11.89
    },
    ... (more results)
  ]
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "Missing 'query' field in request body"
}
```

---

### Request Format Specification

**Content-Type:** `application/json`

**Body:**
```json
{
  "query": "string (required, non-empty)",
  "top_k": "integer (optional, default=5)",
  "algorithm": "string (optional: 'bm25', 'boolean', 'tfidf', default='bm25')"
}
```

**Constraints:**
- `query` must be non-empty
- `query` max length: 500 characters (recommended)
- `top_k` range: 1-20 (default: 5)

**Example Requests:**
```bash
# Simple query
curl -X POST http://localhost:5000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the power of parliament?"}'

# With parameters
curl -X POST http://localhost:5000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "fundamental rights",
    "top_k": 10,
    "algorithm": "bm25"
  }'
```

---

### Response Format Specification

**Success Response (HTTP 200):**
```json
{
  "query": "string",           // Echo of input query
  "response": "string",        // Summary/explanation
  "articles": [
    {
      "doc_id": "string",                // Article.Clause.Subclause
      "article_no": "integer",           // Article number
      "title": "string",                 // Article title
      "text": "string",                  // Article text
      "citation": "string",              // Legal citation
      "score": "float",                  // Relevance score (0-100)
      "title_tokens": ["array"],         // For debugging
      "body_tokens": ["array"]           // For debugging
    }
  ]
}
```

**Error Response (HTTP 400/500):**
```json
{
  "error": "string"            // Error message
}
```

---

### Example Workflows

#### **Workflow 1: Basic Query**
```
User → "What are fundamental rights?"
  ↓
API processes & searches
  ↓
Returns Article 21, 22, 23, etc.
  ↓
Client displays results
```

#### **Workflow 2: Power User Query**
```
User (via command line) →
  curl -X POST /api/v1/ask \
    -d '{"query": "freedom of movement", "top_k": 15}'
  ↓
API returns 15 most relevant articles
  ↓
User processes programmatically
```

---

### Postman Collection

**Location:** `postman/collections/APIs/`

**Requests:**
- `Home.request.yaml` - Test root endpoint
- `Health.request.yaml` - Check health
- `Ask.request.yaml` - Submit questions

**Variables:**
- `{{base_url}}` - Points to API (defined in `postman/environments/Dev Env.environment.yaml`)

**Usage:**
1. Import collection into Postman
2. Set environment variables
3. Send requests

---

## 9. CURRENT IMPLEMENTATION STATUS

### ✅ COMPLETED FEATURES

1. **API Framework**
   - ✅ Flask setup with routing
   - ✅ Three endpoints: home, health, ask
   - ✅ JSON request/response handling
   - ✅ Postman collection for testing

2. **Data Preparation**
   - ✅ Complete constitution JSON (constitution_combined.json)
   - ✅ Flattened document structure (flattened_constitution.json)
   - ✅ ~550+ searchable articles/clauses
   - ✅ Pre-tokenized documents
   - ✅ Proper citations

3. **Text Processing**
   - ✅ Tokenization (normalize, split, punctuation removal)
   - ✅ Stopword filtering (~150 curated stopwords)
   - ✅ Lemmatization dictionary (lemma_dict_v3.json)
   - ✅ NLP preprocessing module

4. **Search Algorithms**
   - ✅ BM25 implementation (full algorithm)
   - ✅ Boolean AND search
   - ✅ TF-IDF scoring
   - ✅ Title boosting feature
   - ✅ Inverted index building
   - ✅ IDF calculation

5. **Infrastructure**
   - ✅ Python environment setup
   - ✅ Requirements file
   - ✅ Modular architecture
   - ✅ Data organization

---

### 🔶 PARTIALLY IMPLEMENTED

1. **API Integration**
   - 🔶 `/api/v1/ask` endpoint defined but logic is PLACEHOLDER
   - 🔶 No actual search algorithm connected
   - 🔶 No document loading
   - Current behavior: Returns dummy response

2. **Lemmatization**
   - 🔶 Three versions generated (v1, v2, v3)
   - 🔶 v3 is final but not integrated into main search
   - 🔶 NLP module exists but optional

---

### ❌ NOT IMPLEMENTED / MISSING

1. **Core Integration**
   - ❌ Flask route doesn't call search functions
   - ❌ No document loading at startup
   - ❌ No index initialization
   - ❌ Algorithm selection/switching not available

2. **Response Formatting**
   - ❌ "response" field is placeholder
   - ❌ No explanation generation
   - ❌ No confidence scores or ranking explanations

3. **Query Processing**
   - ❌ No input validation
   - ❌ No error handling
   - ❌ No query analysis (spelling check, expansion, etc.)
   - ❌ No caching

4. **Advanced Features**
   - ❌ No semantic search (would need embeddings)
   - ❌ No keyword extraction from results
   - ❌ No query suggestions/autocomplete
   - ❌ No multi-language support

5. **Performance**
   - ❌ No caching of indices
   - ❌ No persistence of computed indices
   - ❌ No database backend
   - ❌ No pagination for large result sets

6. **Monitoring & Logging**
   - ❌ No logging
   - ❌ No request/response logging
   - ❌ No error tracking
   - ❌ No performance metrics

---

### Priority Implementation Tasks

**Phase 1 (Essential):**
1. Connect `/api/v1/ask` endpoint to search algorithm
2. Load documents from JSON
3. Initialize BM25/search indices
4. Test end-to-end query flow

**Phase 2 (Important):**
1. Add input validation
2. Implement error handling
3. Add logging
4. Generate meaningful "response" explanations

**Phase 3 (Nice-to-have):**
1. Add caching for indices
2. Support algorithm selection
3. Semantic search with embeddings
4. Query analysis and expansion

---

## 10. CHALLENGES & LIMITATIONS

### Current Challenges

1. **API Logic Not Connected**
   - **Issue:** The `/api/v1/ask` endpoint is a skeleton with no actual search logic
   - **Impact:** Queries return placeholder responses
   - **Effort to Fix:** ~30-60 lines of code

2. **No Error Handling**
   - **Issue:** If documents fail to load, API crashes
   - **Impact:** Poor user experience
   - **Solution:** Try-catch blocks, validation, fallback responses

3. **Lemmatization Not Used in Main Search**
   - **Issue:** Advanced NLP module exists but not integrated
   - **Impact:** Better search quality possible but not deployed
   - **Solution:** Import and use `nlp.preprocess()` in app.py

4. **Duplicate Code**
   - **Issue:** BM25 implemented in both `bm25.py` and `ii_tf.py`
   - **Impact:** Maintenance difficulties, confusion
   - **Solution:** Consolidate into single module

5. **No Persistence**
   - **Issue:** Indices rebuild on every startup
   - **Impact:** Slower startup for large datasets
   - **Solution:** Pre-compute and cache indices

---

### System Limitations

#### **Scalability Limits**

| Factor | Current | Limit | Time |
|--------|---------|-------|------|
| Documents | ~550 | ~10,000 | Index: 2 sec → 20 sec |
| Query time | - | ~100ms | Startup: 5 sec → 30 sec |
| Memory | ~50MB | ~500MB | May need more for embeddings |

**What Breaks at Large Scale:**
- ❌ Index building on every startup
- ❌ In-memory data (no DB)
- ❌ No cluster support
- ❌ Single-threaded

**Scaling Strategies:**
1. **Database:** Use Elasticsearch or similar
2. **Caching:** Redis for index caching
3. **Distributed:** Kubernetes horizontal scaling
4. **Async:** Background index building

---

#### **Algorithmic Limitations**

1. **BM25 is Keyword-Based**
   - ❌ No semantic understanding
   - ❌ "fundamental rights" ≠ "basic freedoms"
   - ❌ Synonymy ignored
   - **Solution:** Semantic search with embeddings

2. **No Query Analysis**
   - ❌ "What are freedom rights?" treated same as "freedom rights"
   - ❌ No phrase detection
   - ❌ No entity recognition
   - **Solution:** NLP-based query parsing

3. **Title Boosting is Fixed**
   - ❌ Weight (5.0) not adaptive
   - ❌ No per-query optimization
   - **Solution:** Machine learning ranking

4. **No Explanation Generation**
   - ❌ Returns article text but no explanation
   - ❌ No highlighting of relevant parts
   - **Solution:** Extractive summarization, question-answering models

---

#### **Data Limitations**

1. **Single Language**
   - ❌ English only
   - ❌ No Nepali support (relevant for local users)
   - **Solution:** Bilingual indices

2. **Static Data**
   - ❌ No support for amendment tracking
   - ❌ No version history
   - **Solution:** Multi-version indices with timestamps

3. **Limited Metadata**
   - ❌ No cross-references between articles
   - ❌ No related articles suggestions
   - **Solution:** Parse and build cross-reference links

---

### Known Issues

1. **Issue:** `ii_tf.py` has embedded stopwords (200+), different from `stopwords.py` (150)
   - **Impact:** Inconsistent preprocessing between modules
   - **Status:** Low priority (both versions work)

2. **Issue:** Lemma dict v1, v2, v3 exist; v3 is recommended but not documented
   - **Impact:** Unclear which to use
   - **Status:** Documentation needed

3. **Issue:** Requirements.txt shows file corruption (binary data visible)
   - **Impact:** May need to regenerate or fix
   - **Status:** Verify before deployment

4. **Issue:** No handling of multi-part queries
   - **Impact:** "freedom AND rights" unsupported
   - **Status:** Known limitation

---

## 11. FUTURE IMPROVEMENTS

### Short-Term Improvements (1-2 weeks)

#### **1. Complete API Integration** 🔴 CRITICAL
```python
# In app.py, replace placeholder with:
from bm25 import BM25, search_bm25_with_boost
import json

@app.route("/api/v1/ask", methods=["POST"])
def ask():
    query = request.json.get("query", "").strip()
    
    if not query:
        return jsonify({"error": "Query cannot be empty"}), 400
    
    try:
        # Load documents
        with open("data/flattened_constitution.json") as f:
            documents = json.load(f)
        
        # Initialize search
        bm25_instance = BM25(documents)
        
        # Process query
        from text_processing import tokenize
        query_tokens = tokenize(query)
        
        if not query_tokens:
            return jsonify({"articles": [], "query": query})
        
        # Search
        results = search_bm25_with_boost(query, bm25_instance, documents, top_k=5)
        
        # Format response
        return jsonify({
            "query": query,
            "response": f"Found {len(results)} relevant articles",
            "articles": results
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```
**Time:** 1-2 hours  
**Impact:** Enables full search functionality

#### **2. Add Input Validation**
- Validate query length (max 500 chars)
- Check for SQL injection attempts (paranoid)
- Reject empty/whitespace queries
- **Time:** 30 minutes

#### **3. Error Handling**
- Try-catch for file not found
- Graceful fallback if index fails
- User-friendly error messages
- **Time:** 1 hour

#### **4. Integrate Lemmatization**
- Use `src/core/nlp.py` instead of simple tokenization
- Better query preprocessing
- **Time:** 30 minutes

---

### Medium-Term Improvements (1-3 months)

#### **5. Response Explanation Generation**
```python
# For each result, add:
{
  "explanation": "This article discusses freedom rights. "
                 "Your query matched: 'freedom' (3x), 'rights' (2x)",
  "relevance_reason": "Title match: 'Freedom' appears in title",
  "related_articles": ["1.2", "21.2"]  # Cross-references
}
```
**Components:**
- Highlight matching terms in article text
- Show frequency of matches
- Suggest related articles
**Challenge:** Extractive summarization or NLP-based

#### **6. Caching & Indexing Optimization**
- Pre-compute indices at build time
- Cache in files (pickle, msgpack)
- Load on startup (fast)
- **Performance Gain:** Startup 5s → 0.5s

#### **7. Algorithm Comparison Tool**
```python
# Endpoint: /api/v1/ask/compare
# Compare results from BM25, Boolean, TF-IDF
# Show which articles rank differently
```

#### **8. Query Expansion**
```python
# Synonyms: "rights" → "rights, freedoms, liberties"
# Expansion: "freedom" → "freedom, liberty, independence"
# Better recall for related concepts
```

---

### Long-Term Improvements (3+ months)

#### **9. Semantic Search with Embeddings**
```python
# Use: sentence-transformers or OpenAI embeddings
# Convert documents & queries to vectors
# Cosine similarity for relevance
# Benefits:
#   - Understand synonyms
#   - Match similar concepts
#   - Query: "Can I move freely?" → finds "freedom of movement"
# Tradeoff: More compute, larger model
```

#### **10. Machine Learning Ranking**
```python
# Training data: (query, article, relevance_label)
# Model: LambdaMART, BERT, etc.
# Learns optimal ranking weights
# Better than heuristic title boosting
```

#### **11. Multilingual Support**
```python
# Add Nepali language support
# Problems:
#   - Different tokenization rules
#   - Different stemming/lemmatization
#   - Different stopwords
# Solution: Language detection + appropriate pipeline
```

#### **12. Database Backend**
```python
# Replace JSON files with PostgreSQL + Elasticsearch
# Benefits:
#   - Persistent indices
#   - Multi-user support
#   - Version control/audit trail
#   - Scalability
```

---

### Feature Roadmap

```
Phase 1 (MVP Completion)     → API integration, validation
Phase 2 (Quality Improvement) → Explanations, caching, multi-algo
Phase 3 (Scaling)            → Database, distributed indexing
Phase 4 (Intelligence)       → Embeddings, ranking ML, QA
```

---

## 12. TECHNICAL DEBT & RECOMMENDATIONS

### Code Quality Issues

#### **Issue 1: Duplicate Implementations**
- **Files:** `bm25.py` vs `ii_tf.py` (both have BM25 code)
- **Recommendation:** Keep `bm25.py`, remove duplicates from `ii_tf.py`
- **Effort:** Low

#### **Issue 2: Inconsistent Tokenization**
- **Files:** `text_processing.py` vs `ii_tf.py` (different stopword lists)
- **Recommendation:** Use single tokenization module everywhere
- **Effort:** Medium

#### **Issue 3: Missing Type Hints**
- **Current:** No Python type annotations
- **Recommendation:** Add type hints (Python 3.7+)
- **Impact:** Better IDE support, bug detection

#### **Issue 4: No Unit Tests**
- **Recommendation:** Create test suite for:
  - Tokenization output
  - BM25 scoring
  - Index building
  - End-to-end queries
- **Coverage Target:** 80%+

---

### Architectural Recommendations

#### **Recommendation 1: Separate Concerns**
```
Current:     app.py
             ├── text_processing
             ├── bm25
             └── boolean_search

Better:      app.py (routing only)
             ├── search_service.py (orchestration)
             ├── preprocessing/
             │   ├── tokenizer.py
             │   └── lemmatizer.py
             ├── search/
             │   ├── bm25_ranking.py
             │   ├── boolean_ranking.py
             │   └── base_ranker.py (abstract)
             └── data/
                 ├── loader.py
                 └── indexer.py
```

#### **Recommendation 2: Configuration Management**
```python
# config.py
class Config:
    DOCUMENTS_PATH = "data/flattened_constitution.json"
    LEMMA_DICT_PATH = "data/lemma_dict_v3.json"
    TOP_K_DEFAULT = 5
    TITLE_BOOST = 5.0
    K1 = 1.5
    B = 0.75
    DEBUG = True
```

#### **Recommendation 3: Logging**
```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Search initiated for query: {query}")
logger.error(f"Failed to load documents: {e}")
logger.debug(f"BM25 scores: {scores}")
```

---

### Deployment Recommendations

1. **Use Environment Variables**
   - Don't hardcode paths
   - Use `python-dotenv` or similar

2. **Use Proper Web Server**
   - Don't use Flask dev server
   - Use Gunicorn, uWSGI, or similar

3. **Add Monitoring**
   - Request logging
   - Error tracking (Sentry)
   - Performance profiling

4. **Containerize**
   - Create `Dockerfile`
   - Use Docker Compose for local dev

---

## CONCLUSION

### Project Summary

This is an **information retrieval system** for Nepal's Constitution built with Flask, BM25 ranking, and custom text processing. The system is ~80% complete (all algorithms implemented, API skeleton exists) but needs final integration of search logic into the API endpoint.

### Key Strengths
✅ Multiple ranking algorithms  
✅ Clean data preprocessing  
✅ Well-structured codebase  
✅ Good documentation (now)  

### Key Gaps
❌ API endpoint not connected to search  
❌ No error handling  
❌ No result explanations  
❌ No caching/optimization  

### Next Steps (Priority Order)
1. **Connect API endpoint** (~2 hours)
2. **Add error handling** (~1 hour)
3. **Integrate lemmatization** (~30 mins)
4. **Add logging & monitoring** (~2 hours)
5. **Write unit tests** (~4 hours)

### Estimated Effort to Production
- **MVP (Basic search):** 1 day
- **Production-ready:** 1 week
- **Full-featured:** 4-6 weeks

---

**Document Generated:** April 15, 2026  
**Last Updated:** Current session  
**Status:** Complete reference documentation
