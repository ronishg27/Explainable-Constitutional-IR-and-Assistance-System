
from backend.text_processing import tokenize

def flatten_articles(articles):
    documents = []
    for art in articles:
        # Tokenize the article title once per article (shared by all clauses)
        title_tokens = tokenize(art["title"])
        
        for clause_index, clause in enumerate(art["content"], start=1):
            clause_number = clause.get("clause_number", clause_index)
            
            if "subclauses" in clause:
                for sub in clause["subclauses"]:
                    subclause_number = sub.get("subclause_number", "?")
                    body_text = sub["text"]
                    
                    doc = {
                        "doc_id": f"{art['article_number']}.{clause_number}.{subclause_number}",
                        "article_no": art["article_number"],
                        "title": art["title"],
                        "text": body_text,
                        "citation": f"Part {art['part_number']}, Article {art['article_number']}({clause_number})({subclause_number})",
                        # NEW: Pre-tokenized fields for weighted scoring
                        "title_tokens": title_tokens,
                        "body_tokens": tokenize(body_text)
                    }
                    documents.append(doc)
            else:
                body_text = clause["text"]
                doc = {
                    "doc_id": f"{art['article_number']}.{clause_number}",
                    "article_no": art["article_number"],
                    "title": art["title"],
                    "text": body_text,
                    "citation": f"Part {art['part_number']}, Article {art['article_number']}({clause_number})",
                    # NEW: Pre-tokenized fields for weighted scoring
                    "title_tokens": title_tokens,
                    "body_tokens": tokenize(body_text)
                }
                documents.append(doc)
    return documents

def main():
    import json
    with open("data/constitution_combined.json", "r") as f:
        articles = json.load(f)
    
    documents = flatten_articles(articles)
    
    with open("data/flattened_constitution.json", "w") as f:
        json.dump(documents, f, indent=2)

if __name__ == "__main__":
    main()