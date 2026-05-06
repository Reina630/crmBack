"""
Script d'initialisation des utilisateurs pour Iman Sales
Crée les utilisateurs de base avec les rôles définis dans le cahier des charges
"""
import os
import sys

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from app.models.user import User, UserRole


def create_users():
    """Créer les utilisateurs par défaut"""
    
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@iman.ne',
            'password': '1234',
            'role': UserRole.ADMIN,
            'first_name': 'Admin',
            'last_name': 'Système'
        },
        {
            'username': 'dc',
            'email': 'dc@iman.ne',
            'password': '1234',
            'role': UserRole.DC,
            'first_name': 'Fatima',
            'last_name': 'Directrice Commerciale'
        },
        {
            'username': 'dg',
            'email': 'dg@iman.ne',
            'password': '1234',
            'role': UserRole.DG,
            'first_name': 'Mohamed',
            'last_name': 'Directeur Général'
        },
        {
            'username': 'ri',
            'email': 'ri@iman.ne',
            'password': '1234',
            'role': UserRole.RI,
            'first_name': 'Aïcha',
            'last_name': 'Resp. Institutions'
        },
        {
            'username': 'rcm',
            'email': 'rcm@iman.ne',
            'password': '1234',
            'role': UserRole.RCM,
            'first_name': 'Ibrahim',
            'last_name': 'Resp. Commercial PME'
        }
       
    ]
    
    created_count = 0
    updated_count = 0
    
    for user_data in users_data:
        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter(
            (User.username == user_data['username']) | 
            (User.email == user_data['email'])
        ).first()
        
        if existing_user:
            # Mettre à jour le rôle et les infos si l'utilisateur existe
            existing_user.role = user_data['role']
            existing_user.first_name = user_data['first_name']
            existing_user.last_name = user_data['last_name']
            existing_user.is_active = True
            print(f"✓ Utilisateur '{user_data['username']}' mis à jour avec rôle {user_data['role']}")
            updated_count += 1
        else:
            # Créer le nouvel utilisateur
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                is_active=True
            )
            user.set_password(user_data['password'])
            db.session.add(user)
            print(f"✓ Utilisateur '{user_data['username']}' créé avec rôle {user_data['role']}")
            created_count += 1
    
    db.session.commit()
    
    print("\n" + "="*50)
    print(f"Résumé: {created_count} créé(s), {updated_count} mis à jour")
    print("="*50)
    
    # Afficher les identifiants
    print("\n📋 Identifiants de connexion:")
    print("-"*50)
    for user_data in users_data:
        role_name = UserRole.get_role_name(user_data['role'])
        print(f"  {role_name}:")
        print(f"    Username: {user_data['username']}")
        print(f"    Password: {user_data['password']}")
        print()


def list_users():
    """Lister tous les utilisateurs existants"""
    users = User.query.all()
    
    print("\n📋 Utilisateurs existants:")
    print("-"*70)
    print(f"{'ID':<4} {'Username':<12} {'Email':<25} {'Rôle':<6} {'Nom complet':<20}")
    print("-"*70)
    
    for user in users:
        print(f"{user.id:<4} {user.username:<12} {user.email:<25} {user.role:<6} {user.full_name:<20}")
    
    print("-"*70)
    print(f"Total: {len(users)} utilisateur(s)")


if __name__ == '__main__':
    with app.app_context():
        print("🚀 Initialisation des utilisateurs Iman Sales")
        print("="*50)
        
        # Créer les utilisateurs
        create_users()
        
        # Lister les utilisateurs
        list_users()
        
        print("\n✅ Initialisation terminée!")
