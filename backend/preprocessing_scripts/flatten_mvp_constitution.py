import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from text_processing import tokenize


def _label_key(key):
    return key.replace("_", " ").strip().capitalize()


def _collect_extra_fields(obj, excluded_keys):
    extras = []
    for key, value in obj.items():
        if key in excluded_keys:
            continue
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        extras.append((_label_key(key), str(value).strip()))
    return extras


def _make_document(doc_id, part_no, article_no, title, text, citation, level, clause_no=None, subclause_id=None):
    return {
        "doc_id": str(doc_id),
        "part_no": part_no,
        "article_no": article_no,
        "clause_no": clause_no,
        "subclause_id": subclause_id,
        "level": level,
        "title": title,
        "text": text,
        "citation": citation,
        "title_tokens": tokenize(title),
        "body_tokens": tokenize(text),
    }


def flatten_mvp_constitution(data):
    """Flattens nested structure to article, clause and sub-clause documents."""
    documents = []

    for part in data.get("parts", []):
        part_no = part.get("part_no", part.get("part_number", "?"))

        for article in part.get("articles", []):
            article_no = article.get("article_no", article.get("article_number", "?"))
            title = article.get("title", "")
            article_segments = []

            article_text = article.get("text", "")
            if article_text:
                article_segments.append(article_text.strip())

            clauses = article.get("clauses")
            if clauses is None:
                clauses = article.get("clause")

            if clauses:
                for clause_index, clause in enumerate(clauses, start=1):
                    clause_number = clause.get("clause_no", clause.get("clause_number", clause_index))
                    clause_text = clause.get("text", "")
                    subclauses = clause.get("sub_clauses", clause.get("subclauses"))

                    if clause_text:
                        article_segments.append(f"({clause_number}) {clause_text.strip()}")

                    clause_extras = _collect_extra_fields(
                        clause,
                        {
                            "clause_no",
                            "clause_number",
                            "text",
                            "sub_clauses",
                            "subclauses",
                        },
                    )
                    for label, value in clause_extras:
                        article_segments.append(f"({clause_number}) [{label}] {value}")

                    if subclauses:
                        for sub_index, sub in enumerate(subclauses, start=1):
                            sub_id = sub.get("letter", sub.get("subclause_number", sub_index))
                            sub_text = sub.get("freedom", sub.get("text", ""))
                            if sub_text:
                                article_segments.append(
                                    f"({clause_number})({sub_id}) {sub_text.strip()}"
                                )

                            sub_extras = _collect_extra_fields(
                                sub,
                                {
                                    "letter",
                                    "subclause_number",
                                    "freedom",
                                    "text",
                                },
                            )
                            for label, value in sub_extras:
                                article_segments.append(
                                    f"({clause_number})({sub_id}) [{label}] {value}"
                                )

            article_extras = _collect_extra_fields(
                article,
                {
                    "article_no",
                    "article_number",
                    "title",
                    "text",
                    "clauses",
                    "clause",
                },
            )
            for label, value in article_extras:
                article_segments.append(f"[{label}] {value}")

            article_body = "\n".join(segment for segment in article_segments if segment)
            if article_body:
                documents.append(
                    _make_document(
                        doc_id=f"{article_no}",
                        part_no=part_no,
                        article_no=article_no,
                        title=title,
                        text=article_body,
                        citation=f"Part {part_no}, Article {article_no}",
                        level="article",
                    )
                )

            if clauses:
                for clause_index, clause in enumerate(clauses, start=1):
                    clause_number = clause.get("clause_no", clause.get("clause_number", clause_index))
                    clause_segments = []

                    clause_text = clause.get("text", "")
                    if clause_text:
                        clause_segments.append(clause_text.strip())

                    clause_extras = _collect_extra_fields(
                        clause,
                        {
                            "clause_no",
                            "clause_number",
                            "text",
                            "sub_clauses",
                            "subclauses",
                        },
                    )
                    for label, value in clause_extras:
                        clause_segments.append(f"[{label}] {value}")

                    clause_body = "\n".join(segment for segment in clause_segments if segment)
                    if clause_body:
                        documents.append(
                            _make_document(
                                doc_id=f"{article_no}.{clause_number}",
                                part_no=part_no,
                                article_no=article_no,
                                clause_no=clause_number,
                                subclause_id=None,
                                title=title,
                                text=clause_body,
                                citation=f"Part {part_no}, Article {article_no}({clause_number})",
                                level="clause",
                            )
                        )

                    subclauses = clause.get("sub_clauses", clause.get("subclauses"))
                    if subclauses:
                        for sub_index, sub in enumerate(subclauses, start=1):
                            sub_id = sub.get("letter", sub.get("subclause_number", sub_index))
                            sub_segments = []

                            sub_text = sub.get("freedom", sub.get("text", ""))
                            if sub_text:
                                sub_segments.append(sub_text.strip())

                            sub_extras = _collect_extra_fields(
                                sub,
                                {
                                    "letter",
                                    "subclause_number",
                                    "freedom",
                                    "text",
                                },
                            )
                            for label, value in sub_extras:
                                sub_segments.append(f"[{label}] {value}")

                            sub_body = "\n".join(segment for segment in sub_segments if segment)
                            if sub_body:
                                documents.append(
                                    _make_document(
                                        doc_id=f"{article_no}.{clause_number}.{sub_id}",
                                        part_no=part_no,
                                        article_no=article_no,
                                        clause_no=clause_number,
                                        subclause_id=sub_id,
                                        title=title,
                                        text=sub_body,
                                        citation=f"Part {part_no}, Article {article_no}({clause_number})({sub_id})",
                                        level="sub-clause",
                                    )
                                )

    return documents


