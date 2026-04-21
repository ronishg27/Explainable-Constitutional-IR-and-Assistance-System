from enum import Enum

from mongoengine import Document, StringField,  DateTimeField,  EnumField
from datetime import datetime, timezone
import bcrypt

class RoleEnum(Enum):
    USER = 'user'
    ADMIN = 'admin'
    

class User(Document):
    fullname = StringField(required=True, min_length=3, max_length=50)
    email = StringField(required=True, unique=True)
    password_hash = StringField(required=True)
    role = EnumField(RoleEnum, default=RoleEnum.USER)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    
    meta = {
        'collection': 'users',  # Collection name
        'indexes': [            # indexes
            'email',
            ('fullname', 'created_at')
        ],
        'ordering': ['-created_at']  # Default sort
    }
    


    def set_password(self, password):
        """Hash password and store the hash."""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password):
        """Verify password against stored hash."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def to_json(self):
        """Custom JSON representation"""
        return {
            'id': str(self.id),
            'fullname': self.fullname,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __str__(self):
        return self.fullname
    
    
    def save(self, *args, **kwargs):
        # Auto-update timestamp on every save
        self.updated_at = datetime.now(timezone.utc)
        return super().save(*args, **kwargs)