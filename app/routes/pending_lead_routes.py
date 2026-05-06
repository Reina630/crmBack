"""
Routes pour la gestion des leads en attente de validation
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.lead import db, Lead
from app.models.pending_lead import PendingLead
from app.models.user import User
from app.models.action_log import ActionLog
from app.models.notification import Notification
from datetime import datetime
from flasgger import swag_from

pending_lead_bp = Blueprint('pending_leads', __name__)


def is_authorized_validator(user):
    """Vérifie si l'utilisateur peut valider des leads"""
    # Tous les rôles peuvent voir et valider les leads IA
    return user.role in ['admin', 'manager', 'user', 'commercial', 'dc', 'dg']


@pending_lead_bp.route('/pending-leads', methods=['GET'])
@jwt_required()
def get_pending_leads():
    """
    Récupère la liste des leads en attente de validation
    ---
    tags:
      - Pending Leads
    security:
      - Bearer: []
    parameters:
      - name: status
        in: query
        type: string
        enum: [pending, validated, rejected, all]
        default: pending
      - name: min_score
        in: query
        type: number
        description: Score minimum (0-1)
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 10
    responses:
      200:
        description: Liste des pending leads
      401:
        description: Non autorisé
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    print(f"User ID: {user_id}, User: {user.username if user else 'None'}, Role: {user.role if user else 'None'}")
    
    if not is_authorized_validator(user):
        print(f"Access denied for role: {user.role}")
        return jsonify({'message': 'Accès refusé - Rôle non autorisé'}), 403
    
    # Paramètres de filtrage
    status = request.args.get('status', 'pending')
    min_score = request.args.get('min_score', type=float)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Requête de base
    query = PendingLead.query
    
    # Filtres
    if status != 'all':
        query = query.filter_by(status=status)
    
    if min_score is not None:
        query = query.filter(PendingLead.score >= min_score)
    
    # Tri par score décroissant et date
    query = query.order_by(PendingLead.score.desc(), PendingLead.created_at.desc())
    
    # Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'pending_leads': [pl.to_dict() for pl in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@pending_lead_bp.route('/pending-leads/<int:id>', methods=['GET'])
@jwt_required()
def get_pending_lead(id):
    """
    Récupère un pending lead spécifique
    ---
    tags:
      - Pending Leads
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Détails du pending lead
      404:
        description: Pending lead non trouvé
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not is_authorized_validator(user):
        return jsonify({'message': 'Accès refusé'}), 403
    
    pending_lead = PendingLead.query.get_or_404(id)
    return jsonify(pending_lead.to_dict())


@pending_lead_bp.route('/pending-leads', methods=['POST'])
@jwt_required()
def create_pending_lead():
    """
    Crée un nouveau pending lead (utilisé par l'IA)
    ---
    tags:
      - Pending Leads
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - conversation_id
            - data
          properties:
            conversation_id:
              type: string
            data:
              type: object
            score:
              type: number
            urgency:
              type: string
    responses:
      201:
        description: Pending lead créé
      400:
        description: Données invalides
    """
    data = request.json
    
    if not data.get('conversation_id') or not data.get('data'):
        return jsonify({'message': 'conversation_id et data requis'}), 400
    
    # Vérifier que les champs essentiels sont présents dans data
    lead_data = data.get('data', {})
    required_fields = ['nom', 'email', 'telephone']
    missing = [f for f in required_fields if not lead_data.get(f)]
    if missing:
        return jsonify({'message': f'Champs manquants dans data: {", ".join(missing)}'}), 400
    
    pending_lead = PendingLead(
        conversation_id=data['conversation_id'],
        data=lead_data,
        score=data.get('score', 0.5),
        urgency=data.get('urgency', 'moyenne'),
        status='pending'
    )
    
    db.session.add(pending_lead)
    db.session.commit()
    
    # Créer une notification pour la directrice commerciale (DC)
    dc_users = User.query.filter_by(role='dc').all()
    
    for dc in dc_users:
        notification = Notification(
            user_id=dc.id,
            type='validation',
            title='Nouveau lead en attente de validation',
            message=f"Un nouveau lead de {lead_data.get('nom', 'Inconnu')} ({lead_data.get('company', 'N/A')}) a été créé par l'Agent IA et nécessite votre validation.",
            link=f'/leads/pending',
            data={
                'pending_lead_id': pending_lead.id,
                'score': pending_lead.score,
                'urgency': pending_lead.urgency
            }
        )
        db.session.add(notification)
    
    db.session.commit()
    
    return jsonify(pending_lead.to_dict()), 201


