from datetime import datetime
from app.models.user import db

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informations client
    nom = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    
    # Date et heure du rendez-vous
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    
    # Motif et notes
    motif = db.Column(db.Text)
    
    # Statut du rendez-vous
    status = db.Column(
        db.String(20), 
        default='pending',
        nullable=False
    )  # pending, confirmed, cancelled, completed
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'telephone': self.telephone,
            'appointment_date': self.appointment_date.isoformat() if self.appointment_date else None,
            'appointment_time': self.appointment_time.strftime('%H:%M') if self.appointment_time else None,
            'motif': self.motif,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
        }
    
    @staticmethod
    def create_appointment(nom, telephone, appointment_date, appointment_time, motif=None):
        """Crée un nouveau rendez-vous"""
        appointment = Appointment(
            nom=nom,
            telephone=telephone,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            motif=motif,
            status='pending'
        )
        db.session.add(appointment)
        db.session.commit()
        return appointment
    
    def update_status(self, new_status):
        """Met à jour le statut du rendez-vous"""
        self.status = new_status
        
        if new_status == 'confirmed':
            self.confirmed_at = datetime.utcnow()
        elif new_status == 'completed':
            self.completed_at = datetime.utcnow()
        elif new_status == 'cancelled':
            self.cancelled_at = datetime.utcnow()
        
        db.session.commit()
