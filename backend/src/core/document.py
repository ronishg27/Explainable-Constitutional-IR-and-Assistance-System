from dataclasses import dataclass
from typing import Optional

@dataclass
class Document:
    doc_id: str
    part_no: str
    article_no: str
    title: str
    text: str
    citation: str
    level: str
    clause_no: Optional[str] = None
    subclause_id: Optional[str] = None
    is_primary: bool = False
    parent_id: Optional[str] = None

    raw_text: Optional[str] = None
    citation_normalized: Optional[str] = None

    boost: float = 1.0

