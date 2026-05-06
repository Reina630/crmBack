"""
Modèle Notification - Alertes et notifications système
"""
from app.models.user import db
from datetime import datetime


class Notification(db.Model):
    """Notification système pour les utilisateurs"""

    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)

    # Destinataire
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # Contenu de la notification
    type = db.Column(db.String(50), nullable=False, index=True)
    # relance, validation, dossier, alert, system

    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)

    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    read = db.Column(db.Boolean, default=False, nullable=False, index=True)

    # Lien optionnel (vers une page spécifique)
    link = db.Column(db.String(500), nullable=True)

    # Données supplémentaires (JSON)
    data = db.Column(db.JSON, nullable=True)

    # Relations
    user = db.relationship('User', backref='notifications')

    def __repr__(self):
        return f'<Notification {self.id}: {self.type} for {self.user_id}>'

    def to_dict(self):
        """Convertit la notification en dictionnaire"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'created_at': self.created_at.isoformat(),
            'read': self.read,
            'link': self.link,
            'data': self.data
        }

    def mark_as_read(self):
        """Marque la notification comme lue"""
        self.read = True
        db.session.commit()

    @staticmethod
    def create_notification(user_id, type, title, message, link=None, data=None):
        """Crée une nouvelle notification"""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            link=link,
            data=data
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    @staticmethod
    def create_bulk_notifications(user_ids, type, title, message, link=None, data=None):
        """Crée des notifications pour plusieurs utilisateurs"""
        notifications = []
        for user_id in user_ids:
            notification = Notification(
                user_id=user_id,
                type=type,
                title=title,
                message=message,
                link=link,
                data=data
            )
            notifications.append(notification)

        db.session.add_all(notifications)
        db.session.commit()
        return notifications

    @staticmethod
    def get_unread_count(user_id):
        """Retourne le nombre de notifications non lues pour un utilisateur"""
        return Notification.query.filter_by(
            user_id=user_id,
            read=False
        ).count()

    @staticmethod
    def get_user_notifications(user_id, limit=50, offset=0):
        """Récupère les notifications d'un utilisateur"""
        return Notification.query.filter_by(user_id=user_id).order_by(
            Notification.created_at.desc()
        ).limit(limit).offset(offset).all()

    @staticmethod
    def mark_all_as_read(user_id):
        """Marque toutes les notifications d'un utilisateur comme lues"""
        Notification.query.filter_by(user_id=user_id, read=False).update({'read': True})
        db.session.commit()


class NotificationTemplate:
    """Templates prédéfinis pour les notifications"""

    # Templates pour les relances
    RELANCE_DOSSIER = {
        'type': 'relance',
        'title': 'Relance nécessaire',
        'message': 'Le dossier {reference} nécessite une relance depuis {days} jours.',
        'link': '/dossiers/{dossier_id}'
    }

    # Templates pour les validations
    VALIDATION_PENDING = {
        'type': 'validation',
        'title': 'Validation en attente',
        'message': 'Le dossier {reference} ({client}) est en attente de validation.',
        'link': '/validations'
    }

    VALIDATION_APPROVED = {
        'type': 'validation',
        'title': 'Dossier validé',
        'message': 'Votre dossier {reference} a été validé par la direction.',
        'link': '/dossiers/{dossier_id}'
    }

    VALIDATION_REJECTED = {
        'type': 'validation',
        'title': 'Dossier rejeté',
        'message': 'Votre dossier {reference} a été rejeté par la direction.',
        'link': '/dossiers/{dossier_id}'
    }

    # Templates pour les dossiers
    DOSSIER_CREATED = {
        'type': 'dossier',
        'title': 'Nouveau dossier',
        'message': 'Un nouveau dossier {reference} a été créé pour {client}.',
        'link': '/dossiers/{dossier_id}'
    }

    DOSSIER_UPDATED = {
        'type': 'dossier',
        'title': 'Dossier mis à jour',
        'message': 'Le dossier {reference} a été mis à jour.',
        'link': '/dossiers/{dossier_id}'
    }

    # Templates pour les leads
    LEAD_VALIDATED = {
        'type': 'alert',
        'title': 'Lead validé',
        'message': 'Le lead {name} a été validé et transformé en prospect.',
        'link': '/prospection'
    }

    @classmethod
    def format_message(cls, template, **kwargs):
        """Formate un message de template avec les variables"""
        return template['message'].format(**kwargs)

    @classmethod
    def format_title(cls, template, **kwargs):
        """Formate un titre de template avec les variables"""
        return template['title'].format(**kwargs)

    @classmethod
    def format_link(cls, template, **kwargs):
        """Formate un lien de template avec les variables"""
        if template.get('link'):
            return template['link'].format(**kwargs)
        return None