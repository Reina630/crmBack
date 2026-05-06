from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
from datetime import datetime
from app.models import db, Dossier, Prospect, Client, User
from app.models.opportunity_line import OpportunityLine
import random
import string

dossier_bp = Blueprint('dossier', __name__, url_prefix='/api/dossiers')

def generate_reference():
    """Génère une référence unique pour l'opportunité"""
    year = datetime.now().year
    random_part = ''.join(random.choices(string.digits, k=4))
    return f"OPP-{year}-{random_part}"

@dossier_bp.route('', methods=['OPTIONS'])
@dossier_bp.route('/', methods=['OPTIONS'])
def dossiers_options():
    """Handle CORS preflight for dossiers"""
    return '', 204

@dossier_bp.route('', methods=['GET'], strict_slashes=False)
@dossier_bp.route('/', methods=['GET'])
@jwt_required()
def get_dossiers():
    """
    Récupérer toutes les opportunités
    ---
    tags:
      - Opportunités
    security:
      - Bearer: []
    parameters:
      - name: status
        in: query
        type: string
        required: false
      - name: prospect_id
        in: query
        type: integer
        required: false
      - name: client_id
        in: query
        type: integer
        required: false
    responses:
      200:
        description: Liste des opportunités
    """
    query = Dossier.query
    
    status = request.args.get('status')
    prospect_id = request.args.get('prospect_id')
    client_id = request.args.get('client_id')
    
    if status:
        query = query.filter_by(status=status)
    if prospect_id:
        query = query.filter_by(prospect_id=int(prospect_id))
    if client_id:
        query = query.filter_by(client_id=int(client_id))
    
    dossiers = query.order_by(Dossier.created_at.desc()).all()
    return jsonify([d.to_dict() for d in dossiers])

@dossier_bp.route('/<int:dossier_id>', methods=['GET'])
@jwt_required()
def get_dossier(dossier_id):
    """
    Récupérer une opportunité par ID
    ---
    tags:
      - Opportunités
    security:
      - Bearer: []
    parameters:
      - name: dossier_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Détails de l'opportunité
      404:
        description: Opportunité non trouvée
    """
    dossier = Dossier.query.get_or_404(dossier_id)
    return jsonify(dossier.to_dict(include_actions=True, include_documents=True))

@dossier_bp.route('/', methods=['POST'])
@jwt_required()
def create_dossier():
    """
    Créer une nouvelle opportunité
    ---
    tags:
      - Opportunités
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - title
            - estimated_amount
          properties:
            prospect_id:
              type: integer
            client_id:
              type: integer
            title:
              type: string
            description:
              type: string
            estimated_amount:
              type: number
            priority:
              type: string
              enum: [normale, haute, urgente]
            origin:
              type: string
    responses:
      201:
        description: Opportunité créée
      400:
        description: Données invalides
    """
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    # Vérifier qu'on a soit prospect_id soit client_id
    prospect_id = data.get('prospect_id')
    client_id = data.get('client_id')
    
    if not prospect_id and not client_id:
        return jsonify({'error': 'prospect_id ou client_id requis'}), 400
    
    # Générer une référence unique
    reference = generate_reference()
    while Dossier.query.filter_by(reference=reference).first():
        reference = generate_reference()
    
    dossier = Dossier(
        reference=reference,
        prospect_id=prospect_id,
        client_id=client_id,
        responsible_id=int(current_user_id),
        title=data.get('title'),
        description=data.get('description'),
        estimated_amount=data.get('estimated_amount'),
        priority=data.get('priority', 'normale'),
        origin=data.get('origin', 'prospection'),
        status='proposition'
    )
    
    db.session.add(dossier)
    db.session.commit()
    
    return jsonify(dossier.to_dict()), 201