@pending_lead_bp.route('/pending-leads/<int:id>/validate', methods=['POST', 'PUT'])
@jwt_required()
def validate_pending_lead(id):
    """
    Valide un pending lead et crée un vrai lead
    ---
    tags:
      - Pending Leads
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        schema:
          type: object
          properties:
            notes:
              type: string
            assigned_to_id:
              type: integer
              description: ID du commercial à assigner
            modifications:
              type: object
              description: Modifications à apporter aux données avant création
    responses:
      200:
        description: Lead validé et créé
      404:
        description: Pending lead non trouvé
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not is_authorized_validator(user):
        return jsonify({'message': 'Accès refusé'}), 403
    
    pending_lead = PendingLead.query.get_or_404(id)
    
    if pending_lead.status != 'pending':
        return jsonify({'message': f'Ce lead a déjà été {pending_lead.status}'}), 400
    
    data = request.json or {}
    modifications = data.get('modifications', {})
    assigned_to_id = data.get('assigned_to_id')
    
    # Vérifier que le commercial existe si assigné
    if assigned_to_id:
        assigned_user = User.query.get(assigned_to_id)
        if not assigned_user:
            return jsonify({'message': 'Commercial non trouvé'}), 404
    
    # Fusionner les données originales avec les modifications
    lead_data = {**pending_lead.data, **modifications}
    
    # Validation : au moins nom OU email OU téléphone
    name = lead_data.get('nom', '').strip()
    email = lead_data.get('email', '').strip()
    phone = lead_data.get('telephone', '').strip()
    
    if not name or name == 'Non renseigné':
        return jsonify({
            'message': 'Nom manquant. Impossible de créer le lead.',
            'error': 'name_required'
        }), 400
    
    # Nettoyer l'email s'il est invalide
    if not email or email == 'Non renseigné' or '@' not in email:
        email = None
    
    # Créer le vrai lead
    lead = Lead(
        name=name,
        email=email,
        phone=phone if phone and phone != 'Non renseigné' else None,
        company=lead_data.get('company') if lead_data.get('company') != 'Non renseigné' else None,
        job_title=lead_data.get('besoin'),  # Besoin exprimé → job_title
        source='Agent IA',  # Source automatique pour les leads IA
        status='nouveau',
        score=pending_lead.score,
        urgency=pending_lead.urgency,
        service_id=lead_data.get('service_id'),  # Si mappé
        assigned_to_id=assigned_to_id  # Affectation du commercial
    )
    
    db.session.add(lead)
    db.session.flush()  # Pour obtenir l'ID du lead
    
    # Mettre à jour le pending lead
    pending_lead.status = 'validated'
    pending_lead.validated_by = user_id
    pending_lead.validated_at = datetime.utcnow()
    pending_lead.validation_notes = data.get('notes')
    pending_lead.lead_id = lead.id
    
    db.session.commit()
    
    # Log de l'action
    try:
        ActionLog.log_action(
            user_id=user_id,
            action_type='validated',
            entity_type='pending_lead',
            entity_id=pending_lead.id,
            changes={
                'before': {'status': 'pending'},
                'after': {'status': 'validated', 'lead_id': lead.id}
            },
            description=f"Pending lead validé -> Lead '{lead.name}' créé",
            ip_address=request.remote_addr
        )
    except Exception as e:
        print(f"Erreur log action: {str(e)}")
    
    return jsonify({
        'message': 'Lead validé avec succès',
        'pending_lead': pending_lead.to_dict()
    })


@pending_lead_bp.route('/pending-leads/<int:id>/reject', methods=['POST', 'PUT'])
@jwt_required()
def reject_pending_lead(id):
    """
    Rejette un pending lead
    ---
    tags:
      - Pending Leads
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        schema:
          type: object
          properties:
            notes:
              type: string
              description: Raison du rejet
    responses:
      200:
        description: Lead rejeté
      404:
        description: Pending lead non trouvé
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not is_authorized_validator(user):
        return jsonify({'message': 'Accès refusé'}), 403
    
    pending_lead = PendingLead.query.get_or_404(id)
    
    if pending_lead.status != 'pending':
        return jsonify({'message': f'Ce lead a déjà été {pending_lead.status}'}), 400
    
    data = request.json or {}
    
    pending_lead.status = 'rejected'
    pending_lead.validated_by = user_id
    pending_lead.validated_at = datetime.utcnow()
    pending_lead.validation_notes = data.get('notes', 'Rejeté')
    
    db.session.commit()
    
    # Log de l'action
    ActionLog.log_action(
        user_id=user_id,
        action_type='rejected',
        entity_type='pending_lead',
        entity_id=pending_lead.id,
        changes={
            'before': {'status': 'pending'},
            'after': {'status': 'rejected', 'notes': pending_lead.validation_notes}
        },
        description=f"Pending lead rejeté: {pending_lead.data.get('nom', 'N/A')}",
        ip_address=request.remote_addr
    )
    
    return jsonify({
        'message': 'Lead rejeté',
        'pending_lead': pending_lead.to_dict()
    })


