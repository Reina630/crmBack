from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
from app.models.lead import db, Lead
from app.models.action_log import ActionLog
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from datetime import datetime

lead_bp = Blueprint('lead_bp', __name__)

@lead_bp.route('/leads/stats', methods=['OPTIONS'])
@cross_origin()
def leads_stats_options():
    """Handle CORS preflight for leads stats"""
    return jsonify({}), 200

@lead_bp.route('/leads/stats', methods=['GET'])
@cross_origin()
@jwt_required()
def get_leads_stats():
    """
    Récupère les statistiques des leads
    ---
    tags:
      - Leads
    security:
      - Bearer: []
    responses:
      200:
        description: Statistiques des leads
        schema:
          type: object
          properties:
            total:
              type: integer
            nouveau:
              type: integer
            en_cours:
              type: integer
            converti:
              type: integer
            perdu:
              type: integer
            avg_score:
              type: number
            conversion_rate:
              type: number
      500:
        description: Erreur serveur
    """
    try:
        # Total des leads
        total = Lead.query.count()
        
        # Debug: voir tous les statuts présents
        all_statuses = db.session.query(Lead.status, func.count(Lead.id)).group_by(Lead.status).all()
        print(f"📊 Statuts présents dans la DB: {dict(all_statuses)}")
        
        # Compter par statut
        nouveau = Lead.query.filter(
            func.lower(func.trim(Lead.status)).in_(['nouveau', 'new'])
        ).count()
        
        qualifie = Lead.query.filter(
            func.lower(func.trim(Lead.status)).in_(['qualifié', 'qualifie', 'qualified'])
        ).count()
        
        en_cours = Lead.query.filter(
            func.lower(func.replace(func.trim(Lead.status), ' ', '_')).in_(['en_cours'])
        ).count()
        
        converti = Lead.query.filter(
            func.lower(func.trim(Lead.status)).in_(['converti', 'converted'])
        ).count()
        
        perdu = Lead.query.filter(
            func.lower(func.trim(Lead.status)).in_(['perdu', 'lost'])
        ).count()
        
        # Les 4 statuts standards : nouveau, qualifié, converti, perdu
        
        print(f"📊 Comptage: total={total}, nouveau={nouveau}, qualifié={qualifie}, en_cours={en_cours}, converti={converti}, perdu={perdu}")
        
        # Score moyen
        avg_score_result = db.session.query(func.avg(Lead.score)).scalar()
        avg_score = float(avg_score_result) if avg_score_result else 0.0
        
        # Taux de conversion
        conversion_rate = round((converti / total * 100), 2) if total > 0 else 0
        
        return jsonify({
            'total': total,
            'nouveau': nouveau,
            'qualifie': qualifie,
            'en_cours': en_cours,
            'converti': converti,
            'perdu': perdu,
            'avg_score': round(avg_score, 2),
            'conversion_rate': conversion_rate
        })
    except Exception as e:
        print(f"❌ Erreur stats leads: {str(e)}")
        return jsonify({'error': str(e)}), 500

@lead_bp.route('/leads', methods=['GET'])
@jwt_required()
def get_leads():
    """
    Récupère tous les leads
    ---
    tags:
      - Leads
    security:
      - Bearer: []
    responses:
      200:
        description: Liste des leads
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              name:
                type: string
              email:
                type: string
              phone:
                type: string
              company:
                type: string
              job_title:
                type: string
              source:
                type: string
              estimated_budget:
                type: number
              product_interest:
                type: string
              sector:
                type: string
              company_size:
                type: string
              urgency:
                type: string
              status:
                type: string
              score:
                type: number
    """
    leads = Lead.query.options(joinedload(Lead.assigned_to)).all()
    return jsonify([lead.to_dict() for lead in leads])

