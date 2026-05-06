"""
Modèle Dossier - Suivi des opportunités commerciales
"""
from app.models.user import db
from datetime import datetime
import json


class Dossier(db.Model):
    """Dossier/Opportunité commerciale"""

    __tablename__ = 'dossiers'

    id = db.Column(db.Integer, primary_key=True)

    # Référence unique
    reference = db.Column(db.String(50), unique=True, nullable=False, index=True)

    # Lien avec prospect (avant conversion en client)
    prospect_id = db.Column(db.Integer, db.ForeignKey('prospects.id'), nullable=True, index=True)

    # Informations client (après conversion)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True, index=True)

    # Responsable du dossier
    responsible_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # Informations du dossier
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Origine et type
    origin = db.Column(db.String(50), nullable=False)  # prospection, client_existant, institution, demande_directe
    estimated_amount = db.Column(db.Float, nullable=False)

    # Statut et priorité
    status = db.Column(db.String(50), default='proposition', nullable=False, index=True)
    # proposition, gagnee, perdue, en_cours, terminee, annulee

    priority = db.Column(db.String(20), default='normale')  # normale, haute, urgente

    # Dates importantes
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_action = db.Column(db.String(100), nullable=True)  # Dernière action effectuée

    # Gestion de projet (pour statut en_cours)
    start_date = db.Column(db.DateTime, nullable=True)  # Date de début réelle du projet
    expected_end_date = db.Column(db.DateTime, nullable=True)  # Date de fin prévue
    actual_end_date = db.Column(db.DateTime, nullable=True)  # Date de fin réelle
    progress_percentage = db.Column(db.Integer, default=0)  # Avancement 0-100%

    # Validation DG
    requires_validation = db.Column(db.Boolean, default=False)
    validation_comment = db.Column(db.Text, nullable=True)
    validated_at = db.Column(db.DateTime, nullable=True)
    validated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Métadonnées
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relations
    prospect_data = db.relationship('Prospect', backref='opportunites', foreign_keys=[prospect_id])
    client_data = db.relationship('Client', back_populates='dossiers', foreign_keys=[client_id])
    responsible = db.relationship('User', backref='dossiers_responsible', foreign_keys=[responsible_id])
    validator = db.relationship('User', backref='validated_dossiers', foreign_keys=[validated_by])

    # Relations avec autres entités
    actions = db.relationship('DossierAction', back_populates='dossier_ref', lazy=True, cascade='all, delete-orphan')
    documents = db.relationship('Document', back_populates='dossier_ref', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Dossier {self.reference}: {self.title}>'

    def to_dict(self, include_actions=False, include_documents=False):
        """Convertit le dossier en dictionnaire"""
        result = {
            'id': self.id,
            'reference': self.reference,
            'prospect_id': self.prospect_id,
            'prospect_name': self.prospect_data.lead.name if self.prospect_data else None,
            'client_id': self.client_id,
            'client_name': self.client_data.name if self.client_data else None,
            'client_type': self.client_data.type if self.client_data else None,
            'responsible_id': self.responsible_id,
            'responsible_name': self.responsible.username if self.responsible else None,
            'title': self.title,
            'description': self.description,
            'origin': self.origin,
            'estimated_amount': self.estimated_amount,
            'status': self.status,
            'priority': self.priority,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_action': self.last_action,
            'requires_validation': self.requires_validation,
            'validation_comment': self.validation_comment,
            'validated_at': self.validated_at.isoformat() if self.validated_at else None,
            'validated_by': self.validated_by,
            'validator_name': self.validator.username if self.validator else None,
            'is_active': self.is_active,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'expected_end_date': self.expected_end_date.isoformat() if self.expected_end_date else None,
            'actual_end_date': self.actual_end_date.isoformat() if self.actual_end_date else None,
            'progress_percentage': self.progress_percentage
        }

        if include_actions and self.actions:
            result['actions'] = [action.to_dict() for action in self.actions]

        if include_documents and self.documents:
            result['documents'] = [doc.to_dict() for doc in self.documents]

        return result

    @staticmethod
    def generate_reference():
        """Génère une référence unique pour le dossier"""
        import random
        import string

        # Format: DOS-YYYY-NNNN (ex: DOS-2026-0001)
        year = datetime.now().year
        while True:
            # Générer un numéro aléatoire
            number = ''.join(random.choices(string.digits, k=4))
            reference = f"DOS-{year}-{number}"

            # Vérifier l'unicité
            if not Dossier.query.filter_by(reference=reference).first():
                return reference

    @staticmethod
    def create_dossier(client_id, responsible_id, title, estimated_amount, origin, **kwargs):
        """Crée un nouveau dossier"""
        reference = Dossier.generate_reference()

        dossier = Dossier(
            reference=reference,
            client_id=client_id,
            responsible_id=responsible_id,
            title=title,
            estimated_amount=estimated_amount,
            origin=origin,
            **kwargs
        )

        db.session.add(dossier)
        db.session.commit()

        # Créer l'action de création
        DossierAction.create_action(
            dossier_id=dossier.id,
            action_type='creation',
            description=f"Dossier créé avec référence {reference}",
            user_id=responsible_id
        )

        return dossier

    def add_action(self, action_type, description, user_id):
        """Ajoute une action au dossier"""
        action = DossierAction.create_action(
            dossier_id=self.id,
            action_type=action_type,
            description=description,
            user_id=user_id
        )
        self.last_action = f"{action_type}: {description}"
        db.session.commit()
        return action

    def submit_for_validation(self, user_id):
        """Soumet le dossier pour validation DG"""
        self.status = 'soumis'
        self.requires_validation = True
        self.add_action('soumission', 'Dossier soumis pour validation DG', user_id)
        db.session.commit()

    def validate(self, user_id, comment=None):
        """Valide le dossier (DG)"""
        self.status = 'valide'
        self.requires_validation = False
        self.validated_at = datetime.utcnow()
        self.validated_by = user_id
        self.validation_comment = comment
        self.add_action('validation', f'Dossier validé par DG{f": {comment}" if comment else ""}', user_id)
        db.session.commit()

    def reject(self, user_id, comment=None):
        """Rejette le dossier (DG)"""
        self.status = 'rejete'
        self.requires_validation = False
        self.validated_at = datetime.utcnow()
        self.validated_by = user_id
        self.validation_comment = comment
        self.add_action('rejet', f'Dossier rejeté par DG{f": {comment}" if comment else ""}', user_id)
        db.session.commit()

    def close(self, status, user_id, comment=None):
        """Clôt le dossier (gagné ou perdu)"""
        if status not in ['gagne', 'perdu']:
            raise ValueError("Le statut doit être 'gagne' ou 'perdu'")

        self.status = status
        action_desc = f'Dossier clôturé ({status})'
        if comment:
            action_desc += f': {comment}'

        self.add_action('cloture', action_desc, user_id)

        # Mettre à jour les métriques du client
        if self.client_data:
            self.client_data.update_revenue()

        db.session.commit()

    def update_progress(self):
        """Met à jour le pourcentage d'avancement basé sur les lignes terminées"""
        from app.models.opportunity_line import OpportunityLine
        
        lines = OpportunityLine.query.filter_by(opportunity_id=self.id).all()
        
        if not lines:
            self.progress_percentage = 0
            return 0
        
        total_lines = len(lines)
        completed_lines = sum(1 for line in lines if line.status == 'terminee')
        
        self.progress_percentage = int((completed_lines / total_lines) * 100)
        return self.progress_percentage


class DossierAction(db.Model):
    """Actions effectuées sur un dossier (historique)"""

    __tablename__ = 'dossier_actions'

    id = db.Column(db.Integer, primary_key=True)
    dossier_id = db.Column(db.Integer, db.ForeignKey('dossiers.id'), nullable=False, index=True)

    # Type d'action
    action_type = db.Column(db.String(50), nullable=False, index=True)
    # creation, modification, relance, soumission, validation, rejet, cloture

    # Description de l'action
    description = db.Column(db.Text, nullable=False)

    # Utilisateur qui a effectué l'action
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_name = db.Column(db.String(120), nullable=True)  # Cache du nom pour performance

    # Métadonnées
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relations
    dossier_ref = db.relationship('Dossier', back_populates='actions')
    user = db.relationship('User', backref='dossier_actions_user')

    def __repr__(self):
        return f'<DossierAction {self.id}: {self.action_type} on {self.dossier_id}>'

    def to_dict(self):
        """Convertit l'action en dictionnaire"""
        return {
            'id': self.id,
            'dossier_id': self.dossier_id,
            'action_type': self.action_type,
            'description': self.description,
            'user_id': self.user_id,
            'user_name': self.user_name or (self.user.username if self.user else 'Utilisateur inconnu'),
            'timestamp': self.timestamp.isoformat()
        }

    @staticmethod
    def create_action(dossier_id, action_type, description, user_id):
        """Crée une nouvelle action"""
        # Récupérer le nom de l'utilisateur pour le cache
        from app.models.user import User
        user = User.query.get(user_id)
        user_name = user.full_name if user else 'Utilisateur inconnu'

        action = DossierAction(
            dossier_id=dossier_id,
            action_type=action_type,
            description=description,
            user_id=user_id,
            user_name=user_name
        )
        
        db.session.add(action)
        return action
    
    def update_progress(self):
        """Met à jour le pourcentage d'avancement basé sur les lignes terminées"""
        if not self.lines:
            self.progress_percentage = 0
            return
        
        total_lines = len(self.lines)
        completed_lines = sum(1 for line in self.lines if line.status == 'terminee')
        
        self.progress_percentage = int((completed_lines / total_lines) * 100)
        return self.progress_percentage

        db.session.add(action)
        db.session.commit()
        return action