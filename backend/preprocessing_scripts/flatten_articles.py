
from text_processing import tokenize

def flatten_articles(articles):
    documents = []
    for art in articles:
        # Tokenize the article title once per article (shared by all clauses)
        article_no = art.get("article_number", art.get("article_no"))
        part_no = art.get("part_number", art.get("part_no", "?"))
        title = art.get("title", "")
        title_tokens = tokenize(title)

        clauses = art.get("content")
        if clauses is None:
            clauses = art.get("clauses")

        # Support articles that contain direct text instead of clause arrays.
        if not clauses:
            body_text = art.get("text", "")
            if body_text:
                doc = {
                    "doc_id": f"{article_no}",
                    "article_no": article_no,
                    "title": title,
                    "text": body_text,
                    "citation": f"Part {part_no}, Article {article_no}",
                    "title_tokens": title_tokens,
                    "body_tokens": tokenize(body_text)
                }
                documents.append(doc)
            continue

        for clause_index, clause in enumerate(clauses, start=1):
            clause_number = clause.get("clause_number", clause.get("clause_no", clause_index))
            
            subclauses = clause.get("subclauses")
            if subclauses is None:
                subclauses = clause.get("sub_clauses")

            if subclauses:
                for sub in subclauses:
                    subclause_number = sub.get("subclause_number", sub.get("letter", "?"))
                    body_text = sub.get("text", sub.get("freedom", ""))
                    if not body_text:
                        continue
                    
                    doc = {
                        "doc_id": f"{article_no}.{clause_number}.{subclause_number}",
                        "article_no": article_no,
                        "title": title,
                        "text": body_text,
                        "citation": f"Part {part_no}, Article {article_no}({clause_number})({subclause_number})",
                        # NEW: Pre-tokenized fields for weighted scoring
                        "title_tokens": title_tokens,
                        "body_tokens": tokenize(body_text)
                    }
                    documents.append(doc)
            else:
                body_text = clause.get("text", "")
                if not body_text:
                    continue
                doc = {
                    "doc_id": f"{article_no}.{clause_number}",
                    "article_no": article_no,
                    "title": title,
                    "text": body_text,
                    "citation": f"Part {part_no}, Article {article_no}({clause_number})",
                    # NEW: Pre-tokenized fields for weighted scoring
                    "title_tokens": title_tokens,
                    "body_tokens": tokenize(body_text)
                }
                documents.append(doc)
    return documents

def main():
    import json
    with open("../data/constitution_combined.json", "r") as f:
        articles = json.load(f)
    
    documents = flatten_articles(articles)
    
    with open("../data/flattened_constitution.json", "w") as f:
        json.dump(documents, f, indent=2)

if __name__ == "__main__":
    main()