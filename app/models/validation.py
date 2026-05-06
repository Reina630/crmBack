"""
Modèle Validation - Suivi des validations DG
"""
from app.models.user import db
from datetime import datetime


class Validation(db.Model):
    """Validation DG d'un dossier"""

    __tablename__ = 'validations'

    id = db.Column(db.Integer, primary_key=True)

    # Dossier à valider
    dossier_id = db.Column(db.Integer, db.ForeignKey('dossiers.id'), nullable=False, unique=True, index=True)

    # Informations du dossier (cache pour performance)
    dossier_reference = db.Column(db.String(50), nullable=False)
    client_name = db.Column(db.String(120), nullable=False)
    responsible_name = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)

    # Statut de validation
    status = db.Column(db.String(20), default='en_attente', nullable=False, index=True)
    # en_attente, valide, rejete

    # Décision
    comment = db.Column(db.Text, nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)
    decided_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Métadonnées
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    priority = db.Column(db.String(20), default='normale')  # normale, haute, urgente

    # Relations
    dossier_ref = db.relationship('Dossier', backref='validation_record')
    validator = db.relationship('User', backref='validations_decided')

    def __repr__(self):
        return f'<Validation {self.id}: {self.dossier_reference} - {self.status}>'

    def to_dict(self):
        """Convertit la validation en dictionnaire"""
        return {
            'id': self.id,
            'dossier_id': self.dossier_id,
            'dossier_reference': self.dossier_reference,
            'client_name': self.client_name,
            'responsible_name': self.responsible_name,
            'amount': self.amount,
            'status': self.status,
            'comment': self.comment,
            'decided_at': self.decided_at.isoformat() if self.decided_at else None,
            'decided_by': self.decided_by,
            'validator_name': self.validator.username if self.validator else None,
            'submitted_at': self.submitted_at.isoformat(),
            'priority': self.priority
        }

    @staticmethod
    def create_validation(dossier):
        """Crée une demande de validation pour un dossier"""
        # Vérifier qu'il n'y a pas déjà une validation en cours
        existing = Validation.query.filter_by(dossier_id=dossier.id).first()
        if existing and existing.status == 'en_attente':
            return existing

        validation = Validation(
            dossier_id=dossier.id,
            dossier_reference=dossier.reference,
            client_name=dossier.client_data.name if dossier.client_data else 'Client inconnu',
            responsible_name=dossier.responsible.username if dossier.responsible else 'Responsable inconnu',
            amount=dossier.estimated_amount,
            priority=dossier.priority,
            status='en_attente'
        )

        db.session.add(validation)
        db.session.commit()
        return validation

    def approve(self, user_id, comment=None):
        """Approuve la validation"""
        self.status = 'valide'
        self.decided_at = datetime.utcnow()
        self.decided_by = user_id
        self.comment = comment

        # Mettre à jour le dossier
        if self.dossier_ref:
            self.dossier_ref.validate(user_id, comment)

        db.session.commit()

    def reject(self, user_id, comment=None):
        """Rejette la validation"""
        self.status = 'rejete'
        self.decided_at = datetime.utcnow()
        self.decided_by = user_id
        self.comment = comment

        # Mettre à jour le dossier
        if self.dossier_ref:
            self.dossier_ref.reject(user_id, comment)

        db.session.commit()

    @staticmethod
    def get_pending_validations():
        """Récupère toutes les validations en attente"""
        return Validation.query.filter_by(status='en_attente').order_by(
            Validation.priority.desc(),
            Validation.submitted_at.asc()
        ).all()

    @staticmethod
    def get_validations_stats():
        """Retourne les statistiques des validations"""
        total = Validation.query.count()
        pending = Validation.query.filter_by(status='en_attente').count()
        approved = Validation.query.filter_by(status='valide').count()
        rejected = Validation.query.filter_by(status='rejete').count()

        return {
            'total': total,
            'pending': pending,
            'approved': approved,
            'rejected': rejected
        }