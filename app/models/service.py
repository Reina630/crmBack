from flask_sqlalchemy import SQLAlchemy
from app.models.lead import db

class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    price_range = db.Column(db.String(100))  # Ex: "5000-15000€", "Sur devis"
    
    # Hiérarchie des services
    parent_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=True)
    category = db.Column(db.String(100))  # communication_classique, communication_digitale, solutions_numeriques
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    # Relations
    leads = db.relationship('Lead', backref='service', lazy=True)
    children = db.relationship('Service', backref=db.backref('parent', remote_side=[id]), lazy=True)

    def to_dict(self, include_children=False):
        """Convertir en dictionnaire"""
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price_range': self.price_range,
            'category': self.category,
            'parent_id': self.parent_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'lead_count': len(self.leads)  # Nombre de leads pour ce service
        }
        
        if include_children and self.children:
            result['children'] = [child.to_dict() for child in self.children if child.is_active]
            
        return result