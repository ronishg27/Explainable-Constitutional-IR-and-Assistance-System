from mongoengine import Document, StringField, DateTimeField,FloatField
from datetime import datetime, timezone


class ReferencedArticle(Document):
    title = StringField(required=True)
    citation = StringField(required=True)
    doc_id = StringField(required=True)
    relevance_score = FloatField(required=True, min_value=0.0)
    
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
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
    def save(self, *args, **kwargs):
        # Auto-update timestamp on every save
        self.updated_at = datetime.now(timezone.utc)
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} (Score: {self.relevance_score})"