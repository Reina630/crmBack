"""
Modèle OpportunityLine - Lignes de prestations d'une opportunité
"""
from app.models.user import db
from datetime import datetime


class OpportunityLine(db.Model):
    """Ligne de prestation dans une opportunité/devis"""

    __tablename__ = 'opportunity_lines'

    id = db.Column(db.Integer, primary_key=True)
    
    # Référence à l'opportunité
    opportunity_id = db.Column(db.Integer, db.ForeignKey('dossiers.id'), nullable=False, index=True)
    
    # Informations de la ligne
    category = db.Column(db.String(100), nullable=False)  # BRANDING, BRANDING EXTERIEUR, etc.
    designation = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer, default=1, nullable=False)  # Durée en mois
    total = db.Column(db.Float, nullable=False)  # Montant total de la ligne
    
    # Ordre d'affichage
    order_index = db.Column(db.Integer, default=0)
    
    # Suivi de production (pour les projets en_cours)
    status = db.Column(db.String(20), default='a_faire')  # a_faire, en_production, terminee
    production_notes = db.Column(db.Text, nullable=True)  # Notes de l'équipe production
    completed_at = db.Column(db.DateTime, nullable=True)  # Date de fin de production
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation
    opportunity = db.relationship('Dossier', backref='lines', foreign_keys=[opportunity_id])
    
    def __repr__(self):
        return f'<OpportunityLine {self.id}: {self.designation}>'
    
    def to_dict(self):
        """Convertit la ligne en dictionnaire"""
        return {
            'id': self.id,
            'opportunity_id': self.opportunity_id,
            'category': self.category,
            'designation': self.designation,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'duration': self.duration,
            'total': self.total,
            'order_index': self.order_index,
            'status': self.status,
            'production_notes': self.production_notes,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def calculate_total(quantity, unit_price, duration):
        """Calcule le total d'une ligne"""
        return quantity * unit_price * duration