@dossier_bp.route('/<int:dossier_id>/status', methods=['PATCH', 'PUT'])
@jwt_required()
def update_dossier_status(dossier_id):
    """
    Mettre à jour le statut d'une opportunité
    Quand statut = 'gagnee', convertir le prospect en client si nécessaire
    ---
    tags:
      - Opportunités
    security:
      - Bearer: []
    parameters:
      - name: dossier_id
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
              enum: [proposition, gagnee, perdue, en_cours, terminee, annulee]
    responses:
      200:
        description: Statut mis à jour
      404:
        description: Opportunité non trouvée
    """
    dossier = Dossier.query.get_or_404(dossier_id)
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['proposition', 'gagnee', 'perdue', 'en_cours', 'terminee', 'annulee']:
        return jsonify({'error': 'Statut invalide'}), 400
    
    old_status = dossier.status
    dossier.status = new_status
    dossier.updated_at = datetime.utcnow()
    
    # Si l'opportunité est gagnée et liée à un prospect, convertir en client
    client_created = False
    if new_status == 'gagnee' and dossier.prospect_id and not dossier.client_id:
        prospect = dossier.prospect_data
        lead = prospect.lead
        
        # Créer le client
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
        db.session.flush()
        
        # Lier le client à l'opportunité
        dossier.client_id = client.id
        
        # Mettre à jour le prospect
        prospect.status = 'converti'
        prospect.client_id = client.id
        prospect.converted_at = datetime.utcnow()
        
        client_created = True
    
    db.session.commit()
    
    return jsonify({
        'dossier': dossier.to_dict(),
        'client_created': client_created,
        'status_changed': old_status != new_status
    })

@dossier_bp.route('/<int:dossier_id>', methods=['PUT'])
@jwt_required()
def update_dossier(dossier_id):
    """
    Mettre à jour une opportunité
    ---
    tags:
      - Opportunités
    security:
      - Bearer: []
    parameters:
      - name: dossier_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        schema:
          type: object
    responses:
      200:
        description: Opportunité mise à jour
    """
    dossier = Dossier.query.get_or_404(dossier_id)
    data = request.get_json()
    
    if 'title' in data:
        dossier.title = data['title']
    if 'description' in data:
        dossier.description = data['description']
    if 'estimated_amount' in data:
        dossier.estimated_amount = data['estimated_amount']
    if 'priority' in data:
        dossier.priority = data['priority']
    
    # Gérer le changement de statut avec conversion automatique
    client_created = False
    if 'status' in data:
        new_status = data['status']
        old_status = dossier.status
        dossier.status = new_status
        
        # Si l'opportunité est gagnée et liée à un prospect, convertir en client
        if new_status == 'gagnee' and dossier.prospect_id and not dossier.client_id:
            prospect = dossier.prospect_data
            lead = prospect.lead
            
            # Créer le client
            client = Client(
                name=lead.company or lead.name,
                type='entreprise' if lead.company else 'particulier',
                contact_name=lead.name,
                email=lead.email,
                phone=lead.phone,
                sector=lead.sector,
                company_size=lead.company_size,
                responsible_id=dossier.responsible_id,
                is_active=True
            )
            
            db.session.add(client)
            db.session.flush()
            
            # Lier le client à l'opportunité
            dossier.client_id = client.id
            
            # Mettre à jour le prospect
            prospect.status = 'converti'
            prospect.client_id = client.id
            prospect.converted_at = datetime.utcnow()
            
            client_created = True
    
    dossier.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    response_data = dossier.to_dict()
    if client_created:
        response_data['client_created'] = True
        response_data['client_id'] = dossier.client_id
    
    return jsonify(response_data)

@dossier_bp.route('/<int:dossier_id>', methods=['DELETE'])
@jwt_required()
def delete_dossier(dossier_id):
    """
    Supprimer une opportunité (soft delete)
    ---
    tags:
      - Opportunités
    security:
      - Bearer: []
    parameters:
      - name: dossier_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Opportunité désactivée
    """
    dossier = Dossier.query.get_or_404(dossier_id)
    dossier.is_active = False
    dossier.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'message': 'Opportunité désactivée avec succès'})

# Routes pour les lignes de prestations