@pending_lead_bp.route('/pending-leads/<int:id>', methods=['PUT'])
@jwt_required()
def update_pending_lead(id):
    """
    Met à jour les données d'un pending lead
    ---
    tags:
      - Pending Leads
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        schema:
          type: object
          properties:
            data:
              type: object
            score:
              type: number
            urgency:
              type: string
    responses:
      200:
        description: Pending lead mis à jour
      404:
        description: Pending lead non trouvé
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not is_authorized_validator(user):
        return jsonify({'message': 'Accès refusé'}), 403
    
    pending_lead = PendingLead.query.get_or_404(id)
    
    if pending_lead.status != 'pending':
        return jsonify({'message': 'Seuls les leads pending peuvent être modifiés'}), 400
    
    data = request.json
    
    # Capturer l'état avant modification
    before_state = pending_lead.to_dict()
    
    if 'data' in data:
        pending_lead.data = {**pending_lead.data, **data['data']}
    if 'score' in data:
        pending_lead.score = data['score']
    if 'urgency' in data:
        pending_lead.urgency = data['urgency']
    
    db.session.commit()
    
    # Log de l'action
    ActionLog.log_action(
        user_id=user_id,
        action_type='updated',
        entity_type='pending_lead',
        entity_id=pending_lead.id,
        changes={'before': before_state, 'after': pending_lead.to_dict()},
        description=f"Pending lead modifié: {pending_lead.data.get('nom', 'N/A')}",
        ip_address=request.remote_addr
    )
    
    return jsonify(pending_lead.to_dict())


@pending_lead_bp.route('/pending-leads/stats', methods=['GET'])
@jwt_required()
def get_pending_stats():
    """
    Statistiques sur les pending leads
    ---
    tags:
      - Pending Leads
    security:
      - Bearer: []
    responses:
      200:
        description: Statistiques
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not is_authorized_validator(user):
        return jsonify({'message': 'Accès refusé'}), 403
    
    total_pending = PendingLead.query.filter_by(status='pending').count()
    total_validated = PendingLead.query.filter_by(status='validated').count()
    total_rejected = PendingLead.query.filter_by(status='rejected').count()
    
    # Leads à haute priorité (score > 0.7)
    high_priority = PendingLead.query.filter(
        PendingLead.status == 'pending',
        PendingLead.score > 0.7
    ).count()
    
    return jsonify({
        'total_pending': total_pending,
        'total_validated': total_validated,
        'total_rejected': total_rejected,
        'high_priority': high_priority
    })


@pending_lead_bp.route('/salespeople', methods=['GET'])
@jwt_required()
def get_salespeople():
    """
    Récupère la liste des commerciaux disponibles pour affectation
    ---
    tags:
      - Pending Leads
    security:
      - Bearer: []
    responses:
      200:
        description: Liste des commerciaux
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not is_authorized_validator(user):
        return jsonify({'message': 'Accès refusé'}), 403
    
    # Récupérer tous les users sauf les agents
    salespeople = User.query.filter(User.role.in_(['admin', 'manager', 'user'])).all()
    
    return jsonify({
        'salespeople': [
            {
                'id': u.id,
                'username': u.username,
                'role': u.role
            } for u in salespeople
        ]
    })