@lead_bp.route('/leads/<int:lead_id>', methods=['GET'])
@jwt_required()
def get_lead(lead_id):
    """
    Récupère un lead spécifique
    ---
    tags:
      - Leads
    security:
      - Bearer: []
    parameters:
      - name: lead_id
        in: path
        type: integer
        required: true
        description: ID du lead
    responses:
      200:
        description: Détails du lead
        schema:
          type: object
          properties:
            id:
              type: integer
            name:
              type: string
            email:
              type: string
            phone:
              type: string
            company:
              type: string
            job_title:
              type: string
            source:
              type: string
            estimated_budget:
              type: number
            product_interest:
              type: string
            sector:
              type: string
            company_size:
              type: string
            urgency:
              type: string
            status:
              type: string
            score:
              type: number
      404:
        description: Lead non trouvé
    """
    from app.models.pending_lead import PendingLead
    
    lead = Lead.query.get_or_404(lead_id)
    
    # Chercher le pending lead associé si le lead vient de l'Agent IA
    pending_lead = None
    conversation_data = None
    
    if lead.source == 'Agent IA':
        pending_lead = PendingLead.query.filter_by(lead_id=lead_id).first()
        if pending_lead and pending_lead.data.get('messages'):
            conversation_data = {
                'conversation_id': pending_lead.conversation_id,
                'messages': pending_lead.data.get('messages', [])
            }
    
    return jsonify({
        'id': lead.id,
        'name': lead.name,
        'email': lead.email,
        'phone': lead.phone,
        'company': lead.company,
        'job_title': lead.job_title,
        'source': lead.source,
        'estimated_budget': lead.estimated_budget,
        'service': lead.service.to_dict() if lead.service else None,
        'sector': lead.sector,
        'company_size': lead.company_size,
        'urgency': lead.urgency,
        'status': lead.status,
        'score': lead.score,
        'created_at': lead.created_at.isoformat() if lead.created_at else None,
        'updated_at': lead.updated_at.isoformat() if lead.updated_at else None,
        'conversation': conversation_data  # Conversation du chatbot si disponible
    })

