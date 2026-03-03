from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import json

db = SQLAlchemy()

class ChatSession(db.Model):
    """Represents a single chat conversation session."""
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    title = db.Column(db.String(255), nullable=True) # Optional summary title
    
    # Relationship to messages
    messages = db.relationship('ChatMessage', backref='session', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "title": self.title
        }

class ChatMessage(db.Model):
    """Represents a single message within a chat session."""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey('chat_sessions.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    sources_json = db.Column(db.Text, nullable=True) # Stored as JSON string
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "sources": json.loads(self.sources_json) if self.sources_json else [],
            "timestamp": self.timestamp.isoformat()
        }
