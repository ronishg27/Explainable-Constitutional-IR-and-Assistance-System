# 📜 Constitutional RAG UI/UX Specification

**Tech Stack:** React + Tailwind CSS
**Purpose:** Build a clean, explainable RAG interface for querying the Constitution of Nepal using an LLM (Ollama) and retrieved articles.

---

# 🎯 High-Level Goals

The UI should:

- Clearly present the **LLM-generated answer**
- Show **supporting constitutional articles (evidence)**
- Build **trust through transparency**
- Provide **interactive navigation between answer and sources**

---

# 🧩 Core Layout

## ✅ Split-Screen Layout (Desktop)

```
┌──────────────────────────────┬──────────────────────────────┐
│         Answer Panel         │       Articles Panel         │
│                              │                              │
│  Streaming LLM Answer        │  Ranked Article Cards        │
│  Citations (clickable)       │  Relevance + Highlights      │
│  Confidence Score            │  Expandable Content          │
│                              │                              │
└──────────────────────────────┴──────────────────────────────┘
```

### Layout Ratio:

- Left (Answer Panel): **60% width**
- Right (Articles Panel): **40% width**

---

## 📱 Mobile Layout

```
[ Answer Panel ]
----------------
[ Articles Panel ]
```

---

# 🧠 Component 1: Answer Panel

## Responsibilities

- Display **streaming response from LLM**
- Highlight and link **citations**
- Show **confidence level**
- Provide **loading state**

---

## 🔹 Features

### 1. Streaming Answer

- Display text as it is generated (typewriter or chunked streaming)
- Maintain readability (line spacing, paragraph breaks)

```jsx
<div className="prose max-w-none">{streamedAnswer}</div>
```

---

### 2. Clickable Citations

Example:

```
...right to freedom of expression (Article 17)
```

- Clicking `(Article 17)` should:
    - Scroll to corresponding article in right panel

---

### 3. Confidence Indicator

Display normalized score:

```
🟢 High Confidence (87%)
```

Color mapping:

- Green → High
- Yellow → Medium
- Red → Low

---

### 4. Answer Metadata

```
Based on 3 relevant articles
```

---

### 5. Loading State

While generating:

```
Thinking...
Analyzing articles...
Generating answer...
```

Optional animation:

```jsx
<div className="animate-pulse text-gray-500">Generating answer...</div>
```

---

# 📜 Component 2: Articles Panel

## Responsibilities

- Display retrieved articles
- Show ranking and relevance
- Explain _why_ each article was selected

---

## 🔹 Article Card Structure

```jsx
<div className="p-4 border rounded-xl shadow-sm">
	<h3 className="font-semibold">Article 17 – Right to Freedom</h3>

	<div className="text-sm text-green-600">🟢 Highly Relevant (92%)</div>

	<p className="mt-2 text-sm">
		Every citizen shall have the right to freedom...
	</p>

	<div className="mt-2 text-xs text-gray-500">
		✔ Keyword match ✔ Title match ✔ Term proximity
	</div>

	<button className="mt-2 text-blue-500 text-sm">View Details ▼</button>
</div>
```

---

## 🔹 Features

### 1. Relevance Label

| Score  | Label              |
| ------ | ------------------ |
| 85–100 | 🟢 Highly Relevant |
| 60–85  | 🟡 Relevant        |
| <60    | 🔴 Weak            |

---

### 2. Highlight Matched Terms

Example:

```
...right to **freedom** of **expression**
```

Implementation idea:

```jsx
function highlight(text, keywords) {
	// wrap matched words with <mark>
}
```

---

### 3. Expandable Content

- Default: short preview (2–3 lines)
- Expanded: full article text

---

### 4. Scroll Sync

- Clicking citation → scroll to article
- Use `ref` + `scrollIntoView()`

---

### 5. Optional: Scoring Details (Expandable)

```
▼ View scoring details

BM25: 6.94
Proximity: 3.01
Title Boost: +5
Final Boost: ×1.42
Total Score: 17.37
```

---

# 🔁 Interactions Between Panels

## 1. Citation Click → Scroll

- `(Article 17)` → scroll to article card

## 2. Article Hover → Highlight in Answer (optional)

- Advanced UX improvement

## 3. Article Click → Pin to Top (optional)

---

# 🔍 Query Input Section

## Top Search Bar

```jsx
<input
	type="text"
	placeholder="Ask about the Constitution of Nepal..."
	className="w-full p-3 border rounded-lg"
/>
```

---

## Suggested Queries

```
• What are fundamental rights?
• What is freedom of speech?
• What are duties of citizens?
```

---

# 📊 Score Presentation Strategy

## DO NOT show raw scores directly

Instead:

### Primary Display:

```
Relevance: 🟢 Highly Relevant (87%)
```

### Secondary (Expandable):

- Full IR breakdown

---

# 🎨 Design Guidelines

## Colors

- Primary: Blue
- Background: Neutral (white or gray-50)
- Relevance:
    - Green (#16a34a)
    - Yellow (#eab308)
    - Red (#dc2626)

---

## Typography

- Answer: larger font (`text-lg`)
- Articles: normal (`text-sm`)
- Use `prose` class for readability

---

## Spacing

- Use `p-4`, `gap-4`
- Avoid clutter

---

# ⚡ Performance Considerations

- Limit articles to **top 3–5**
- Lazy load full article content
- Debounce search input

---

# 🧪 Debug / Dev Mode (Optional)

Show:

```
Retrieved: 5 articles | Used: 3
```

---

# 🧱 Suggested Component Structure

```jsx
<App>
	<SearchBar />
	<MainLayout>
		<AnswerPanel />
		<ArticlesPanel />
	</MainLayout>
</App>
```

---

# 🚀 Advanced Features (Optional)

- “Explain simpler” button
- “More detailed answer”
- “Show only citations”
- Query history
- Dark mode toggle

---

# 🎯 Final UX Principle

> The UI should not just give answers — it should **prove them**

Users should always see:

- Where the answer came from
- Why those articles were chosen
- How confident the system is

---

# ✅ Deliverable Expectations for Coding Agent

- Fully responsive layout
- Smooth streaming support
- Scroll linking between answer ↔ articles
- Clean, minimal Tailwind styling
- Modular React components

---

**End of Spec**
