"""
Modèle pour les logs d'actions utilisateurs (audit trail)
"""
from app.models.user import db
from datetime import datetime


class ActionLog(db.Model):
    """Log de chaque action effectuée par les utilisateurs"""
    
    __tablename__ = 'action_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Qui a fait l'action
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Type d'action
    action_type = db.Column(
        db.String(50), 
        nullable=False,
        index=True
    )  # created, updated, deleted, validated, rejected, status_changed, etc.
    
    # Sur quel type d'entité
    entity_type = db.Column(
        db.String(50), 
        nullable=False,
        index=True
    )  # lead, pending_lead, service, user
    
    # ID de l'entité concernée
    entity_id = db.Column(db.Integer, nullable=False, index=True)
    
    # Changements effectués (JSON)
    changes = db.Column(db.JSON, nullable=True)  # {"before": {...}, "after": {...}}
    
    # Métadonnées
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 ou IPv6
    
    # Description lisible (optionnel)
    description = db.Column(db.String(500), nullable=True)
    
    # Relations
    user = db.relationship('User', backref='action_logs')
    
    def __repr__(self):
        return f'<ActionLog {self.id}: {self.user_id} {self.action_type} {self.entity_type}#{self.entity_id}>'
    
    def to_dict(self):
        """Convertit le log en dictionnaire"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'action_type': self.action_type,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'changes': self.changes,
            'description': self.description,
            'timestamp': self.timestamp.isoformat(),
            'ip_address': self.ip_address
        }
    
    @staticmethod
    def log_action(
        user_id: int,
        action_type: str,
        entity_type: str,
        entity_id: int,
        changes: dict = None,
        description: str = None,
        ip_address: str = None
    ):
        """
        Crée un log d'action
        
        Args:
            user_id: ID de l'utilisateur
            action_type: Type d'action (created, updated, deleted, etc.)
            entity_type: Type d'entité (lead, service, etc.)
            entity_id: ID de l'entité
            changes: Dictionnaire des changements
            description: Description lisible
            ip_address: Adresse IP
        """
        log = ActionLog(
            user_id=user_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=changes,
            description=description,
            ip_address=ip_address
        )
        db.session.add(log)
        db.session.commit()
        return log
