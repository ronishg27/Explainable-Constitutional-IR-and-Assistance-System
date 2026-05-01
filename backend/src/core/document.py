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