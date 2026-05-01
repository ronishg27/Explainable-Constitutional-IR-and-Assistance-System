import json
from .document import Document

class IndexBuilder:
    def __init__(self, bm25_processor, proximity_processor):
        self.bm25_processor = bm25_processor
        self.proximity_processor = proximity_processor

    def build_tf_index(self, documents: list[Document]) -> dict[str, dict[str, int]]:
        index = {}
        for doc in documents:
            tokens = self.bm25_processor.process_text(doc.text)
            for token in tokens:
                index.setdefault(token, {})
                index[token][doc.doc_id] = index[token].get(doc.doc_id, 0) + 1
        return index

    def build_positional_index(self, documents: list[Document]) -> dict[str, dict[str, list[int]]]:
        index = {}
        for doc in documents:
            tokens = self.proximity_processor.process_text(doc.text)
            for pos, token in enumerate(tokens):
                index.setdefault(token, {})
                index[token].setdefault(doc.doc_id, []).append(pos)
        return index

    def compute_doc_stats(self, documents: list[Document]):
        doc_lengths = {}
        total = 0
        for doc in documents:
            tokens = self.bm25_processor.process_text(doc.text)
            doc_lengths[doc.doc_id] = len(tokens)
            total += len(tokens)
        avgdl = total / len(documents) if documents else 0.0
        return doc_lengths, avgdl

    def save_json(self, data, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_json(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def run(self, documents: list[Document], output_dir: str):
        tf_index = self.build_tf_index(documents)
        pos_index = self.build_positional_index(documents)
        doc_lengths, avgdl = self.compute_doc_stats(documents)

        self.save_json(tf_index, f"{output_dir}/tf_index.json")
        self.save_json(pos_index, f"{output_dir}/pos_index.json")
        self.save_json({"doc_lengths": doc_lengths, "avgdl": avgdl},
                       f"{output_dir}/doc_stats.json")