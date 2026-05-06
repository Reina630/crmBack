"""
Modèle Document - Gestion des devis, offres et contrats
"""
from app.models.user import db
from datetime import datetime
import os


class Document(db.Model):
    """Document attaché à un dossier"""

    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)

    # Informations de base
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False, index=True)  # devis, offre, contrat, autre

    # Relation avec le dossier
    dossier_id = db.Column(db.Integer, db.ForeignKey('dossiers.id'), nullable=False, index=True)

    # Métadonnées du fichier
    file_path = db.Column(db.String(500), nullable=True)  # Chemin relatif du fichier
    file_size = db.Column(db.Integer, nullable=True)  # Taille en octets
    mime_type = db.Column(db.String(100), nullable=True)  # Type MIME

    # Traçabilité
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Métadonnées
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relations
    dossier_ref = db.relationship('Dossier', back_populates='documents')
    uploader = db.relationship('User', backref='uploaded_documents')

    def __repr__(self):
        return f'<Document {self.id}: {self.name} ({self.type})>'

    def to_dict(self):
        """Convertit le document en dictionnaire"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'dossier_id': self.dossier_id,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'uploaded_by': self.uploaded_by,
            'uploader_name': self.uploader.username if self.uploader else None,
            'uploaded_at': self.uploaded_at.isoformat(),
            'is_active': self.is_active,
            'url': self.get_url()
        }

    def get_url(self):
        """Retourne l'URL d'accès au document"""
        if self.file_path:
            # Pour un serveur de fichiers, retourner l'URL appropriée
            return f"/api/documents/{self.id}/download"
        return None

    def get_file_extension(self):
        """Retourne l'extension du fichier"""
        if self.name:
            return os.path.splitext(self.name)[1].lower()
        return ''

    def is_pdf(self):
        """Vérifie si le document est un PDF"""
        return self.get_file_extension() == '.pdf'

    def is_image(self):
        """Vérifie si le document est une image"""
        ext = self.get_file_extension()
        return ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']

    def is_office_document(self):
        """Vérifie si le document est un document Office"""
        ext = self.get_file_extension()
        return ext in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']

    @staticmethod
    def create_document(name, type, dossier_id, uploaded_by, file_path=None, file_size=None, mime_type=None):
        """Crée un nouveau document"""
        document = Document(
            name=name,
            type=type,
            dossier_id=dossier_id,
            uploaded_by=uploaded_by,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type
        )

        db.session.add(document)
        db.session.commit()

        # Ajouter une action au dossier
        from app.models.dossier import DossierAction
        DossierAction.create_action(
            dossier_id=dossier_id,
            action_type='modification',
            description=f'Document ajouté: {name}',
            user_id=uploaded_by
        )

        return document

    def delete_file(self):
        """Supprime le fichier physique"""
        if self.file_path:
            try:
                full_path = os.path.join(os.getcwd(), self.file_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
            except Exception as e:
                print(f"Erreur lors de la suppression du fichier {self.file_path}: {e}")

    def soft_delete(self):
        """Suppression logique du document"""
        self.is_active = False
        db.session.commit()

    def hard_delete(self):
        """Suppression physique du document"""
        self.delete_file()
        db.session.delete(self)
        db.session.commit()


class DocumentTemplate(db.Model):
    """Modèles de documents prédéfinis"""

    __tablename__ = 'document_templates'

    id = db.Column(db.Integer, primary_key=True)

    # Informations de base
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    type = db.Column(db.String(50), nullable=False)  # devis, offre, contrat, autre

    # Template
    template_path = db.Column(db.String(500), nullable=True)  # Chemin du fichier template
    variables = db.Column(db.JSON, nullable=True)  # Variables disponibles dans le template

    # Métadonnées
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relations
    creator = db.relationship('User', backref='created_templates')

    def __repr__(self):
        return f'<DocumentTemplate {self.id}: {self.name}>'

    def to_dict(self):
        """Convertit le template en dictionnaire"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'template_path': self.template_path,
            'variables': self.variables,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }

    @staticmethod
    def create_template(name, type, created_by, **kwargs):
        """Crée un nouveau template"""
        template = DocumentTemplate(
            name=name,
            type=type,
            created_by=created_by,
            **kwargs
        )
        db.session.add(template)
        db.session.commit()
        return template