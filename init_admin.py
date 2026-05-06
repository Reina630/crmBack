"""
Script pour initialiser la base de données avec un utilisateur administrateur par défaut
"""

from app import app
from app.models.user import User, db

def init_admin():
    """Crée un utilisateur admin par défaut s'il n'existe pas déjà"""
    with app.app_context():
        # Vérifier si un admin existe déjà
        admin_exists = User.query.filter_by(role='admin').first()
        
        if not admin_exists:
            # Créer l'admin par défaut
            admin = User(
                username='admin',
                email='admin@imanagence.com',
                role='admin'
            )
            admin.set_password('1234')  # Mot de passe temporaire à changer
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Utilisateur admin créé avec succès!")
            print("📧 Email: admin@imanagence.com")
            print("🔑 Username: admin")
            print("🔒 Password: 1234")
            #print("⚠️  Changez ce mot de passe dès la première connexion!")
        else:
            print("ℹ️  Un utilisateur admin existe déjà")

if __name__ == '__main__':
    init_admin()