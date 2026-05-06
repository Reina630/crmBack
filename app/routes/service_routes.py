from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.service import Service, db
from app.models.action_log import ActionLog
from app.utils.decorators import admin_required
from sqlalchemy.exc import IntegrityError

service_bp = Blueprint('service_bp', __name__)

@service_bp.route('/services', methods=['GET'])
@jwt_required()
def get_services():
    """
    Récupère tous les services
    ---
    tags:
      - Services
    security:
      - Bearer: []
    parameters:
      - name: active_only
        in: query
        type: boolean
        description: Récupérer seulement les services actifs
    responses:
      200:
        description: Liste des services
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              name:
                type: string
              description:
                type: string
              price_range:
                type: string
              is_active:
                type: boolean
              lead_count:
                type: integer
    """
    active_only = request.args.get('active_only', 'false').lower() == 'true'
    
    if active_only:
        services = Service.query.filter_by(is_active=True).all()
    else:
        services = Service.query.all()
    
    return jsonify([service.to_dict() for service in services]), 200

@service_bp.route('/services/<int:service_id>', methods=['GET'])
@jwt_required()
def get_service(service_id):
    """
    Récupère un service spécifique
    ---
    tags:
      - Services
    security:
      - Bearer: []
    parameters:
      - name: service_id
        in: path
        type: integer
        required: true
        description: ID du service
    responses:
      200:
        description: Détails du service
      404:
        description: Service non trouvé
    """
    service = Service.query.get_or_404(service_id)
    return jsonify(service.to_dict()), 200

@service_bp.route('/services', methods=['POST'])
@jwt_required()
@admin_required
def create_service():
    """
    Créer un nouveau service (Admin uniquement)
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
            - name
          properties:
            name:
              type: string
              description: Nom du service
              example: "Développement Web"
            description:
              type: string
              description: Description du service
              example: "Création de sites web sur mesure"
            price_range:
              type: string
              description: Fourchette de prix
              example: "5000-15000€"
            is_active:
              type: boolean
              description: Service actif
              default: true
    responses:
      201:
        description: Service créé avec succès
      400:
        description: Données invalides ou service déjà existant
      403:
        description: Accès refusé - Droits admin requis
    """
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'message': 'Le nom du service est requis'}), 400
    
    try:
        service = Service(
            name=data['name'],
            description=data.get('description'),
            price_range=data.get('price_range'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(service)
        db.session.commit()
        
        # Log de l'action
        ActionLog.log_action(
            user_id=get_jwt_identity(),
            action_type='created',
            entity_type='service',
            entity_id=service.id,
            changes={'after': service.to_dict()},
            description=f"Service '{service.name}' créé",
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'message': 'Service créé avec succès',
            'service': service.to_dict()
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Un service avec ce nom existe déjà'}), 400

@service_bp.route('/services/<int:service_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_service(service_id):
    """
    Mettre à jour un service (Admin uniquement)
    ---
    tags:
      - Administration
    security:
      - Bearer: []
    parameters:
      - name: service_id
        in: path
        type: integer
        required: true
        description: ID du service
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            description:
              type: string
            price_range:
              type: string
            is_active:
              type: boolean
    responses:
      200:
        description: Service mis à jour
      404:
        description: Service non trouvé
      403:
        description: Accès refusé - Droits admin requis
    """
    service = Service.query.get_or_404(service_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'Aucune donnée fournie'}), 400
    
    try:
        # Capturer l'état avant modification
        before_state = service.to_dict()
        
        service.name = data.get('name', service.name)
        service.description = data.get('description', service.description)
        service.price_range = data.get('price_range', service.price_range)
        service.is_active = data.get('is_active', service.is_active)
        
        db.session.commit()
        
        # Log de l'action
        ActionLog.log_action(
            user_id=get_jwt_identity(),
            action_type='updated',
            entity_type='service',
            entity_id=service.id,
            changes={'before': before_state, 'after': service.to_dict()},
            description=f"Service '{service.name}' mis à jour",
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'message': 'Service mis à jour avec succès',
            'service': service.to_dict()
        }), 200
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Un service avec ce nom existe déjà'}), 400

@service_bp.route('/services/<int:service_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_service(service_id):
    """
    Supprimer un service (Admin uniquement)
    ---
    tags:
      - Administration
    security:
      - Bearer: []
    parameters:
      - name: service_id
        in: path
        type: integer
        required: true
        description: ID du service à supprimer
    responses:
      200:
        description: Service supprimé
      400:
        description: Service lié à des leads existants
      404:
        description: Service non trouvé
      403:
        description: Accès refusé - Droits admin requis
    """
    service = Service.query.get_or_404(service_id)
    
    # Vérifier si le service a des leads associés
    if len(service.leads) > 0:
        return jsonify({
            'message': f'Impossible de supprimer le service. {len(service.leads)} lead(s) y sont associé(s).'
        }), 400
    
    # Capturer les données avant suppression
    service_data = service.to_dict()
    service_name = service.name
    
    db.session.delete(service)
    db.session.commit()
    
    # Log de l'action
    ActionLog.log_action(
        user_id=get_jwt_identity(),
        action_type='deleted',
        entity_type='service',
        entity_id=service_id,
        changes={'before': service_data},
        description=f"Service '{service_name}' supprimé",
        ip_address=request.remote_addr
    )
    
    return jsonify({'message': 'Service supprimé avec succès'}), 200