from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.appointment import Appointment, db
from app.models.appointment_event import AppointmentEvent
from app.models.notification import Notification
from app.utils.decorators import admin_required
from datetime import datetime, timedelta
from flask_cors import cross_origin

appointment_bp = Blueprint('appointment_bp', __name__)


@appointment_bp.route('/appointments', methods=['POST', 'OPTIONS'])
@cross_origin()
def create_appointment():
    """
    Crée un nouveau rendez-vous (public pour le chatbot)
    ---
    tags:
      - Appointments
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - nom
            - telephone
            - appointment_date
            - appointment_time
          properties:
            nom:
              type: string
            telephone:
              type: string
            appointment_date:
              type: string
              format: date
            appointment_time:
              type: string
            motif:
              type: string
    responses:
      201:
        description: Rendez-vous créé
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.json
    
    if not data or not all(k in data for k in ['nom', 'telephone', 'appointment_date', 'appointment_time']):
        return jsonify({'message': 'Données manquantes'}), 400
    
    try:
        # Parser la date et l'heure
        appointment_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
        appointment_time = datetime.strptime(data['appointment_time'], '%H:%M').time()
        
        appointment = Appointment.create_appointment(
            nom=data['nom'],
            telephone=data['telephone'],
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            motif=data.get('motif')
        )
        
        return jsonify(appointment.to_dict()), 201
    except ValueError as e:
        return jsonify({'message': f'Format de date/heure invalide: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'message': f'Erreur: {str(e)}'}), 500


@appointment_bp.route('/appointments', methods=['GET'])
@jwt_required()
def get_appointments():
    """
    Récupère la liste des rendez-vous (admin uniquement)
    ---
    tags:
      - Appointments
    security:
      - Bearer: []
    parameters:
      - name: status
        in: query
        type: string
        enum: [pending, confirmed, cancelled, completed, all]
        default: all
      - name: start_date
        in: query
        type: string
        format: date
      - name: end_date
        in: query
        type: string
        format: date
    responses:
      200:
        description: Liste des rendez-vous
    """
    status = request.args.get('status', 'all')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Appointment.query
    
    # Filtres
    if status != 'all':
        query = query.filter_by(status=status)
    
    if start_date:
        query = query.filter(Appointment.appointment_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    
    if end_date:
        query = query.filter(Appointment.appointment_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    # Tri par date croissante
    query = query.order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc())
    
    appointments = query.all()
    
    return jsonify({
        'appointments': [apt.to_dict() for apt in appointments],
        'total': len(appointments)
    })


@appointment_bp.route('/appointments/<int:id>', methods=['GET'])
@jwt_required()
def get_appointment(id):
    """
    Récupère un rendez-vous spécifique
    ---
    tags:
      - Appointments
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Détails du rendez-vous
      404:
        description: Rendez-vous non trouvé
    """
    appointment = Appointment.query.get_or_404(id)
    return jsonify(appointment.to_dict())


@appointment_bp.route('/appointments/<int:id>/status', methods=['PUT'])
@jwt_required()
def update_appointment_status(id):
    """
    Met à jour le statut d'un rendez-vous
    ---
    tags:
      - Appointments
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - status
          properties:
            status:
              type: string
              enum: [pending, confirmed, cancelled, completed]
    responses:
      200:
        description: Statut mis à jour
      404:
        description: Rendez-vous non trouvé
    """
    data = request.json
    
    if not data or 'status' not in data:
        return jsonify({'message': 'Statut requis'}), 400
    
    appointment = Appointment.query.get_or_404(id)
    
    valid_statuses = ['pending', 'confirmed', 'cancelled', 'completed']
    if data['status'] not in valid_statuses:
        return jsonify({'message': 'Statut invalide'}), 400
    
    appointment.update_status(data['status'])
    
    return jsonify({
        'message': 'Statut mis à jour',
        'appointment': appointment.to_dict()
    })


@appointment_bp.route('/appointments/<int:id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_appointment(id):
    """
    Supprime un rendez-vous (admin uniquement)
    ---
    tags:
      - Appointments
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Rendez-vous supprimé
      404:
        description: Rendez-vous non trouvé
    """
    appointment = Appointment.query.get_or_404(id)
    db.session.delete(appointment)
    db.session.commit()
    
    return jsonify({'message': 'Rendez-vous supprimé avec succès'})


@appointment_bp.route('/appointments/stats', methods=['GET'])
@jwt_required()
def get_appointment_stats():
    """
    Statistiques sur les rendez-vous
    ---
    tags:
      - Appointments
    security:
      - Bearer: []
    responses:
      200:
        description: Statistiques des rendez-vous
    """
    total = Appointment.query.count()
    pending = Appointment.query.filter_by(status='pending').count()
    confirmed = Appointment.query.filter_by(status='confirmed').count()
    completed = Appointment.query.filter_by(status='completed').count()
    cancelled = Appointment.query.filter_by(status='cancelled').count()
    
    return jsonify({
        'total': total,
        'pending': pending,
        'confirmed': confirmed,
        'completed': completed,
        'cancelled': cancelled
    })


# ==================== NOUVELLES ROUTES POUR L'AGENDA UNIFIÉ ====================

@appointment_bp.route('/appointments/events', methods=['GET'])
@jwt_required()
def get_appointment_events():
    """Récupère tous les événements d'agenda"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = AppointmentEvent.query
    
    if start_date:
        query = query.filter(AppointmentEvent.start_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(AppointmentEvent.start_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    events = query.order_by(AppointmentEvent.start_date, AppointmentEvent.start_time).all()
    return jsonify([e.to_dict() for e in events]), 200


@appointment_bp.route('/appointments/events', methods=['POST'])
@jwt_required()
def create_appointment_event():
    """Crée un nouvel événement d'agenda"""
    data = request.json
    user_id = get_jwt_identity()
    
    if not data.get('title') or not data.get('start_date') or not data.get('start_time'):
        return jsonify({'message': 'Titre, date et heure requis'}), 400
    
    try:
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time() if data.get('end_time') else None
        
        event = AppointmentEvent(
            title=data['title'],
            client_name=data.get('client_name'),
            client_id=data.get('client_id'),
            type=data.get('type', 'rendez-vous'),
            start_date=start_date,
            start_time=start_time,
            end_time=end_time,
            location=data.get('location'),
            description=data.get('description'),
            assigned_to_id=data.get('assigned_to_id', user_id),
            status=data.get('status', 'planifie'),
            priority=data.get('priority', 'moyenne'),
            reminder_minutes=data.get('reminder_minutes', 15),
            participants=data.get('participants', [])
        )
        
        db.session.add(event)
        db.session.commit()
        
        # Créer une notification de rappel si demandé
        if event.reminder_minutes and event.assigned_to_id:
            notification = Notification(
                user_id=event.assigned_to_id,
                type='alert',
                title=f'Rappel: {event.title}',
                message=f'Rendez-vous prévu le {event.start_date.strftime("%d/%m/%Y")} à {event.start_time.strftime("%H:%M")}',
                link=f'/agenda',
                data={'appointment_event_id': event.id}
            )
            db.session.add(notification)
            db.session.commit()
        
        return jsonify(event.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erreur: {str(e)}'}), 500


@appointment_bp.route('/appointments/events/<int:event_id>', methods=['GET'])
@jwt_required()
def get_appointment_event(event_id):
    """Récupère un événement spécifique"""
    event = AppointmentEvent.query.get_or_404(event_id)
    return jsonify(event.to_dict()), 200


@appointment_bp.route('/appointments/events/<int:event_id>', methods=['PUT'])
@jwt_required()
def update_appointment_event(event_id):
    """Met à jour un événement d'agenda"""
    event = AppointmentEvent.query.get_or_404(event_id)
    data = request.json
    
    try:
        if data.get('title'):
            event.title = data['title']
        if data.get('client_name'):
            event.client_name = data['client_name']
        if data.get('type'):
            event.type = data['type']
        if data.get('start_date'):
            event.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if data.get('start_time'):
            event.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        if data.get('end_time'):
            event.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        if 'location' in data:
            event.location = data['location']
        if 'description' in data:
            event.description = data['description']
        if data.get('status'):
            event.status = data['status']
        if data.get('priority'):
            event.priority = data['priority']
        if 'reminder_minutes' in data:
            event.reminder_minutes = data['reminder_minutes']
        if 'participants' in data:
            event.participants = data['participants']
        
        event.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(event.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erreur: {str(e)}'}), 500


@appointment_bp.route('/appointments/events/<int:event_id>/status', methods=['PUT'])
@jwt_required()
def update_event_status(event_id):
    """Met à jour le statut d'un événement"""
    event = AppointmentEvent.query.get_or_404(event_id)
    data = request.json
    
    if not data.get('status'):
        return jsonify({'message': 'Statut requis'}), 400
    
    event.status = data['status']
    event.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(event.to_dict()), 200


@appointment_bp.route('/appointments/events/<int:event_id>', methods=['DELETE'])
@jwt_required()
def delete_appointment_event(event_id):
    """Supprime un événement d'agenda"""
    event = AppointmentEvent.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    
    return jsonify({'message': 'Événement supprimé'}), 200


@appointment_bp.route('/appointments/events/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming_events():
    """Récupère les prochains événements"""
    user_id = get_jwt_identity()
    today = datetime.utcnow().date()
    
    events = AppointmentEvent.query.filter(
        AppointmentEvent.start_date >= today,
        AppointmentEvent.status.in_(['planifie', 'confirme']),
        AppointmentEvent.assigned_to_id == user_id
    ).order_by(AppointmentEvent.start_date, AppointmentEvent.start_time).limit(10).all()
    
    return jsonify([e.to_dict() for e in events]), 200
