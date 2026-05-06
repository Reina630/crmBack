"""
Modèle Client - Répertoire central des clients
"""
from app.models.user import db
from datetime import datetime


class Client(db.Model):
    """Client officiel (distinct des leads/prospects)"""

    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)

    # Informations de base
    name = db.Column(db.String(120), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False)  # institution, pme, grande_entreprise

    # Contact principal
    contact_name = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)

    # Informations commerciales
    responsible_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    sector = db.Column(db.String(100), nullable=True)  # Secteur d'activité
    company_size = db.Column(db.String(50), nullable=True)  # TPE, PME, Grande entreprise

    # Métriques financières
    total_revenue = db.Column(db.Float, default=0.0)  # Chiffre d'affaires total généré
    dossiers_count = db.Column(db.Integer, default=0)  # Nombre de dossiers

    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relations
    responsible = db.relationship('User', backref='clients', foreign_keys=[responsible_id])
    dossiers = db.relationship('Dossier', back_populates='client_data', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Client {self.id}: {self.name}>'

    def to_dict(self):
        """Convertit le client en dictionnaire"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'contact_name': self.contact_name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'responsible_id': self.responsible_id,
            'responsible_name': self.responsible.username if self.responsible else None,
            'sector': self.sector,
            'company_size': self.company_size,
            'total_revenue': self.total_revenue,
            'dossiers_count': self.dossiers_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }

    @staticmethod
    def create_client(name, type, responsible_id, **kwargs):
        """Crée un nouveau client"""
        client = Client(
            name=name,
            type=type,
            responsible_id=responsible_id,
            **kwargs
        )
        db.session.add(client)
        db.session.commit()
        return client

    def update_revenue(self):
        """Recalcule le revenu total depuis les dossiers gagnés"""
        from app.models.dossier import Dossier
        total = db.session.query(db.func.sum(Dossier.estimated_amount)).filter(
            Dossier.client_id == self.id,
            Dossier.status == 'gagne'
        ).scalar() or 0.0
        self.total_revenue = total
        self.dossiers_count = len(self.dossiers)
        db.session.commit()