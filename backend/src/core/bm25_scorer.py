import math


class BM25Scorer:
    def __init__(
        self, 
        tf_index: dict[str, dict[str, int]],
        doc_lengths: dict[str, int],
        avgdl: float,
        k1: float = 1.5,
        b: float = 0.75   
    ):
        self.tf_index = tf_index
        self.doc_lengths = doc_lengths
        self.avgdl = avgdl
        self.k1 = k1
        self.b = b
        self.N = len(doc_lengths)
        
    def idf(self, term: str) -> float:
        df = len(self.tf_index.get(term, {}))
        if df == 0:
            return 0.0
        
        return math.log((self.N - df + 0.5) / (df + 0.5) + 1)
    
    def score(self, query_tokens: list[str], doc_id:str) -> float:
        total = 0.0
        doc_len = self.doc_lengths.get(doc_id, 0)
        if doc_len == 0:
            return 0.0
        
        for term in query_tokens:
            tf = self.tf_index.get(term, {}).get(doc_id, 0)
            if tf == 0:
                continue
            idf = self.idf(term)
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
            total += idf * (numerator / denominator)
        return total
    
    def score_with_title_boost(
        self,
        query_tokens: list[str],
        doc_id: str,
        title_tokens: list[str],
        title_boost: float = 5.0
    )-> float:
        base = self.score(query_tokens, doc_id)
        title_match_count = len(set(query_tokens) & set(title_tokens))
        return base+ (title_match_count * title_boost)
    
    