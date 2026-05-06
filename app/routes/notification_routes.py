"""
Routes pour la gestion des notifications
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.notification import Notification
from app.models.user import db, User
from datetime import datetime

notification_bp = Blueprint('notifications', __name__)


@notification_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """
    Récupère toutes les notifications de l'utilisateur connecté
    ---
    tags:
      - Notifications
    security:
      - Bearer: []
    parameters:
      - name: unread_only
        in: query
        type: boolean
        default: false
    responses:
      200:
        description: Liste des notifications
      401:
        description: Non autorisé
    """
    user_id = get_jwt_identity()
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    query = Notification.query.filter_by(user_id=user_id)
    
    if unread_only:
        query = query.filter_by(read=False)
    
    notifications = query.order_by(Notification.created_at.desc()).all()
    
    return jsonify([n.to_dict() for n in notifications]), 200


@notification_bp.route('/notifications/unread', methods=['GET'])
@jwt_required()
def get_unread_notifications():
    """
    Récupère uniquement les notifications non lues
    ---
    tags:
      - Notifications
    security:
      - Bearer: []
    responses:
      200:
        description: Liste des notifications non lues
    """
    user_id = get_jwt_identity()
    
    notifications = Notification.query.filter_by(
        user_id=user_id,
        read=False
    ).order_by(Notification.created_at.desc()).all()
    
    return jsonify([n.to_dict() for n in notifications]), 200


@notification_bp.route('/notifications/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_as_read(notification_id):
    """
    Marque une notification comme lue
    ---
    tags:
      - Notifications
    security:
      - Bearer: []
    parameters:
      - name: notification_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Notification marquée comme lue
      404:
        description: Notification non trouvée
    """
    user_id = get_jwt_identity()
    
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=user_id
    ).first_or_404()
    
    notification.read = True
    db.session.commit()
    
    return jsonify({'message': 'Notification marquée comme lue'}), 200


@notification_bp.route('/notifications/read-all', methods=['PUT'])
@jwt_required()
def mark_all_as_read():
    """
    Marque toutes les notifications de l'utilisateur comme lues
    ---
    tags:
      - Notifications
    security:
      - Bearer: []
    responses:
      200:
        description: Toutes les notifications marquées comme lues
    """
    user_id = get_jwt_identity()
    
    Notification.query.filter_by(
        user_id=user_id,
        read=False
    ).update({'read': True})
    
    db.session.commit()
    
    return jsonify({'message': 'Toutes les notifications ont été marquées comme lues'}), 200


@notification_bp.route('/notifications/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """
    Supprime une notification
    ---
    tags:
      - Notifications
    security:
      - Bearer: []
    parameters:
      - name: notification_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Notification supprimée
      404:
        description: Notification non trouvée
    """
    user_id = get_jwt_identity()
    
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=user_id
    ).first_or_404()
    
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'message': 'Notification supprimée'}), 200
