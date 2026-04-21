from mongoengine import Document, ReferenceField, StringField, DateTimeField, ListField
from datetime import timezone, datetime
from .user_model import User
from .referenced_article_model import ReferencedArticle


class Message(Document):
    query = StringField(required=True)
    answer = StringField()
    
    # reference fields
    user = ReferenceField(User, required=True, reverse_delete_rule=2)  # CASCADE
    articles = ListField(ReferenceField(ReferencedArticle, reverse_delete_rule=3), default=[])  # NULLIFY; store as List
    
    # timestamps
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    
    meta ={
        'collection': 'messages',
        'indexes': [
            'query', 'user', ('query', 'created_at')
        ],
        'ordering': ['-created_at']
    }
    
    def to_json(self):
        return {
            'id': str(self.id),
            'query': self.query,
            'answer': self.answer,
            'user': self.user.to_json() if self.user else None,
            'articles': [article.to_json() for article in self.articles],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __str__(self):
        return f"Message by {self.user.fullname if self.user else 'Unknown'}: {self.query[:50]}..."
    
    def save(self, *args, **kwargs):
        # Auto-update timestamp on every save
        self.updated_at = datetime.now(timezone.utc)
        return super().save(*args, **kwargs)