@dossier_bp.route('/<int:dossier_id>/lines', methods=['GET'])
@jwt_required()
def get_opportunity_lines(dossier_id):
    """
    Récupérer les lignes de prestations d'une opportunité
    ---
    tags:
      - Opportunités
    security:
      - Bearer: []
    parameters:
      - name: dossier_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Liste des lignes
    """
    dossier = Dossier.query.get_or_404(dossier_id)
    lines = OpportunityLine.query.filter_by(opportunity_id=dossier_id).order_by(OpportunityLine.order_index).all()
    return jsonify([line.to_dict() for line in lines])

@dossier_bp.route('/<int:dossier_id>/lines', methods=['POST'])
@jwt_required()
def create_opportunity_line(dossier_id):
    """
    Ajouter une ligne de prestation
    ---
    tags:
      - Opportunités
    security:
      - Bearer: []
    parameters:
      - name: dossier_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - category
            - designation
            - quantity
            - unit_price
            - duration
          properties:
            category:
              type: string
            designation:
              type: string
            quantity:
              type: integer
            unit_price:
              type: number
            duration:
              type: integer
            order_index:
              type: integer
    responses:
      201:
        description: Ligne créée
    """
    dossier = Dossier.query.get_or_404(dossier_id)
    data = request.get_json()
    
    # Support camelCase et snake_case
    unit_price = data.get('unit_price') or data.get('unitPrice', 0)
    
    # Calculer le total
    total = OpportunityLine.calculate_total(
        data.get('quantity', 1),
        unit_price,
        data.get('duration', 1)
    )
    
    line = OpportunityLine(
        opportunity_id=dossier_id,
        category=data.get('category'),
        designation=data.get('designation', ''),
        quantity=data.get('quantity', 1),
        unit_price=unit_price,
        duration=data.get('duration', 1),
        total=total,
        order_index=data.get('order_index', 0)
    )
    
    db.session.add(line)
    
    # Mettre à jour le montant estimé de l'opportunité
    update_opportunity_total(dossier_id)
    
    db.session.commit()
    
    return jsonify(line.to_dict()), 201

@dossier_bp.route('/<int:dossier_id>/lines/<int:line_id>', methods=['PUT'])
@jwt_required()
def update_opportunity_line(dossier_id, line_id):
    """
    Mettre à jour une ligne de prestation
    ---
    tags:
      - Opportunités
    security:
      - Bearer: []
    """
    line = OpportunityLine.query.filter_by(id=line_id, opportunity_id=dossier_id).first_or_404()
    data = request.get_json()
    
    if 'category' in data:
        line.category = data['category']
    if 'designation' in data:
        line.designation = data['designation']
    if 'quantity' in data:
        line.quantity = data['quantity']
    # Support camelCase et snake_case
    if 'unit_price' in data or 'unitPrice' in data:
        line.unit_price = data.get('unit_price') or data.get('unitPrice')
    if 'duration' in data:
        line.duration = data['duration']
    if 'order_index' in data:
        line.order_index = data['order_index']
    
    # Recalculer le total
    line.total = OpportunityLine.calculate_total(line.quantity, line.unit_price, line.duration)
    line.updated_at = datetime.utcnow()
    
    # Mettre à jour le montant estimé de l'opportunité
    update_opportunity_total(dossier_id)
    
    db.session.commit()
    
    return jsonify(line.to_dict())

@dossier_bp.route('/<int:dossier_id>/lines/<int:line_id>', methods=['DELETE'])
@jwt_required()
def delete_opportunity_line(dossier_id, line_id):
    """
    Supprimer une ligne de prestation
    ---
    tags:
      - Opportunités
    security:
      - Bearer: []
    """
    line = OpportunityLine.query.filter_by(id=line_id, opportunity_id=dossier_id).first_or_404()
    
    db.session.delete(line)
    
    # Mettre à jour le montant estimé de l'opportunité
    update_opportunity_total(dossier_id)
    
    db.session.commit()
    
    return jsonify({'message': 'Ligne supprimée avec succès'})

