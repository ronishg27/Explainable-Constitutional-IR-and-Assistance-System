import json
import re
from pathlib import Path

TOKEN_RE = re.compile(r"[a-z]+(?:'[a-z]+)?")

IRREGULAR = {
    "ate": "eat",
    "eaten": "eat",
    "took": "take",
    "taken": "take",
    "gave": "give",
    "given": "give",
    "went": "go",
    "gone": "go",
    "did": "do",
    "done": "do",
    "does": "do",
    "has": "have",
    "had": "have",
    "was": "be",
    "were": "be",
    "been": "be",
    "is": "be",
    "are": "be",
    "am": "be",
    "men": "man",
    "women": "woman",
    "children": "child",
    "mice": "mouse",
    "teeth": "tooth",
    "feet": "foot",
}


def read_documents(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_vocab(documents):
    vocab = set()
    for doc in documents:
        for field in ("title", "text"):
            text = str(doc.get(field, "")).lower()
            vocab.update(TOKEN_RE.findall(text))
    return vocab


def undouble(token):
    if len(token) >= 2 and token[-1] == token[-2] and token[-1] not in "aeiou":
        return token[:-1]
    return token


def best_candidate(token, candidates, vocab):
    for cand in candidates:
        if cand in vocab:
            return cand
    return token


def lemma_for(token, vocab):
    if token in IRREGULAR and IRREGULAR[token] in vocab:
        return IRREGULAR[token]

    if token.endswith("ies") and len(token) > 4:
        return best_candidate(token, [token[:-3] + "y"], vocab)

    if token.endswith("es") and len(token) > 4:
        return best_candidate(token, [token[:-2], token[:-1]], vocab)

    if token.endswith("s") and len(token) > 3 and not token.endswith("ss"):
        return best_candidate(token, [token[:-1]], vocab)

    if token.endswith("ing") and len(token) > 5:
        stem = token[:-3]
        return best_candidate(token, [stem, undouble(stem), stem + "e"], vocab)

    if token.endswith("ed") and len(token) > 4:
        stem = token[:-2]
        return best_candidate(token, [stem, undouble(stem), stem + "e"], vocab)

    if token.endswith("er") and len(token) > 4:
        stem = token[:-2]
        return best_candidate(token, [stem, undouble(stem), stem + "e"], vocab)

    if token.endswith("est") and len(token) > 5:
        stem = token[:-3]
        return best_candidate(token, [stem, undouble(stem), stem + "e"], vocab)

    return token


def build_safe_dict(vocab):
    safe_dict = {}
    for token in sorted(vocab):
        safe_dict[token] = lemma_for(token, vocab)
    return safe_dict


def main():
    root = Path(__file__).resolve().parents[1]
    docs_path = root / "data" / "output" / "flattened_nepal_constitution.json"
    if not docs_path.exists():
        docs_path = root / "data" / "output" / "flattened_constitution.json"
    output_path = root / "data" / "output" / "lemma_dict_v3.json"

    documents = read_documents(docs_path)
    vocab = extract_vocab(documents)
    safe_dict = build_safe_dict(vocab)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(safe_dict, f, indent=2, sort_keys=True)

    changed = sum(1 for k, v in safe_dict.items() if k != v)
    print(f"vocab_size={len(vocab)}")
    print(f"lemma_entries={len(safe_dict)}")
    print(f"changed_mappings={changed}")
    print(f"output={output_path}")


if __name__ == "__main__":
    main()
