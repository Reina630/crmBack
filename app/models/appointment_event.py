"""
Modèle Appointment étendu - Gestion complète des rendez-vous et réunions
"""
from datetime import datetime
from app.models.user import db

class AppointmentEvent(db.Model):
    """Événements d'agenda (rendez-vous, réunions, appels, visites)"""
    
    __tablename__ = 'appointment_events'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informations de base
    title = db.Column(db.String(200), nullable=False)
    client_name = db.Column(db.String(100))
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    
    # Type d'événement
    type = db.Column(db.String(20), nullable=False)  # rendez-vous, appel, reunion, visite
    
    # Date et heure
    start_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_date = db.Column(db.Date)
    end_time = db.Column(db.Time)
    
    # Lieu et description
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    
    # Assignation
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    assigned_to = db.relationship('User', backref='appointments')
    
    # Statut et priorité
    status = db.Column(db.String(20), default='planifie', nullable=False)  # planifie, confirme, annule, termine
    priority = db.Column(db.String(20), default='moyenne')  # haute, moyenne, basse
    
    # Système de rappel
    reminder_minutes = db.Column(db.Integer, default=15)  # Minutes avant l'événement
    reminder_sent = db.Column(db.Boolean, default=False)
    
    # Participants (JSON array)
    participants = db.Column(db.JSON)
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<AppointmentEvent {self.id}: {self.title}>'
    
    def to_dict(self):
        """Convertit l'événement en dictionnaire"""
        return {
            'id': self.id,
            'title': self.title,
            'client_name': self.client_name,
            'client_id': self.client_id,
            'type': self.type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'location': self.location,
            'description': self.description,
            'assigned_to_id': self.assigned_to_id,
            'assigned_to': {
                'id': self.assigned_to.id,
                'username': self.assigned_to.username,
                'first_name': self.assigned_to.first_name,
                'last_name': self.assigned_to.last_name
            } if self.assigned_to else None,
            'status': self.status,
            'priority': self.priority,
            'reminder_minutes': self.reminder_minutes,
            'reminder_sent': self.reminder_sent,
            'participants': self.participants or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