@dossier_bp.route('/<int:dossier_id>/lines/bulk', methods=['POST'])
@jwt_required()
def bulk_create_opportunity_lines(dossier_id):
    """
    Créer plusieurs lignes en une fois
    ---
    tags:
      - Opportunités
    security:
      - Bearer: []
    parameters:
      - name: dossier_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            lines:
              type: array
              items:
                type: object
    responses:
      201:
        description: Lignes créées
    """
    dossier = Dossier.query.get_or_404(dossier_id)
    data = request.get_json()
    lines_data = data.get('lines', [])
    
    # Supprimer les anciennes lignes
    OpportunityLine.query.filter_by(opportunity_id=dossier_id).delete()
    
    # Créer les nouvelles lignes
    created_lines = []
    for idx, line_data in enumerate(lines_data):
        # Support camelCase (frontend) et snake_case (backend)
        unit_price = line_data.get('unit_price') or line_data.get('unitPrice', 0)
        
        total = OpportunityLine.calculate_total(
            line_data.get('quantity', 1),
            unit_price,
            line_data.get('duration', 1)
        )
        
        line = OpportunityLine(
            opportunity_id=dossier_id,
            category=line_data.get('category'),
            designation=line_data.get('designation', ''),
            quantity=line_data.get('quantity', 1),
            unit_price=unit_price,
            duration=line_data.get('duration', 1),
            total=total,
            order_index=idx
        )
        
        db.session.add(line)
        created_lines.append(line)
    
    # Mettre à jour le montant estimé de l'opportunité
    update_opportunity_total(dossier_id)
    
    db.session.commit()
    
    return jsonify([line.to_dict() for line in created_lines]), 201

def update_opportunity_total(dossier_id):
    """Fonction helper pour mettre à jour le montant total de l'opportunité"""
    lines = OpportunityLine.query.filter_by(opportunity_id=dossier_id).all()
    total = sum(line.total for line in lines)
    
    dossier = Dossier.query.get(dossier_id)
    if dossier:
        dossier.estimated_amount = total
        dossier.updated_at = datetime.utcnow()


# Routes pour la gestion de projet

@dossier_bp.route('/<int:dossier_id>/start-project', methods=['POST'])
@jwt_required()
def start_project(dossier_id):
    """
    Démarrer un projet (passer l'opportunité en mode projet)
    ---
    tags:
      - Projets
    """
    dossier = Dossier.query.get_or_404(dossier_id)
    
    data = request.get_json()
    
    dossier.status = 'en_cours'
    dossier.start_date = datetime.utcnow()
    dossier.expected_end_date = datetime.fromisoformat(data.get('expected_end_date')) if data.get('expected_end_date') else None
    dossier.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify(dossier.to_dict())


@dossier_bp.route('/<int:dossier_id>/lines/<int:line_id>/status', methods=['PUT'])
@jwt_required()
def update_line_status(dossier_id, line_id):
    """
    Mettre à jour le statut d'une ligne/tâche
    ---
    tags:
      - Projets
    """
    line = OpportunityLine.query.filter_by(
        id=line_id,
        opportunity_id=dossier_id
    ).first_or_404()
    
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['a_faire', 'en_production', 'terminee']:
        return jsonify({'error': 'Statut invalide'}), 400
    
    line.status = new_status
    line.production_notes = data.get('production_notes', line.production_notes)
    
    if new_status == 'terminee' and not line.completed_at:
        line.completed_at = datetime.utcnow()
    elif new_status != 'terminee':
        line.completed_at = None
    
    line.updated_at = datetime.utcnow()
    
    # Mettre à jour le pourcentage de progression du projet
    dossier = Dossier.query.get(dossier_id)
    dossier.update_progress()
    
    db.session.commit()
    
    return jsonify({
        'line': line.to_dict(),
        'project_progress': dossier.progress_percentage
    })


@dossier_bp.route('/<int:dossier_id>/complete', methods=['POST'])
@jwt_required()
def complete_project(dossier_id):
    """
    Terminer un projet
    ---
    tags:
      - Projets
    """
    dossier = Dossier.query.get_or_404(dossier_id)
    
    dossier.status = 'terminee'
    dossier.actual_end_date = datetime.utcnow()
    dossier.progress_percentage = 100
    dossier.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify(dossier.to_dict())

