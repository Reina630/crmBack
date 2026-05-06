"""
Routes pour la gestion des validations
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.models import db, Validation, Dossier, User, Notification
from app.utils.decorators import admin_required

validation_bp = Blueprint('validation', __name__, url_prefix='/api/validations')


@validation_bp.route('', methods=['OPTIONS'])
@validation_bp.route('/', methods=['OPTIONS'])
def validations_options():
    """Handle CORS preflight for validations"""
    return '', 204


@validation_bp.route('', methods=['GET'], strict_slashes=False)
@validation_bp.route('/', methods=['GET'])
@jwt_required()
def get_validations():
    """
    Récupérer toutes les validations
    Filtrables par statut
    """
    status = request.args.get('status')
    
    query = Validation.query
    
    if status:
        query = query.filter_by(status=status)
    
    validations = query.order_by(
        Validation.priority.desc(),
        Validation.submitted_at.desc()
    ).all()
    
    return jsonify([v.to_dict() for v in validations])


@validation_bp.route('/<int:validation_id>', methods=['GET'])
@jwt_required()
def get_validation(validation_id):
    """Récupérer une validation par ID"""
    validation = Validation.query.get_or_404(validation_id)
    return jsonify(validation.to_dict())


@validation_bp.route('', methods=['POST'], strict_slashes=False)
@validation_bp.route('/', methods=['POST'])
@jwt_required()
def create_validation():
    """
    Créer une demande de validation pour un dossier
    """
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    dossier_id = data.get('dossier_id')
    if not dossier_id:
        return jsonify({'error': 'dossier_id requis'}), 400
    
    # Vérifier que le dossier existe
    dossier = Dossier.query.get_or_404(dossier_id)
    
    # Vérifier qu'il n'y a pas déjà une validation en attente
    existing = Validation.query.filter_by(
        dossier_id=dossier_id,
        status='en_attente'
    ).first()
    
    if existing:
        return jsonify({'error': 'Une validation est déjà en attente pour ce dossier'}), 400
    
    # Récupérer les infos du responsable
    responsible = User.query.get(dossier.responsible_id) if dossier.responsible_id else None
    responsible_name = responsible.username if responsible else 'Non assigné'
    
    # Récupérer le nom du client
    client_name = 'N/A'
    if dossier.client_id:
        from app.models.client import Client
        client = Client.query.get(dossier.client_id)
        if client:
            client_name = client.name
    elif dossier.prospect_id:
        from app.models.prospect import Prospect
        prospect = Prospect.query.get(dossier.prospect_id)
        if prospect and prospect.lead:
            client_name = prospect.lead.name
    
    # Créer la validation
    validation = Validation(
        dossier_id=dossier_id,
        dossier_reference=dossier.reference,
        client_name=client_name,
        responsible_name=responsible_name,
        amount=dossier.estimated_amount or 0,
        priority=data.get('priority', 'normale')
    )
    
    db.session.add(validation)
    
    # Créer une notification pour les admins/DC
    admins = User.query.filter_by(role='admin').all()
    for admin in admins:
        notification = Notification(
            user_id=admin.id,
            type='validation',
            title='Nouvelle demande de validation',
            message=f"Le dossier {dossier.reference} pour {client_name} nécessite votre validation ({validation.amount}€)",
            link=f'/validations/{validation.id}'
        )
        db.session.add(notification)
    
    db.session.commit()
    
    return jsonify(validation.to_dict()), 201


@validation_bp.route('/<int:validation_id>/approve', methods=['PATCH'])
@jwt_required()
@admin_required
def approve_validation(validation_id):
    """
    Approuver une validation
    """
    current_user_id = get_jwt_identity()
    data = request.get_json() or {}
    
    validation = Validation.query.get_or_404(validation_id)
    
    if validation.status != 'en_attente':
        return jsonify({'error': 'Cette validation a déjà été traitée'}), 400
    
    validation.status = 'valide'
    validation.decided_at = datetime.utcnow()
    validation.decided_by = current_user_id
    validation.comment = data.get('comment', '')
    
    # Mettre à jour le statut du dossier
    dossier = validation.dossier_ref
    if dossier:
        dossier.validation_status = 'approved'
    
    # Notifier le responsable du dossier
    if dossier and dossier.responsible_id:
        notification = Notification(
            user_id=dossier.responsible_id,
            type='validation',
            title='Devis validé',
            message=f"Votre devis pour {validation.client_name} a été approuvé",
            link=f'/dossiers/{dossier.id}'
        )
        db.session.add(notification)
    
    db.session.commit()
    
    return jsonify(validation.to_dict())


@validation_bp.route('/<int:validation_id>/reject', methods=['PATCH'])
@jwt_required()
@admin_required
def reject_validation(validation_id):
    """
    Rejeter une validation
    """
    current_user_id = get_jwt_identity()
    data = request.get_json() or {}
    
    validation = Validation.query.get_or_404(validation_id)
    
    if validation.status != 'en_attente':
        return jsonify({'error': 'Cette validation a déjà été traitée'}), 400
    
    comment = data.get('comment')
    if not comment:
        return jsonify({'error': 'Un commentaire est requis pour le rejet'}), 400
    
    validation.status = 'rejete'
    validation.decided_at = datetime.utcnow()
    validation.decided_by = current_user_id
    validation.comment = comment
    
    # Mettre à jour le statut du dossier
    dossier = validation.dossier_ref
    if dossier:
        dossier.validation_status = 'rejected'
    
    # Notifier le responsable du dossier
    if dossier and dossier.responsible_id:
        notification = Notification(
            user_id=dossier.responsible_id,
            type='validation',
            title='Devis rejeté',
            message=f"Votre devis pour {validation.client_name} a été rejeté. Raison: {comment}",
            link=f'/dossiers/{dossier.id}'
        )
        db.session.add(notification)
    
    db.session.commit()
    
    return jsonify(validation.to_dict())


@validation_bp.route('/stats', methods=['GET'])
@jwt_required()
@admin_required
def get_validation_stats():
    """
    Statistiques sur les validations
    """
    total = Validation.query.count()
    en_attente = Validation.query.filter_by(status='en_attente').count()
    valide = Validation.query.filter_by(status='valide').count()
    rejete = Validation.query.filter_by(status='rejete').count()
    
    return jsonify({
        'total': total,
        'en_attente': en_attente,
        'valide': valide,
        'rejete': rejete
    })