@lead_bp.route('/leads', methods=['POST'])
@jwt_required()
def create_lead():
    """
    Créer un nouveau lead
    ---
    tags:
      - Leads
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
            - email
          properties:
            name:
              type: string
              description: Nom du lead
              example: "Jean Dupont"
            email:
              type: string
              format: email
              description: Email du lead
              example: "jean@example.com"
            phone:
              type: string
              description: Téléphone du lead
              example: "0123456789"
            company:
              type: string
              description: Entreprise du lead
              example: "ACME Corp"
            job_title:
              type: string
              description: Poste du lead
              example: "Directeur Marketing"
            source:
              type: string
              description: Source du lead
              example: "Facebook"
            estimated_budget:
              type: number
              description: Budget estimé
              example: 5000
            service_id:
              type: integer
              description: ID du service recherché
              example: 1
            sector:
              type: string
              description: Secteur d'activité
              example: "Tech"
            company_size:
              type: string
              description: Taille de l'entreprise
              example: "PME"
            urgency:
              type: string
              description: Urgence du besoin
              example: "1-3 mois"
            status:
              type: string
              description: Statut du lead
              default: "new"
              example: "new"
            score:
              type: number
              description: Score de conversion
              default: 0.0
              example: 0.0
    responses:
      201:
        description: Lead créé avec succès
        schema:
          type: object
          properties:
            message:
              type: string
            id:
              type: integer
      400:
        description: Données invalides
    """
    data = request.get_json()
    
    print(f"📥 Données reçues pour création lead: {data}")
    
    try:
        # Vérifier si l'email existe déjà
        if Lead.query.filter_by(email=data['email']).first():
            print(f"❌ Email déjà existant: {data['email']}")
            return jsonify({'error': 'Un lead avec cet email existe déjà'}), 400
        
        lead = Lead(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            company=data.get('company'),
            job_title=data.get('job_title'),
            source=data.get('source', 'interface'),  # Valeur par défaut
            estimated_budget=data.get('estimated_budget'),
            service_id=data.get('service_id'),
            sector=data.get('sector'),
            company_size=data.get('company_size'),
            urgency=data.get('urgency', 'moyenne'),  # Valeur par défaut
            status=data.get('status', 'nouveau'),
            score=data.get('score', 0.0)
        )
        db.session.add(lead)
        db.session.commit()
        
        print(f"✅ Lead créé avec succès: ID={lead.id}, email={lead.email}")
        
        # Log de l'action
        try:
            ActionLog.log_action(
                user_id=get_jwt_identity(),
                action_type='created',
                entity_type='lead',
                entity_id=lead.id,
                changes={'after': {
                    'id': lead.id,
                    'name': lead.name,
                    'email': lead.email,
                    'status': lead.status
                }},
                description=f"Lead '{lead.name}' créé",
                ip_address=request.remote_addr
            )
        except Exception as log_error:
            print(f"⚠️ Erreur log action (non bloquante): {str(log_error)}")
        
        return jsonify({'message': 'Lead created', 'id': lead.id}), 201
    except KeyError as e:
        print(f"❌ KeyError: Champ requis manquant: {str(e)}")
        return jsonify({'error': f'Champ requis manquant: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur création lead: {str(e)}")
        print(f"Type d'erreur: {type(e).__name__}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': f'Erreur lors de la création: {str(e)}'}), 500

@lead_bp.route('/leads/<int:lead_id>', methods=['PUT'])
@jwt_required()
def update_lead(lead_id):
    """
    Mettre à jour un lead
    ---
    tags:
      - Leads
    security:
      - Bearer: []
    parameters:
      - name: lead_id
        in: path
        type: integer
        required: true
        description: ID du lead
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              description: Nom du lead
            email:
              type: string
              format: email
              description: Email du lead
            phone:
              type: string
              description: Téléphone du lead
            company:
              type: string
              description: Entreprise du lead
            job_title:
              type: string
              description: Poste du lead
            source:
              type: string
              description: Source du lead
            estimated_budget:
              type: number
              description: Budget estimé
            service_id:
              type: integer
              description: ID du service recherché
            sector:
              type: string
              description: Secteur d'activité
            company_size:
              type: string
              description: Taille de l'entreprise
            urgency:
              type: string
              description: Urgence du besoin
            status:
              type: string
              description: Statut du lead
            score:
              type: number
              description: Score de conversion
    responses:
      200:
        description: Lead mis à jour
        schema:
          type: object
          properties:
            message:
              type: string
      404:
        description: Lead non trouvé
    """
    lead = Lead.query.get_or_404(lead_id)
    data = request.get_json()
    
    # Capturer l'état avant modification
    before_state = lead.to_dict()
    
    lead.name = data.get('name', lead.name)
    lead.email = data.get('email', lead.email)
    lead.phone = data.get('phone', lead.phone)
    lead.company = data.get('company', lead.company)
    lead.job_title = data.get('job_title', lead.job_title)
    lead.source = data.get('source', lead.source)
    lead.estimated_budget = data.get('estimated_budget', lead.estimated_budget)
    lead.service_id = data.get('service_id', lead.service_id)
    lead.sector = data.get('sector', lead.sector)
    lead.company_size = data.get('company_size', lead.company_size)
    lead.urgency = data.get('urgency', lead.urgency)
    lead.notes = data.get('notes', lead.notes)
    
    # Gérer le changement de statut vers "qualifié"
    old_status = lead.status
    new_status = data.get('status', lead.status)
    lead.status = new_status
    
    lead.score = data.get('score', lead.score)
    db.session.commit()
    
    # Si le lead devient qualifié, créer automatiquement un prospect
    if new_status.lower() in ['qualifié', 'qualifie', 'qualified'] and old_status.lower() not in ['qualifié', 'qualifie', 'qualified']:
        from app.models.prospect import Prospect
        # Vérifier qu'il n'existe pas déjà
        existing_prospect = Prospect.query.filter_by(lead_id=lead.id).first()
        if not existing_prospect:
            prospect = Prospect(
                lead_id=lead.id,
                notes=f"Lead qualifié automatiquement le {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            db.session.add(prospect)
            db.session.commit()
    
    # Log de l'action
    ActionLog.log_action(
        user_id=get_jwt_identity(),
        action_type='updated',
        entity_type='lead',
        entity_id=lead.id,
        changes={'before': before_state, 'after': lead.to_dict()},
        description=f"Lead '{lead.name}' mis à jour",
        ip_address=request.remote_addr
    )
    
    return jsonify({'message': 'Lead updated'})

@lead_bp.route('/leads/<int:lead_id>/status', methods=['PATCH'])
@jwt_required()
def update_lead_status(lead_id):
    """
    Mettre à jour le statut d'un lead
    ---
    tags:
      - Leads
    security:
      - Bearer: []
    parameters:
      - name: lead_id
        in: path
        type: integer
        required: true
        description: ID du lead
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            status:
              type: string
              required: true
              description: Nouveau statut du lead
    responses:
      200:
        description: Statut mis à jour
        schema:
          type: object
          properties:
            message:
              type: string
            prospect_created:
              type: boolean
      404:
        description: Lead non trouvé
    """
    lead = Lead.query.get_or_404(lead_id)
    data = request.get_json()
    
    old_status = lead.status
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({'error': 'Le statut est requis'}), 400
    
    lead.status = new_status
    db.session.commit()
    
    prospect_created = False
    # Si le lead devient qualifié, créer automatiquement un prospect
    if new_status.lower() in ['qualifié', 'qualifie', 'qualified'] and old_status.lower() not in ['qualifié', 'qualifie', 'qualified']:
        from app.models.prospect import Prospect
        # Vérifier qu'il n'existe pas déjà
        existing_prospect = Prospect.query.filter_by(lead_id=lead.id).first()
        if not existing_prospect:
            prospect = Prospect(
                lead_id=lead.id,
                notes=f"Lead qualifié automatiquement le {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            db.session.add(prospect)
            db.session.commit()
            prospect_created = True
    
    # Log de l'action
    ActionLog.log_action(
        user_id=get_jwt_identity(),
        action_type='updated',
        entity_type='lead',
        entity_id=lead.id,
        changes={'old_status': old_status, 'new_status': new_status},
        description=f"Statut du lead '{lead.name}' changé de '{old_status}' à '{new_status}'",
        ip_address=request.remote_addr
    )
    
    return jsonify({
        'message': 'Statut mis à jour',
        'prospect_created': prospect_created,
        'lead': lead.to_dict()
    })

@lead_bp.route('/leads/<int:lead_id>', methods=['DELETE'])
@jwt_required()
def delete_lead(lead_id):
    """
    Supprimer un lead
    ---
    tags:
      - Leads
    security:
      - Bearer: []
    parameters:
      - name: lead_id
        in: path
        type: integer
        required: true
        description: ID du lead à supprimer
    responses:
      200:
        description: Lead supprimé
        schema:
          type: object
          properties:
            message:
              type: string
      404:
        description: Lead non trouvé
    """
    lead = Lead.query.get_or_404(lead_id)
    
    # Capturer les données avant suppression
    lead_data = lead.to_dict()
    lead_name = lead.name
    
    db.session.delete(lead)
    db.session.commit()
    
    # Log de l'action
    ActionLog.log_action(
        user_id=get_jwt_identity(),
        action_type='deleted',
        entity_type='lead',
        entity_id=lead_id,
        changes={'before': lead_data},
        description=f"Lead '{lead_name}' supprimé",
        ip_address=request.remote_addr
    )
    
    return jsonify({'message': 'Lead deleted'})


@lead_bp.route('/leads/export', methods=['POST', 'OPTIONS'])
@jwt_required(optional=True)
def export_leads():
    """
    Exporte les leads en PDF avec champs personnalisables
    ---
    tags:
      - Leads
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: false
        schema:
          type: object
          properties:
            status:
              type: string
              description: Filtrer par statut
            urgency:
              type: string
              description: Filtrer par urgence
            fields:
              type: array
              items:
                type: string
              description: Liste des champs à inclure dans l'export
    responses:
      200:
        description: Fichier PDF des leads
        content:
          application/pdf:
            schema:
              type: string
              format: binary
    """
    # Handle OPTIONS for CORS
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    # Récupérer les filtres et champs depuis le body
    data = request.get_json() or {}
    status_filter = data.get('status')
    urgency_filter = data.get('urgency')
    selected_fields = data.get('fields', [])
    
    # Définir tous les champs disponibles avec leurs configurations
    all_fields = {
        'id': {'label': 'ID', 'width': 1.5, 'max_len': None, 'attr': 'id'},
        'name': {'label': 'Nom', 'width': 3, 'max_len': 20, 'attr': 'name'},
        'email': {'label': 'Email', 'width': 4, 'max_len': 25, 'attr': 'email'},
        'phone': {'label': 'Tél', 'width': 2.5, 'max_len': 15, 'attr': 'phone'},
        'company': {'label': 'Entreprise', 'width': 3, 'max_len': 20, 'attr': 'company'},
        'job_title': {'label': 'Poste', 'width': 2.5, 'max_len': 15, 'attr': 'job_title'},
        'source': {'label': 'Source', 'width': 2, 'max_len': 10, 'attr': 'source'},
        'sector': {'label': 'Secteur', 'width': 2.5, 'max_len': 15, 'attr': 'sector'},
        'urgency': {'label': 'Urgence', 'width': 2, 'max_len': 10, 'attr': 'urgency'},
        'status': {'label': 'Statut', 'width': 2, 'max_len': 10, 'attr': 'status'},
        'score': {'label': 'Score', 'width': 1.5, 'max_len': None, 'attr': 'score'},
        'created_at': {'label': 'Date création', 'width': 2.5, 'max_len': None, 'attr': 'created_at'},
        'assigned_to': {'label': 'Assigné à', 'width': 2.5, 'max_len': 15, 'attr': 'assigned_to'},
    }
    
    # Si aucun champ sélectionné, utiliser les champs par défaut
    if not selected_fields:
        selected_fields = ['id', 'name', 'email', 'phone', 'company', 'job_title', 
                          'source', 'sector', 'urgency', 'status', 'score']
    
    # Filtrer pour ne garder que les champs valides
    valid_fields = [f for f in selected_fields if f in all_fields]
    
    # Construire la requête
    query = Lead.query.order_by(Lead.created_at.desc())
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    if urgency_filter:
        query = query.filter_by(urgency=urgency_filter)
    
    leads = query.all()
    
    # Créer le PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=1*cm, bottomMargin=1*cm)

    elements = []
    styles = getSampleStyleSheet()

    # Ajouter le logo IMAN centré
    from reportlab.platypus import Image
    import os
    
    # Chercher le logo dans plusieurs emplacements possibles
    logo_candidates = [
        os.path.join(os.path.dirname(__file__), 'logo-iman.png'),  # Dans app/
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../../frontend/src/assets/logo-iman.png')),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../frontend/src/assets/logo-iman.png')),
    ]
    
    logo_path = None
    for path in logo_candidates:
        if os.path.exists(path):
            logo_path = path
            break
    
    if logo_path:
        try:
            # Créer l'image du logo (taille réduite pour un meilleur rendu)
            img = Image(logo_path, width=2.5*cm, height=2.5*cm, kind='proportional')
            img.hAlign = 'CENTER'
            elements.append(img)
            elements.append(Spacer(1, 0.3*cm))
            print(f"✅ Logo IMAN chargé depuis: {logo_path}")
        except Exception as e:
            print(f"❌ Erreur chargement logo IMAN: {e}")
    else:
        print(f"⚠️ Logo IMAN introuvable. Chemins testés: {logo_candidates}")

    # Titre avec design professionnel
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor("#630A23"),  # Rouge hsl(351, 75%, 40%)
        spaceAfter=12,
        spaceBefore=6,
        alignment=1,  # Center
        fontName='Helvetica-Bold'
    )
    title = Paragraph(f"EXPORT DES LEADS", title_style)
    elements.append(title)
    
    # Sous-titre avec la date
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#666666'),
        spaceAfter=20,
        alignment=1,  # Center
        fontName='Helvetica'
    )
    subtitle = Paragraph(f"{datetime.now().strftime('%d/%m/%Y à %H:%M')}", subtitle_style)
    elements.append(subtitle)
    elements.append(Spacer(1, 0.3*cm))
    
    # En-têtes du tableau (basés sur les champs sélectionnés)
    headers = [all_fields[field]['label'] for field in valid_fields]
    data = [headers]
    
    # Données
    for lead in leads:
        row = []
        for field in valid_fields:
            field_config = all_fields[field]
            attr_value = getattr(lead, field_config['attr'], '')

            # Formatage spécial pour certains champs
            if field == 'id':
                value = str(attr_value)
            elif field == 'score':
                value = f"{int(attr_value * 100)}%" if attr_value is not None else ''
            elif field == 'created_at':
                value = attr_value.strftime('%d/%m/%Y') if attr_value else ''
            elif field == 'assigned_to':
                # attr_value est un objet User ou None
                value = attr_value.username[:15] if attr_value and hasattr(attr_value, 'username') else ''
            else:
                # Appliquer la longueur max si définie
                if attr_value:
                    value = str(attr_value)
                    if field_config['max_len']:
                        value = value[:field_config['max_len']]
                else:
                    value = ''
            row.append(value)
        data.append(row)
    
    # Créer le tableau avec largeurs dynamiques
    col_widths = [all_fields[field]['width']*cm for field in valid_fields]
    table = Table(data, colWidths=col_widths)

    # Style du tableau avec design professionnel (rouge hsl(351, 75%, 40%))
    table.setStyle(TableStyle([
        # En-tête - Rouge principal
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#630A23')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),

        # Corps du tableau
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#333333')),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),

        # Bordures élégantes
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DDDDDD')),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#630A23')),

        # Alternance de couleurs subtile
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FDF5F6')]),
    ]))
    
    elements.append(table)
    
    # Footer professionnel avec ligne de séparation
    elements.append(Spacer(1, 0.5*cm))
    
    # Ligne de séparation
    from reportlab.platypus import HRFlowable
    hr = HRFlowable(width="100%", thickness=1, color=colors.HexColor('#630A23'), 
                    spaceAfter=0.3*cm, spaceBefore=0.3*cm)
    elements.append(hr)
    
    # Informations du footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        alignment=1  # Center
    )
    footer_text = Paragraph(
        f"<b>Total: {len(leads)} lead(s)</b> | Généré par <b>IMAN Sales Hub</b> | "
        f"© {datetime.now().year} IMAN",
        footer_style
    )
    elements.append(footer_text)
    
    # Générer le PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Créer la réponse
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=leads_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    
    # Logger l'export
    try:
        ActionLog.log_action(
            user_id=get_jwt_identity(),
            action_type='exported',
            entity_type='lead',
            entity_id=0,
            changes={'count': len(leads), 'format': 'pdf'},
            description=f"Export de {len(leads)} leads en PDF",
            ip_address=request.remote_addr
        )
    except:
        pass  # Ne pas bloquer l'export si le log échoue
    
    return response
