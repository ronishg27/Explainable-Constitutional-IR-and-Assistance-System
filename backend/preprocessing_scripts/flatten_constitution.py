import json
import logging
from pathlib import Path
from src.core.text_processor import TextProcessor

logger = logging.getLogger(__name__)

_tokenizer = TextProcessor(use_lemmatization=True, remove_stopwords=True)

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


def _format_provision(provision_text):
    text = provision_text.strip()
    if text.startswith("Provided that"):
        return text
    return f"Provided that {text}"


def _format_explanation(explanation_text):
    text = explanation_text.strip()
    if text.startswith("Explanation:"):
        return text
    return f"Explanation: {text}"


def _flatten_sub_clauses(sub_clauses, parent_id, part_no, article_no, title, citation_prefix, level_num, create_docs=True):
    """Recursively flatten sub_clauses. Returns (inline_segments, documents)."""
    segments = []
    docs = []

    for index, sub in enumerate(sub_clauses, start=1):
        if level_num == 1:
            sub_id = sub.get("letter", str(index))
        else:
            sub_id = sub.get("clause_no", str(index))

        sub_text = sub.get("text", sub.get("freedom", ""))
        sub_segments = []

        if sub_text:
            sub_segments.append(sub_text.strip())

        provision = sub.get("provision", "")
        if provision:
            sub_segments.append(_format_provision(provision))

        explanation = sub.get("explanation", "")
        if explanation:
            sub_segments.append(_format_explanation(explanation))

        prefix = f"({sub_id})"
        joined = " ".join(sub_segments)
        if joined:
            segments.append(f"{prefix} {joined}")

        if create_docs:
            doc_id = f"{parent_id}.{sub_id}"
            body = "\n".join(sub_segments)
            if body:
                docs.append(
                    _make_document(
                        doc_id=doc_id,
                        part_no=part_no,
                        article_no=article_no,
                        clause_no=None,
                        subclause_id=str(sub_id),
                        level="sub-clause",
                        title=title,
                        text=body,
                        citation=f"{citation_prefix}({sub_id})",
                    )
                )

        nested = sub.get("sub_clauses", [])
        if nested:
            nested_segments, nested_docs = _flatten_sub_clauses(
                nested, parent_id, part_no, article_no, title,
                f"{citation_prefix}({sub_id})", level_num + 1,
                create_docs=create_docs
            )
            segments.extend(nested_segments)
            docs.extend(nested_docs)

    return segments, docs


def _make_document(doc_id, part_no, article_no, title, text, citation, level, clause_no=None, subclause_id=None):
    base_text = text.strip()

    lines = [f"Part {part_no} Article {article_no}"]
    if clause_no:
        lines.append(f"Clause {clause_no}")
    if subclause_id:
        lines.append(f"Subclause {subclause_id}")
    lines.append(title)
    lines.append(base_text)
    enriched_text = "\n".join(lines)

    citation_normalized = f"article {article_no}"
    if clause_no:
        citation_normalized += f" clause {clause_no}"
    if subclause_id:
        citation_normalized += f" subclause {subclause_id}"
    citation_normalized += f" part {part_no}"

    return {
        "doc_id": str(doc_id),
        "part_no": part_no,
        "article_no": article_no,
        "clause_no": clause_no,
        "subclause_id": subclause_id,
        "level": level,

        "is_primary": level in ["clause", "sub-clause"],
        "parent_id": str(article_no),

        "title": title,
        "text": enriched_text.strip(),
        "raw_text": base_text,

        "title_tokens": _tokenizer.process_text(title),
        "body_tokens": _tokenizer.process_text(enriched_text.strip()),

        "citation": citation,
        "citation_normalized": citation_normalized,

        "boost": 1.5 if level in ["clause", "sub-clause"] else 1.0
    }


def _flatten_clauses(clauses, article_no, part_no, title):
    """Process numbered clauses under an article. Returns list of clause documents."""
    docs = []
    for clause in clauses:
        clause_number = clause.get("clause_no", "?")
        clause_segments = []

        clause_text = clause.get("text", "")
        if clause_text:
            clause_segments.append(clause_text.strip())

        clause_provision = clause.get("provision", "")
        if clause_provision:
            clause_segments.append(_format_provision(clause_provision))

        clause_explanation = clause.get("explanation", "")
        if clause_explanation:
            clause_segments.append(_format_explanation(clause_explanation))

        clause_sub_clauses = clause.get("sub_clauses", [])
        if clause_sub_clauses:
            sub_segments, _ = _flatten_sub_clauses(
                clause_sub_clauses,
                f"{article_no}.{clause_number}",
                part_no, article_no, title,
                f"Part {part_no}, Article {article_no}({clause_number})",
                level_num=1,
                create_docs=False
            )
            clause_segments.extend(sub_segments)

        clause_body = "\n".join(segment for segment in clause_segments if segment)
        if clause_body:
            docs.append(
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
    return docs


def flatten_constitution(data):
    """Flattens nested structure to article, clause and sub-clause documents (new schema)."""
    documents = []

    for part in data.get("parts", []):
        part_no = part.get("part_no", "?")

        for article in part.get("articles", []):
            article_no = article.get("article_no", "?")
            title = article.get("title", "")
            article_segments = []

            article_text = article.get("text", "")
            if article_text:
                article_segments.append(article_text.strip())

            article_provision = article.get("provision", "")
            if article_provision:
                article_segments.append(_format_provision(article_provision))

            article_explanation = article.get("explanation", "")
            if article_explanation:
                article_segments.append(_format_explanation(article_explanation))

            sub_clauses = article.get("sub_clauses", [])
            clauses = article.get("clauses", [])

            if sub_clauses:
                sub_segments, _ = _flatten_sub_clauses(
                    sub_clauses, str(article_no), part_no, article_no, title,
                    f"Part {part_no}, Article {article_no}", level_num=1,
                    create_docs=False
                )
                article_segments.extend(sub_segments)

                article_body = "\n".join(segment for segment in article_segments if segment)
                if article_body:
                    documents.append(
                        _make_document(
                            doc_id=f"{article_no}",
                            part_no=part_no,
                            article_no=article_no,
                            clause_no=None,
                            subclause_id=None,
                            title=title,
                            text=article_body,
                            citation=f"Part {part_no}, Article {article_no}",
                            level="article",
                        )
                    )
                continue

            if clauses:
                documents.extend(
                    _flatten_clauses(clauses, article_no, part_no, title)
                )
                continue

            article_body = "\n".join(segment for segment in article_segments if segment)
            if article_body:
                documents.append(
                    _make_document(
                        doc_id=f"{article_no}",
                        part_no=part_no,
                        article_no=article_no,
                        clause_no=None,
                        subclause_id=None,
                        title=title,
                        text=article_body,
                        citation=f"Part {part_no}, Article {article_no}",
                        level="article",
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


        has_clauses = any(item.get("type") == "clause" for item in content)
        if not has_clauses:
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
    logging.basicConfig(level=logging.INFO)
    root = Path(__file__).resolve().parents[1]
    input_path = root / "data" / "nepal_constitution_new.json"
    output_path = root / "data" / "output" / "flattened_nepal_constitution.json"

    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Detect format and flatten accordingly
    if isinstance(data, list):
        # Flat list format (constitution_combined.json)
        documents = flatten_flat_constitution(data)
    else:
        # Nested format with parts (nepal_constitution.json)
        documents = flatten_constitution(data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)

    logger.info("Flattened %d documents into %s", len(documents), output_path)


if __name__ == "__main__":
    main()

