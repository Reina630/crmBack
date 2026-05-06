from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.user import User, db
from app.models.action_log import ActionLog
from app.utils.decorators import admin_required
from sqlalchemy.exc import IntegrityError

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/register', methods=['POST'])
@jwt_required()
@admin_required
def register():
    """
    Créer un nouveau compte utilisateur (Admin uniquement)
    ---
    tags:
      - Administration
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - email
            - password
          properties:
            username:
              type: string
              description: Nom d'utilisateur
              example: "john_doe"
            email:
              type: string
              format: email
              description: Email de l'utilisateur
              example: "john@example.com"
            password:
              type: string
              description: Mot de passe
              example: "motdepasse123"
            role:
              type: string
              description: Rôle de l'utilisateur
              default: "user"
              example: "user"
    responses:
      201:
        description: Utilisateur créé avec succès
        schema:
          type: object
          properties:
            message:
              type: string
            user:
              type: object
              properties:
                id:
                  type: integer
                username:
                  type: string
                email:
                  type: string
                role:
                  type: string
      400:
        description: Données invalides ou utilisateur déjà existant
      403:
        description: Accès refusé - Droits admin requis
    """
    data = request.get_json()
    
    # Validation des données requises
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Username, email et password sont requis'}), 400
    
    try:
        # Créer le nouvel utilisateur
        user = User(
            username=data['username'],
            email=data['email'],
            role=data.get('role', 'user')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Log de l'action
        ActionLog.log_action(
            user_id=get_jwt_identity(),
            action_type='created',
            entity_type='user',
            entity_id=user.id,
            changes={'after': user.to_dict()},
            description=f"Utilisateur '{user.username}' créé avec rôle {user.role}",
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'message': 'Utilisateur créé avec succès',
            'user': user.to_dict()
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Nom d\'utilisateur ou email déjà existant'}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Connexion utilisateur
    ---
    tags:
      - Authentification
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              description: Nom d'utilisateur ou email
              example: "john_doe"
            password:
              type: string
              description: Mot de passe
              example: "motdepasse123"
    responses:
      200:
        description: Connexion réussie
        schema:
          type: object
          properties:
            access_token:
              type: string
              description: Token JWT pour l'authentification
            user:
              type: object
              properties:
                id:
                  type: integer
                username:
                  type: string
                email:
                  type: string
                role:
                  type: string
      401:
        description: Identifiants invalides
    """
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username et password sont requis'}), 400
    
    # Rechercher l'utilisateur par username ou email
    user = User.query.filter(
        (User.username == data['username']) | (User.email == data['username'])
    ).first()
    
    if user and user.check_password(data['password']) and user.is_active:
        # Créer le token JWT avec identity en string explicite
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
    
    return jsonify({'message': 'Identifiants invalides'}), 401

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Récupérer le profil utilisateur connecté
    ---
    tags:
      - Authentification
    security:
      - Bearer: []
    responses:
      200:
        description: Profil utilisateur
        schema:
          type: object
          properties:
            id:
              type: integer
            username:
              type: string
            email:
              type: string
            role:
              type: string
      401:
        description: Token invalide ou expiré
    """
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user or not user.is_active:
        return jsonify({'message': 'Utilisateur non trouvé'}), 404
    
    return jsonify(user.to_dict()), 200

@auth_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_all_users():
    """
    Lister tous les utilisateurs (Admin uniquement)
    ---
    tags:
      - Administration
    security:
      - Bearer: []
    responses:
      200:
        description: Liste des utilisateurs
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              username:
                type: string
              email:
                type: string
              role:
                type: string
              is_active:
                type: boolean
              created_at:
                type: string
      403:
        description: Accès refusé - Droits admin requis
    """
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200

@auth_bp.route('/users/<int:user_id>/toggle', methods=['PUT'])
@jwt_required()
@admin_required
def toggle_user_status(user_id):
    """
    Activer/désactiver un utilisateur (Admin uniquement)
    ---
    tags:
      - Administration
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID de l'utilisateur
    responses:
      200:
        description: Statut utilisateur modifié
        schema:
          type: object
          properties:
            message:
              type: string
            user:
              type: object
      403:
        description: Accès refusé - Droits admin requis
      404:
        description: Utilisateur non trouvé
    """
    user = User.query.get_or_404(user_id)
    
    # Empêcher de désactiver le dernier admin
    if user.role == 'admin' and user.is_active:
        active_admins = User.query.filter_by(role='admin', is_active=True).count()
        if active_admins <= 1:
            return jsonify({'message': 'Impossible de désactiver le dernier administrateur'}), 400
    
    user.is_active = not user.is_active
    db.session.commit()
    
    # Log de l'action
    ActionLog.log_action(
        user_id=get_jwt_identity(),
        action_type='status_changed',
        entity_type='user',
        entity_id=user.id,
        changes={
            'before': {'is_active': not user.is_active},
            'after': {'is_active': user.is_active}
        },
        description=f"Utilisateur '{user.username}' {'activé' if user.is_active else 'désactivé'}",
        ip_address=request.remote_addr
    )
    
    status = 'activé' if user.is_active else 'désactivé'
    return jsonify({
        'message': f'Utilisateur {status} avec succès',
        'user': user.to_dict()
    }), 200