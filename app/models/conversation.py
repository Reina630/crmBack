from datetime import datetime
from app.models.user import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm.attributes import flag_modified

class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(100), unique=True, nullable=False)
    
    # Messages de la conversation (array JSON)
    messages = db.Column(JSON, default=list)
    
    # Informations du lead collecté
    lead_data = db.Column(JSON)
    score = db.Column(db.Float, default=0.0)
    
    # État de la conversation
    status = db.Column(db.String(50), default='active')  # active, completed, abandoned
    
    # Relations
    pending_lead_id = db.Column(db.Integer, db.ForeignKey('pending_leads.id'))
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'))
    
    # Métadonnées
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # En secondes
    message_count = db.Column(db.Integer, default=0)
    
    # IP et user agent pour analytics
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    
    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'messages': self.messages or [],
            'lead_data': self.lead_data,
            'score': self.score,
            'status': self.status,
            'pending_lead_id': self.pending_lead_id,
            'lead_id': self.lead_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': self.duration,
            'message_count': self.message_count,
            'ip_address': self.ip_address
        }
    
    @staticmethod
    def create_conversation(conversation_id, ip_address=None, user_agent=None):
        """Crée une nouvelle conversation"""
        conversation = Conversation(
            conversation_id=conversation_id,
            ip_address=ip_address,
            user_agent=user_agent,
            messages=[],
            status='active'
        )
        db.session.add(conversation)
        db.session.commit()
        return conversation
    
    def add_message(self, role, content):
        """Ajoute un message à la conversation"""
        if not self.messages:
            self.messages = []
        
        message = {
            'role': role,  # 'user' ou 'assistant'
            'content': content,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.messages.append(message)
        self.message_count = len(self.messages)
        
        # IMPORTANT : Signaler à SQLAlchemy que le JSON a changé
        flag_modified(self, 'messages')
        
        db.session.commit()
    
    def complete(self, lead_data=None, score=None, pending_lead_id=None):
        """Marque la conversation comme terminée"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        
        if self.started_at and self.completed_at:
            self.duration = int((self.completed_at - self.started_at).total_seconds())
        
        if lead_data:
            self.lead_data = lead_data
        if score is not None:
            self.score = score
        if pending_lead_id:
            self.pending_lead_id = pending_lead_id
        
        db.session.commit()
    
    def abandon(self):
        """Marque la conversation comme abandonnée"""
        self.status = 'abandoned'
        self.completed_at = datetime.utcnow()
        
        if self.started_at and self.completed_at:
            self.duration = int((self.completed_at - self.started_at).total_seconds())
        
        db.session.commit()
