from flask_sqlalchemy import SQLAlchemy
from .lead import db

class Prospect(db.Model):
    __tablename__ = 'prospects'
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=False, unique=True)
    qualified_at = db.Column(db.DateTime, server_default=db.func.now())
    status = db.Column(db.String(50), default='en_cours')  # en_cours, converti, perdu
    notes = db.Column(db.Text)
    converted_at = db.Column(db.DateTime)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)

    # Relations
    lead = db.relationship('Lead', backref=db.backref('prospect', uselist=False))
    client = db.relationship('Client', backref='prospect', foreign_keys=[client_id])

    def to_dict(self):
        return {
            'id': self.id,
            'lead_id': self.lead_id,
            'qualified_at': self.qualified_at.isoformat() if self.qualified_at else None,
            'status': self.status,
            'notes': self.notes,
            'converted_at': self.converted_at.isoformat() if self.converted_at else None,
            'client_id': self.client_id,
            'lead': self.lead.to_dict() if self.lead else None
        }