def flatten_flat_constitution(data):
    """Flattens flat list structure to article and clause documents."""
    documents = []

    for article in data:
        article_no = article.get("article_number", "?")
        part_no = article.get("part_number", "?")
        title = article.get("title", "")
        article_segments = []

        content = article.get("content", [])
        if content:
            for item_index, item in enumerate(content, start=1):
                item_type = item.get("type", "")
                item_text = item.get("text", "")

                if item_type == "clause":
                    clause_number = item.get("clause_number", "")
                    if clause_number and item_text:
                        article_segments.append(f"({clause_number}) {item_text.strip()}")

                    clause_segments = []
                    if item_text:
                        clause_segments.append(item_text.strip())

                    item_extras = _collect_extra_fields(
                        item,
                        {"type", "clause_number", "text"},
                    )
                    for label, value in item_extras:
                        clause_segments.append(f"[{label}] {value}")

                    clause_body = "\n".join(segment for segment in clause_segments if segment)
                    if clause_body and clause_number != "":
                        documents.append(
                            _make_document(
                                doc_id=f"{article_no}.{clause_number}",
                                part_no=part_no,
                                article_no=article_no,
                                clause_no=clause_number,
                                subclause_id=None,
                                title=title,
                                text=clause_body,
                                citation=f"Part {part_no}, Article {article_no}({clause_number})",
                                level="clause",
                            )
                        )
                elif item_type == "paragraph":
                    if item_text:
                        article_segments.append(item_text.strip())
                else:
                    # Generic content item
                    if item_text:
                        article_segments.append(item_text.strip())

                # Collect extra fields from content items
                item_extras = _collect_extra_fields(
                    item,
                    {"type", "clause_number", "text"},
                )
                for label, value in item_extras:
                    article_segments.append(f"[Item {item_index} {label}] {value}")

        article_extras = _collect_extra_fields(
            article,
            {
                "article_number",
                "part_number",
                "title",
                "content",
            },
        )
        for label, value in article_extras:
            article_segments.append(f"[{label}] {value}")

        body_text = "\n".join(segment for segment in article_segments if segment)
        if body_text:
            documents.append(
                _make_document(
                    doc_id=f"{article_no}",
                    part_no=part_no,
                    article_no=article_no,
                    clause_no=None,
                    subclause_id=None,
                    title=title,
                    text=body_text,
                    citation=f"Part {part_no}, Article {article_no}",
                    level="article",
                )
            )

    return documents


def main():
    root = Path(__file__).resolve().parents[1]
    input_path = root / "data" / "constitution_combined.json"
    output_path = root / "data" / "flattened_nepal_constitution.json"

    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Detect format and flatten accordingly
    if isinstance(data, list):
        # Flat list format (constitution_combined.json)
        documents = flatten_flat_constitution(data)
    else:
        # Nested format with parts (nepal_constitution_mvp.json)
        documents = flatten_mvp_constitution(data)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)

    print(f"Flattened {len(documents)} documents into {output_path}")


if __name__ == "__main__":
    main()
