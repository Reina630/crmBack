"""
Routes pour consulter les logs d'actions (historique d'audit)
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.action_log import db, ActionLog
from app.models.user import User
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from flasgger import swag_from

action_log_bp = Blueprint('action_logs', __name__)


@action_log_bp.route('/action-logs', methods=['GET'])
@jwt_required()
def get_action_logs():
    """
    Récupère l'historique des actions
    ---
    tags:
      - Action Logs
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: query
        type: integer
        description: Filtrer par utilisateur
      - name: entity_type
        in: query
        type: string
        description: Filtrer par type d'entité (lead, service, user, pending_lead)
      - name: entity_id
        in: query
        type: integer
        description: Filtrer par ID d'entité spécifique
      - name: action_type
        in: query
        type: string
        description: Filtrer par type d'action (created, updated, deleted, validated, rejected)
      - name: start_date
        in: query
        type: string
        format: date
        description: Date de début (YYYY-MM-DD)
      - name: end_date
        in: query
        type: string
        format: date
        description: Date de fin (YYYY-MM-DD)
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 50
    responses:
      200:
        description: Liste des logs
      401:
        description: Non autorisé
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Seuls admin, manager et dc peuvent voir tous les logs
    if current_user.role not in ['admin', 'manager', 'dc']:
        return jsonify({'message': 'Accès refusé'}), 403
    
    # Paramètres de filtrage
    user_id = request.args.get('user_id', type=int)
    entity_type = request.args.get('entity_type')
    entity_id = request.args.get('entity_id', type=int)
    action_type = request.args.get('action_type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Requête de base avec joinedload pour charger la relation user
    query = ActionLog.query.options(joinedload(ActionLog.user))
    
    # Filtres
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    
    if entity_id:
        query = query.filter_by(entity_id=entity_id)
    
    if action_type:
        query = query.filter_by(action_type=action_type)
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(ActionLog.timestamp >= start_dt)
        except ValueError:
            return jsonify({'message': 'Format de date invalide pour start_date'}), 400
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(ActionLog.timestamp < end_dt)
        except ValueError:
            return jsonify({'message': 'Format de date invalide pour end_date'}), 400
    
    # Tri par date décroissante
    query = query.order_by(ActionLog.timestamp.desc())
    
    # Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'logs': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@action_log_bp.route('/action-logs/stats', methods=['GET'])
@jwt_required()
def get_action_stats():
    """
    Statistiques sur les actions
    ---
    tags:
      - Action Logs
    security:
      - Bearer: []
    parameters:
      - name: days
        in: query
        type: integer
        default: 7
        description: Nombre de jours à analyser
    responses:
      200:
        description: Statistiques
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if current_user.role not in ['admin', 'manager', 'dc']:
        return jsonify({'message': 'Accès refusé'}), 403
    
    days = request.args.get('days', 7, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Stats par type d'action
    from sqlalchemy import func
    
    action_counts = db.session.query(
        ActionLog.action_type,
        func.count(ActionLog.id)
    ).filter(
        ActionLog.timestamp >= start_date
    ).group_by(ActionLog.action_type).all()
    
    # Stats par entité
    entity_counts = db.session.query(
        ActionLog.entity_type,
        func.count(ActionLog.id)
    ).filter(
        ActionLog.timestamp >= start_date
    ).group_by(ActionLog.entity_type).all()
    
    # Utilisateurs les plus actifs
    user_activity = db.session.query(
        ActionLog.user_id,
        User.username,
        func.count(ActionLog.id).label('count')
    ).join(User).filter(
        ActionLog.timestamp >= start_date
    ).group_by(ActionLog.user_id, User.username).order_by(func.count(ActionLog.id).desc()).limit(10).all()
    
    return jsonify({
        'period_days': days,
        'actions_by_type': {action: count for action, count in action_counts},
        'actions_by_entity': {entity: count for entity, count in entity_counts},
        'top_users': [
            {'user_id': user_id, 'username': username, 'actions': count}
            for user_id, username, count in user_activity
        ]
    })


@action_log_bp.route('/action-logs/entity/<string:entity_type>/<int:entity_id>', methods=['GET'])
@jwt_required()
def get_entity_history(entity_type, entity_id):
    """
    Récupère l'historique complet d'une entité spécifique
    ---
    tags:
      - Action Logs
    security:
      - Bearer: []
    parameters:
      - name: entity_type
        in: path
        type: string
        required: true
      - name: entity_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Historique de l'entité
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if current_user.role not in ['admin', 'manager', 'user']:
        return jsonify({'message': 'Accès refusé'}), 403
    
    logs = ActionLog.query.filter_by(
        entity_type=entity_type,
        entity_id=entity_id
    ).order_by(ActionLog.timestamp.asc()).all()
    
    return jsonify({
        'entity_type': entity_type,
        'entity_id': entity_id,
        'history': [log.to_dict() for log in logs]
    })
