from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models.user import User, UserRole

def admin_required(f):
    """Décorateur qui vérifie que l'utilisateur connecté est un admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({'message': 'Utilisateur non trouvé ou inactif'}), 404
            
        if user.role != UserRole.ADMIN:
            return jsonify({'message': 'Accès refusé. Droits administrateur requis.'}), 403
            
        return f(*args, **kwargs)
    return decorated_function


def permission_required(permission):
    """Décorateur qui vérifie que l'utilisateur a une permission spécifique"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user_id = int(get_jwt_identity())
            user = User.query.get(current_user_id)
            
            if not user or not user.is_active:
                return jsonify({'message': 'Utilisateur non trouvé ou inactif'}), 404
                
            if not user.has_permission(permission):
                return jsonify({'message': f'Accès refusé. Permission "{permission}" requise.'}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def roles_required(*roles):
    """Décorateur qui vérifie que l'utilisateur a l'un des rôles spécifiés"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user_id = int(get_jwt_identity())
            user = User.query.get(current_user_id)
            
            if not user or not user.is_active:
                return jsonify({'message': 'Utilisateur non trouvé ou inactif'}), 404
                
            if user.role not in roles:
                role_names = [UserRole.get_role_name(r) for r in roles]
                return jsonify({
                    'message': f'Accès refusé. Rôles autorisés: {", ".join(role_names)}'
                }), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def management_required(f):
    """Décorateur qui vérifie que l'utilisateur est DC, DG ou Admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({'message': 'Utilisateur non trouvé ou inactif'}), 404
            
        if not user.is_manager():
            return jsonify({'message': 'Accès refusé. Rôle de direction requis.'}), 403
            
        return f(*args, **kwargs)
    return decorated_function


def commercial_required(f):
    """Décorateur qui vérifie que l'utilisateur est un commercial (DC, RI, RCM)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({'message': 'Utilisateur non trouvé ou inactif'}), 404
            
        if not user.is_commercial():
            return jsonify({'message': 'Accès refusé. Rôle commercial requis.'}), 403
            
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Récupère l'utilisateur courant depuis le token JWT"""
    current_user_id = int(get_jwt_identity())
    return User.query.get(current_user_id)