"""
Modèle pour les leads en attente de validation
"""
from app.models.user import db
from datetime import datetime
import json


class PendingLead(db.Model):
    """Lead collecté par l'IA, en attente de validation par un commercial"""
    
    __tablename__ = 'pending_leads'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(100), nullable=False, index=True)  # Session ID du chat
    
    # Données collectées (stockées en JSON)
    data = db.Column(db.JSON, nullable=False)  # {nom, email, telephone, besoin, company, etc.}
    
    # Scoring et métadonnées
    score = db.Column(db.Float, default=0.0)  # Score de qualification (0-1)
    urgency = db.Column(db.String(20), default='moyenne')  # haute, moyenne, basse
    
    # Statut de validation
    status = db.Column(
        db.String(20), 
        default='pending',
        nullable=False,
        index=True
    )  # pending, validated, rejected
    
    # Traçabilité
    validated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Qui a validé/rejeté
    validated_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Notes du validateur
    validation_notes = db.Column(db.Text, nullable=True)
    
    # ID du lead créé après validation
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    
    # Relations
    validator = db.relationship('User', backref='validated_pending_leads', foreign_keys=[validated_by])
    lead = db.relationship('Lead', backref='pending_lead', foreign_keys=[lead_id])
    
    def __repr__(self):
        return f'<PendingLead {self.id} - {self.status}>'
    
    def to_dict(self):
        """Convertit le pending lead en dictionnaire"""
        result = {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'data': self.data,
            'score': self.score,
            'urgency': self.urgency,
            'status': self.status,
            'validated_by': self.validated_by,
            'validated_at': self.validated_at.isoformat() if self.validated_at else None,
            'created_at': self.created_at.isoformat(),
            'validation_notes': self.validation_notes,
            'lead_id': self.lead_id,
            'validator_name': self.validator.username if self.validator else None
        }
        
        # Récupérer les messages de la conversation associée
        from app.models.conversation import Conversation
        conversation = Conversation.query.filter_by(conversation_id=self.conversation_id).first()
        if conversation and conversation.messages:
            result['data']['messages'] = conversation.messages
        
        return result
    
    @property
    def name(self):
        """Récupère le nom depuis les données"""
        return self.data.get('nom', 'N/A')
    
    @property
    def email(self):
        """Récupère l'email depuis les données"""
        return self.data.get('email', 'N/A')
    
    @property
    def phone(self):
        """Récupère le téléphone depuis les données"""
        return self.data.get('telephone', 'N/A')
    
    @property
    def need(self):
        """Récupère le besoin depuis les données"""
        return self.data.get('besoin', 'N/A')
