# Constitution JSON Schema — Single Source of Truth

## JSON Structure
<!-- C:\Users\Rons\OneDrive\Desktop\Constitution_assistant\backend\temp\data\nepal_constitution_extracted.json -->
```json
{
  "document": {
    "title": "Constitution of Nepal, 2072 (2015)",
    "year_np": 2072,
    "year_en": 2015
  },
  "parts": [
    {
      "part_no": 1,
      "part_title": "Preliminary",
      "articles": [
        {
          "article_no": 1,
          "title": "Constitution as the fundamental law",
          "explanation": "optional",
          "provision": "optional",
          "text": "use when article has direct text and NO clauses",
          "sub_clauses": [
            "optional — used as alternative to clauses (e.g. Article 51). Same shape as clause.sub_clauses below, with recursive nesting."
          ],
          "clauses": [
            {
              "clause_no": 1,
              "text": "clause text — lead-in only; no inline (a)(b)(c) if sub_clauses exist",
              "explanation": "optional",
              "provision": "optional — Provided that... rider",
              "sub_clauses": [
                {
                  "letter": "a",
                  "text": "sub-clause text",
                  "explanation": "optional",
                  "provision": "optional",
                  "sub_clauses": [
                    {
                      "clause_no": 1,
                      "text": "nested item text",
                      "explanation": "optional",
                      "provision": "optional"
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

## Rules

- An article has **either** `text` **or** `clauses` (array), never both
- An article can also have `sub_clauses` directly (alternative to `clauses`) — used for list-type articles like Article 51
- If a clause or article has `sub_clauses`, its `text` field must NOT contain inline `(a)(b)(c)` enumeration — only the lead-in sentence. The structured list lives in `sub_clauses`.
- A clause or article with inline `(a)(b)(c)` in `text` and NO `sub_clauses` array is using the flattened format (e.g. Article 48, Article 65). These are rendered inline.
- Cross-reference patterns like `sub-clause (a) of clause (1)` in `text` are NOT inline enumerations and must not be split into `sub_clauses`.
- `sub_clauses` can be nested recursively: level-1 items use `letter` as identifier, deeper items use `clause_no`
- `provision` is an optional string at any level, rendered as italic "Provided that..." block
- `explanation` is an optional string at any level, rendered as italic "Explanation:" block

## Field Reference

| Field | Appears On | Type | Notes |
|-------|-----------|------|-------|
| `document` | root | object | document metadata |
| `title` | document | string | |
| `year_np` | document | number | Nepali year |
| `year_en` | document | number | Gregorian year |
| `parts` | root | array | |
| `part_no` | part | number | |
| `part_title` | part | string | |
| `articles` | part | array | |
| `article_no` | article | number | |
| `title` | article | string | |
| `text` | article, clause | string (conditional) | Mutually exclusive with `clauses`; must not contain inline `(a)(b)(c)` if `sub_clauses` is present |
| `explanation` | article, clause, sub_clause | string (optional) | |
| `provision` | article, clause, sub_clause | string (optional) | "Provided that..." rider |
| `sub_clauses` | article, clause, sub_clause | array (optional) | Recursive — items deeper than level 1 use `clause_no` |
| `clauses` | article | array (conditional) | Mutually exclusive with `text` |
| `clause_no` | clause, nested sub_clause | number | |
| `letter` | sub_clause (level 1) | string | `"a"`, `"b"`, etc. |

## Rendering Behavior (constitution_preview.html)

| Field | CSS Class | Rendering |
|-------|-----------|-----------|
| `art.text` (with inline `(a)(b)(c)`, no `sub_clauses`) | `.article-text` | Split into inline list; items use `(a)`, `(b)` labels |
| `art.text` (plain, no inline markers) | `.article-text` | Plain block |
| `*.provision` | `.proviso` | Italic, prefixed "Provided that" |
| `*.explanation` | `.explanation` | Italic, prefixed "Explanation:" |
| `clause` text | `.clause-label` + `.clause-text` | `(n) text` inline |
| `sub_clause` (letter) | `.sc-label` + text | `(a) text` |
| `sub_clause` with nested items | `.nested-list` | Indented with left border, items use `(1)` labels |
