import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from text_processing import tokenize


def flatten_mvp_constitution(data):
    documents = []

    for part in data.get("parts", []):
        part_no = part.get("part_no", part.get("part_number", "?"))

        for article in part.get("articles", []):
            article_no = article.get("article_no", article.get("article_number", "?"))
            title = article.get("title", "")
            title_tokens = tokenize(title)

            clauses = article.get("clauses")
            if clauses is None:
                clauses = article.get("clause")

            if clauses:
                for clause_index, clause in enumerate(clauses, start=1):
                    clause_number = clause.get("clause_no", clause.get("clause_number", clause_index))
                    clause_text = clause.get("text", "")
                    subclauses = clause.get("sub_clauses", clause.get("subclauses"))

                    if subclauses:
                        for sub in subclauses:
                            sub_id = sub.get("letter", sub.get("subclause_number", "?"))
                            sub_text = sub.get("freedom", sub.get("text", ""))
                            if not sub_text:
                                continue

                            documents.append({
                                "doc_id": f"{article_no}.{clause_number}.{sub_id}",
                                "part_no": part_no,
                                "article_no": article_no,
                                "title": title,
                                "text": sub_text,
                                "citation": f"Part {part_no}, Article {article_no}({clause_number})({sub_id})",
                                "title_tokens": title_tokens,
                                "body_tokens": tokenize(sub_text),
                            })

                    elif clause_text:
                        documents.append({
                            "doc_id": f"{article_no}.{clause_number}",
                            "part_no": part_no,
                            "article_no": article_no,
                            "title": title,
                            "text": clause_text,
                            "citation": f"Part {part_no}, Article {article_no}({clause_number})",
                            "title_tokens": title_tokens,
                            "body_tokens": tokenize(clause_text),
                        })

            else:
                body_text = article.get("text", "")
                if body_text:
                    documents.append({
                        "doc_id": f"{article_no}",
                        "part_no": part_no,
                        "article_no": article_no,
                        "title": title,
                        "text": body_text,
                        "citation": f"Part {part_no}, Article {article_no}",
                        "title_tokens": title_tokens,
                        "body_tokens": tokenize(body_text),
                    })

    return documents


def main():
    root = Path(__file__).resolve().parents[1]
    input_path = root / "data" / "nepal_constitution_mvp.json"
    output_path = root / "data" / "flattened_nepal_constitution_mvp.json"

    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    documents = flatten_mvp_constitution(data)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)

    print(f"Flattened {len(documents)} documents into {output_path}")


if __name__ == "__main__":
    main()
