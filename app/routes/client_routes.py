from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.models import db, Client, User
from app.schemas.client_schema import ClientSchema

client_bp = Blueprint('client', __name__, url_prefix='/api/clients')

client_schema = ClientSchema()
clients_schema = ClientSchema(many=True)

@client_bp.route('/', methods=['GET'])
@jwt_required()
def get_clients():
    """
    Récupérer tous les clients
    ---
    tags:
      - Clients
    security:
      - Bearer: []
    parameters:
      - name: is_active
        in: query
        type: boolean
        required: false
        description: Filtrer par statut actif/inactif
    responses:
      200:
        description: Liste des clients
    """
    is_active = request.args.get('is_active')
    
    query = Client.query
    
    if is_active is not None:
        is_active_bool = is_active.lower() == 'true'
        query = query.filter_by(is_active=is_active_bool)
    
    clients = query.order_by(Client.created_at.desc()).all()
    return jsonify([c.to_dict() for c in clients])

@client_bp.route('/<int:client_id>', methods=['GET'])
@jwt_required()
def get_client(client_id):
    """
    Récupérer un client par ID
    ---
    tags:
      - Clients
    security:
      - Bearer: []
    parameters:
      - name: client_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Détails du client
      404:
        description: Client non trouvé
    """
    client = Client.query.get_or_404(client_id)
    return jsonify(client.to_dict())

@client_bp.route('/', methods=['POST'])
@jwt_required()
def create_client():
    """
    Créer un nouveau client
    ---
    tags:
      - Clients
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
            - type
          properties:
            name:
              type: string
            type:
              type: string
              enum: [entreprise, particulier, institution, pme, grande_entreprise]
            contact_name:
              type: string
            email:
              type: string
            phone:
              type: string
            address:
              type: string
            responsible_id:
              type: integer
            sector:
              type: string
            company_size:
              type: string
    responses:
      201:
        description: Client créé
      400:
        description: Données invalides
    """
    data = request.get_json()
    
    client = Client(
        name=data.get('name'),
        type=data.get('type'),
        contact_name=data.get('contact_name'),
        email=data.get('email'),
        phone=data.get('phone'),
        address=data.get('address'),
        responsible_id=data.get('responsible_id'),
        sector=data.get('sector'),
        company_size=data.get('company_size'),
        is_active=True
    )
    
    db.session.add(client)
    db.session.commit()
    
    return jsonify(client.to_dict()), 201

@client_bp.route('/<int:client_id>', methods=['PUT'])
@jwt_required()
def update_client(client_id):
    """
    Mettre à jour un client
    ---
    tags:
      - Clients
    security:
      - Bearer: []
    parameters:
      - name: client_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            type:
              type: string
            contact_name:
              type: string
            email:
              type: string
            phone:
              type: string
            address:
              type: string
            responsible_id:
              type: integer
            sector:
              type: string
            company_size:
              type: string
            is_active:
              type: boolean
    responses:
      200:
        description: Client mis à jour
      404:
        description: Client non trouvé
    """
    client = Client.query.get_or_404(client_id)
    data = request.get_json()
    
    # Mettre à jour les champs
    if 'name' in data:
        client.name = data['name']
    if 'type' in data:
        client.type = data['type']
    if 'contact_name' in data:
        client.contact_name = data['contact_name']
    if 'email' in data:
        client.email = data['email']
    if 'phone' in data:
        client.phone = data['phone']
    if 'address' in data:
        client.address = data['address']
    if 'responsible_id' in data:
        client.responsible_id = data['responsible_id']
    if 'sector' in data:
        client.sector = data['sector']
    if 'company_size' in data:
        client.company_size = data['company_size']
    if 'is_active' in data:
        client.is_active = data['is_active']
    
    client.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify(client.to_dict())

@client_bp.route('/<int:client_id>', methods=['DELETE'])
@jwt_required()
def delete_client(client_id):
    """
    Supprimer un client (soft delete - marque comme inactif)
    ---
    tags:
      - Clients
    security:
      - Bearer: []
    parameters:
      - name: client_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Client désactivé
      404:
        description: Client non trouvé
    """
    client = Client.query.get_or_404(client_id)
    client.is_active = False
    client.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'message': 'Client désactivé avec succès'})

@client_bp.route('/<int:client_id>/stats', methods=['GET'])
@jwt_required()
def get_client_stats(client_id):
    """
    Récupérer les statistiques d'un client
    ---
    tags:
      - Clients
    security:
      - Bearer: []
    parameters:
      - name: client_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Statistiques du client
      404:
        description: Client non trouvé
    """
    client = Client.query.get_or_404(client_id)
    
    # Mettre à jour les revenus
    client.update_revenue()
    
    stats = {
        'client': client.to_dict(),
        'dossiers': {
            'total': client.dossiers_count,
            'active': len([d for d in client.dossiers if d.status not in ['gagne', 'perdu', 'abandonne']]),
            'won': len([d for d in client.dossiers if d.status == 'gagne']),
            'lost': len([d for d in client.dossiers if d.status == 'perdu']),
        },
        'revenue': {
            'total': client.total_revenue,
            'average_per_dossier': client.total_revenue / client.dossiers_count if client.dossiers_count > 0 else 0
        }
    }
    
    return jsonify(stats)
