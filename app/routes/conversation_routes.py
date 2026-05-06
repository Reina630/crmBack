from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.conversation import Conversation, db
from app.models.user import User
from app.utils.decorators import admin_required
from datetime import datetime, timedelta

conversation_bp = Blueprint('conversation_bp', __name__)


@conversation_bp.route('/conversations', methods=['POST'])
def create_conversation():
    """
    Crée une nouvelle conversation (public pour l'IA)
    ---
    tags:
      - Conversations
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - conversation_id
          properties:
            conversation_id:
              type: string
            ip_address:
              type: string
            user_agent:
              type: string
    responses:
      201:
        description: Conversation créée
    """
    data = request.json
    
    if not data or not data.get('conversation_id'):
        return jsonify({'message': 'conversation_id requis'}), 400
    
    # Vérifier si la conversation existe déjà
    existing = Conversation.query.filter_by(conversation_id=data['conversation_id']).first()
    if existing:
        return jsonify(existing.to_dict()), 200
    
    conversation = Conversation.create_conversation(
        conversation_id=data['conversation_id'],
        ip_address=data.get('ip_address'),
        user_agent=data.get('user_agent')
    )
    
    return jsonify(conversation.to_dict()), 201


@conversation_bp.route('/conversations/<conversation_id>/message', methods=['POST'])
def add_message(conversation_id):
    """
    Ajoute un message à une conversation (public pour l'IA)
    ---
    tags:
      - Conversations
    parameters:
      - name: conversation_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - role
            - content
          properties:
            role:
              type: string
              enum: [user, assistant]
            content:
              type: string
    responses:
      200:
        description: Message ajouté
      404:
        description: Conversation non trouvée
    """
    data = request.json
    
    if not data or not data.get('role') or not data.get('content'):
        return jsonify({'message': 'role et content requis'}), 400
    
    conversation = Conversation.query.filter_by(conversation_id=conversation_id).first()
    if not conversation:
        return jsonify({'message': 'Conversation non trouvée'}), 404
    
    conversation.add_message(data['role'], data['content'])
    
    return jsonify({'message': 'Message ajouté', 'conversation': conversation.to_dict()})


@conversation_bp.route('/conversations/<conversation_id>/complete', methods=['PUT'])
def complete_conversation(conversation_id):
    """
    Marque une conversation comme terminée (public pour l'IA)
    ---
    tags:
      - Conversations
    parameters:
      - name: conversation_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        schema:
          type: object
          properties:
            lead_data:
              type: object
            score:
              type: number
            pending_lead_id:
              type: integer
    responses:
      200:
        description: Conversation terminée
      404:
        description: Conversation non trouvée
    """
    data = request.json or {}
    
    conversation = Conversation.query.filter_by(conversation_id=conversation_id).first()
    if not conversation:
        return jsonify({'message': 'Conversation non trouvée'}), 404
    
    conversation.complete(
        lead_data=data.get('lead_data'),
        score=data.get('score'),
        pending_lead_id=data.get('pending_lead_id')
    )
    
    return jsonify({'message': 'Conversation terminée', 'conversation': conversation.to_dict()})


@conversation_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    """
    Récupère la liste des conversations
    ---
    tags:
      - Conversations
    security:
      - Bearer: []
    parameters:
      - name: status
        in: query
        type: string
        enum: [active, completed, abandoned, all]
        default: all
      - name: start_date
        in: query
        type: string
        format: date
      - name: end_date
        in: query
        type: string
        format: date
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 20
    responses:
      200:
        description: Liste des conversations
    """
    status = request.args.get('status', 'all')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Conversation.query
    
    # Filtres
    if status != 'all':
        query = query.filter_by(status=status)
    
    if start_date:
        query = query.filter(Conversation.started_at >= datetime.fromisoformat(start_date))
    
    if end_date:
        query = query.filter(Conversation.started_at <= datetime.fromisoformat(end_date))
    
    # Tri par date décroissante
    query = query.order_by(Conversation.started_at.desc())
    
    # Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'conversations': [conv.to_dict() for conv in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@conversation_bp.route('/conversations/<int:id>', methods=['GET'])
@jwt_required()
def get_conversation(id):
    """
    Récupère une conversation spécifique
    ---
    tags:
      - Conversations
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Détails de la conversation
      404:
        description: Conversation non trouvée
    """
    conversation = Conversation.query.get_or_404(id)
    return jsonify(conversation.to_dict())


@conversation_bp.route('/conversations/by-conversation-id/<conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation_by_id(conversation_id):
    """
    Récupère une conversation par son conversation_id
    ---
    tags:
      - Conversations
    security:
      - Bearer: []
    parameters:
      - name: conversation_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Détails de la conversation
      404:
        description: Conversation non trouvée
    """
    conversation = Conversation.query.filter_by(conversation_id=conversation_id).first_or_404()
    return jsonify(conversation.to_dict())


@conversation_bp.route('/conversations/stats', methods=['GET'])
@jwt_required()
def get_conversation_stats():
    """
    Statistiques sur les conversations
    ---
    tags:
      - Conversations
    security:
      - Bearer: []
    parameters:
      - name: days
        in: query
        type: integer
        default: 30
    responses:
      200:
        description: Statistiques des conversations
    """
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)
    
    total = Conversation.query.filter(Conversation.started_at >= since).count()
    completed = Conversation.query.filter(
        Conversation.started_at >= since,
        Conversation.status == 'completed'
    ).count()
    abandoned = Conversation.query.filter(
        Conversation.started_at >= since,
        Conversation.status == 'abandoned'
    ).count()
    active = Conversation.query.filter(
        Conversation.started_at >= since,
        Conversation.status == 'active'
    ).count()
    
    # Durée moyenne
    avg_duration = db.session.query(db.func.avg(Conversation.duration)).filter(
        Conversation.started_at >= since,
        Conversation.duration.isnot(None)
    ).scalar() or 0
    
    # Score moyen
    avg_score = db.session.query(db.func.avg(Conversation.score)).filter(
        Conversation.started_at >= since,
        Conversation.score.isnot(None)
    ).scalar() or 0
    
    # Messages moyens par conversation
    avg_messages = db.session.query(db.func.avg(Conversation.message_count)).filter(
        Conversation.started_at >= since
    ).scalar() or 0
    
    # Taux de conversion
    conversion_rate = (completed / total * 100) if total > 0 else 0
    
    return jsonify({
        'total_conversations': total,
        'completed': completed,
        'abandoned': abandoned,
        'active': active,
        'avg_duration': round(avg_duration, 2),
        'avg_score': round(avg_score, 3),
        'avg_messages': round(avg_messages, 1),
        'conversion_rate': round(conversion_rate, 2)
    })


@conversation_bp.route('/conversations/<int:id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_conversation(id):
    """
    Supprime une conversation (Admin uniquement)
    ---
    tags:
      - Administration
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Conversation supprimée
      404:
        description: Conversation non trouvée
    """
    conversation = Conversation.query.get_or_404(id)
    db.session.delete(conversation)
    db.session.commit()
    
    return jsonify({'message': 'Conversation supprimée avec succès'})
