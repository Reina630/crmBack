from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime
from app.models import db, Prospect, Lead, Client
from app.schemas.prospect_schema import ProspectSchema

prospect_bp = Blueprint('prospect', __name__, url_prefix='/api/prospects')

prospect_schema = ProspectSchema()
prospects_schema = ProspectSchema(many=True)

@prospect_bp.route('/', methods=['GET'])
@jwt_required()
def get_prospects():
    """
    Récupérer tous les prospects
    ---
    tags:
      - Prospects
    security:
      - Bearer: []
    responses:
      200:
        description: Liste des prospects
    """
    prospects = Prospect.query.all()
    return jsonify([p.to_dict() for p in prospects])

@prospect_bp.route('/<int:prospect_id>', methods=['GET'])
@jwt_required()
def get_prospect(prospect_id):
    """
    Récupérer un prospect par ID
    ---
    tags:
      - Prospects
    security:
      - Bearer: []
    parameters:
      - name: prospect_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Détails du prospect
      404:
        description: Prospect non trouvé
    """
    prospect = Prospect.query.get_or_404(prospect_id)
    return jsonify(prospect.to_dict())

@prospect_bp.route('/', methods=['POST'])
@jwt_required()
def create_prospect():
    """
    Créer un nouveau prospect
    ---
    tags:
      - Prospects
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            lead_id:
              type: integer
              required: true
            notes:
              type: string
    responses:
      201:
        description: Prospect créé
      400:
        description: Lead déjà qualifié
      404:
        description: Lead non trouvé
    """
    data = request.get_json()
    lead_id = data.get('lead_id')
    notes = data.get('notes')
    lead = Lead.query.get_or_404(lead_id)
    # Vérifier qu'il n'est pas déjà prospect
    if Prospect.query.filter_by(lead_id=lead_id).first():
        return jsonify({'error': 'Ce lead est déjà qualifié en prospect.'}), 400
    prospect = Prospect(lead_id=lead_id, notes=notes)
    db.session.add(prospect)
    db.session.commit()
    return jsonify(prospect.to_dict()), 201

@prospect_bp.route('/<int:prospect_id>', methods=['PUT'])
@jwt_required()
def update_prospect(prospect_id):
    """
    Mettre à jour un prospect
    ---
    tags:
      - Prospects
    security:
      - Bearer: []
    parameters:
      - name: prospect_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            notes:
              type: string
    responses:
      200:
        description: Prospect mis à jour
      404:
        description: Prospect non trouvé
    """
    prospect = Prospect.query.get_or_404(prospect_id)
    data = request.get_json()
    prospect.notes = data.get('notes', prospect.notes)
    db.session.commit()
    return jsonify(prospect.to_dict())

@prospect_bp.route('/<int:prospect_id>', methods=['DELETE'])
@jwt_required()
def delete_prospect(prospect_id):
    """
    Supprimer un prospect
    ---
    tags:
      - Prospects
    security:
      - Bearer: []
    parameters:
      - name: prospect_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Prospect supprimé
      404:
        description: Prospect non trouvé
    """
    prospect = Prospect.query.get_or_404(prospect_id)
    db.session.delete(prospect)
    db.session.commit()
    return jsonify({'message': 'Prospect supprimé.'})

@prospect_bp.route('/<int:prospect_id>/status', methods=['PATCH'])
@jwt_required()
def update_prospect_status(prospect_id):
    """
    Mettre à jour le statut d'un prospect et créer automatiquement un client si converti
    ---
    tags:
      - Prospects
    security:
      - Bearer: []
    parameters:
      - name: prospect_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            status:
              type: string
              enum: [en_cours, converti, perdu]
              required: true
    responses:
      200:
        description: Statut mis à jour (et client créé si converti)
      400:
        description: Statut invalide
      404:
        description: Prospect non trouvé
    """
    prospect = Prospect.query.get_or_404(prospect_id)
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['en_cours', 'converti', 'perdu']:
        return jsonify({'error': 'Statut invalide'}), 400
    
    prospect.status = new_status
    
    # Si le prospect est converti, créer automatiquement un client
    if new_status == 'converti' and not prospect.client_id:
        lead = prospect.lead
        
        # Créer le client avec les données du lead
        client = Client(
            name=lead.company or lead.name,
            type='entreprise' if lead.company else 'particulier',
            contact_name=lead.name,
            email=lead.email,
            phone=lead.phone,
            sector=lead.sector,
            company_size=lead.company_size,
            is_active=True
        )
        
        db.session.add(client)
        db.session.flush()  # Pour obtenir l'ID du client
        
        prospect.client_id = client.id
        prospect.converted_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'prospect': prospect.to_dict(),
        'client_created': prospect.client_id is not None and new_status == 'converti'
    })


