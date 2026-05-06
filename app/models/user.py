from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.lead import db

# Définition des rôles selon le cahier des charges Iman Sales
class UserRole:
    DC = 'dc'       # Directrice Commerciale - Vue totale, supervision
    DG = 'dg'       # Directeur Général - Validation, consultation
    RI = 'ri'       # Responsable Institution - Clients institutions/ONG
    RCM = 'rcm'     # Responsable Commercial Business - Prospection PME
    ADMIN = 'admin' # Administrateur système
    AGENT = 'agent' # Agent IA (pour les appels API automatisés)
    
    @classmethod
    def all_roles(cls):
        return [cls.DC, cls.DG, cls.RI, cls.RCM, cls.ADMIN, cls.AGENT]
    
    @classmethod
    def commercial_roles(cls):
        """Rôles qui font de la prospection/vente"""
        return [cls.DC, cls.RI, cls.RCM]
    
    @classmethod
    def management_roles(cls):
        """Rôles de direction/supervision"""
        return [cls.DC, cls.DG, cls.ADMIN]
    
    @classmethod
    def get_role_name(cls, role):
        """Retourne le nom complet du rôle"""
        names = {
            cls.DC: 'Directrice Commerciale',
            cls.DG: 'Directeur Général',
            cls.RI: 'Responsable Institution',
            cls.RCM: 'Responsable Commercial Business',
            cls.ADMIN: 'Administrateur',
            cls.AGENT: 'Agent IA'
        }
        return names.get(role, role)
    
    @classmethod
    def get_permissions(cls, role):
        """Retourne les permissions pour un rôle donné"""
        permissions = {
            cls.ADMIN: [
                'admin', 'manage_users', 'view_all', 'edit_all', 'delete_all',
                'view_dashboard_full', 'view_prospection', 'view_validations',
                'validate_dossiers', 'manage_services', 'view_reports', 'export_data'
            ],
            cls.DG: [
                'view_dashboard_summary', 'view_all', 'view_validations',
                'validate_dossiers', 'view_reports', 'export_data'
            ],
            cls.DC: [
                'view_dashboard_full', 'view_all', 'edit_all', 'view_prospection',
                'view_validations', 'reassign_dossiers', 'view_reports', 'export_data',
                'manage_team'
            ],
            cls.RI: [
                'view_dashboard_summary', 'view_own', 'edit_own', 'view_prospection',
                'create_dossiers', 'view_clients_institutions', 'view_reports'
            ],
            cls.RCM: [
                'view_dashboard_summary', 'view_own', 'edit_own', 'view_prospection',
                'create_dossiers', 'create_prospects', 'view_clients_pme', 'view_reports'
            ],
            cls.AGENT: [
                'create_pending_leads', 'create_conversations', 'create_appointments'
            ]
        }
        return permissions.get(role, [])


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=UserRole.RCM)  # dc, dg, ri, rcm, admin, agent
    first_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def set_password(self, password):
        """Hash et stocker le mot de passe"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Vérifier le mot de passe"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Retourne le nom complet de l'utilisateur"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    @property
    def role_name(self):
        """Retourne le nom complet du rôle"""
        return UserRole.get_role_name(self.role)
    
    @property
    def permissions(self):
        """Retourne la liste des permissions de l'utilisateur"""
        return UserRole.get_permissions(self.role)
    
    def has_permission(self, permission):
        """Vérifie si l'utilisateur a une permission spécifique"""
        return permission in self.permissions
    
    def is_commercial(self):
        """Vérifie si l'utilisateur est un commercial"""
        return self.role in UserRole.commercial_roles()
    
    def is_manager(self):
        """Vérifie si l'utilisateur a un rôle de direction"""
        return self.role in UserRole.management_roles()

    def to_dict(self):
        """Convertir en dictionnaire (sans le hash du password)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'role_name': self.role_name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'permissions': self.permissions,
            'is_active': self.is_active,
            'is_commercial': self.is_commercial(),
            'is_manager': self.is_manager(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }