from mongoengine import Document, ListField, StringField, DateTimeField, FloatField, IntField
from datetime import datetime, timezone


class ReferencedArticle(Document):
    title = StringField(required=True)
    citation = StringField(required=True)
    doc_id = StringField(required=True)
    relevance_score = FloatField(required=True, min_value=0.0)
    bm25_score = FloatField(default=0.0)
    proximity_score = FloatField(default=0.0)
    title_match_count = IntField(default=0)
    article_no = IntField()
    clause_no = StringField()
    subclause_id = StringField()
    level = StringField()
    part_no = IntField()
    text = StringField()
    full_text = StringField()
    matched_terms = ListField(StringField(), default=list)
    exact_matched_terms = ListField(StringField(), default=list)

    # timestamps
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    meta = {
        'collection':'referenced_articles',
        'indexes':[
            'title', 'citation', 'doc_id', ('title', 'created_at')
        ],
        'ordering': ['-created_at']

    }

    def to_json(self):
        return {
            'id': str(self.id),
            'title': self.title,
            'citation': self.citation,
            'doc_id': self.doc_id,
            'relevance_score': self.relevance_score,
            'bm25_score': self.bm25_score,
            'proximity_score': self.proximity_score,
            'title_match_count': self.title_match_count,
            'article_no': self.article_no,
            'clause_no': self.clause_no,
            'subclause_id': self.subclause_id,
            'level': self.level,
            'part_no': self.part_no,
            'text': self.text,
            'full_text': self.full_text,
            'matched_terms': self.matched_terms,
            'exact_matched_terms': self.exact_matched_terms,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def save(self, *args, **kwargs):
        # Auto-update timestamp on every save
        self.updated_at = datetime.now(timezone.utc)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} (Score: {self.relevance_score})"

