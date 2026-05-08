from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app.config import Config
from app.models.lead import db
from app.models.user import User  # Import nécessaire pour les migrations
from app.models.service import Service  # Import nécessaire pour les migrations
from app.models.pending_lead import PendingLead  # Import nécessaire pour les migrations
from app.models.action_log import ActionLog  # Import nécessaire pour les migrations
from app.models.conversation import Conversation  # Import nécessaire pour les migrations
from app.models.appointment import Appointment  # Import nécessaire pour les migrations
from app.models.appointment_event import AppointmentEvent  # Import nécessaire pour les migrations
from app.models.client import Client  # Import nécessaire pour les migrations
from app.models.dossier import Dossier, DossierAction  # Import nécessaire pour les migrations
from app.models.opportunity_line import OpportunityLine  # Import nécessaire pour les migrations
from app.models.document import Document, DocumentTemplate  # Import nécessaire pour les migrations
from app.models.validation import Validation  # Import nécessaire pour les migrations
from app.models.notification import Notification  # Import nécessaire pour les migrations
from app.routes.lead_routes import lead_bp
from app.routes.auth_routes import auth_bp

from app.routes.service_routes import service_bp
from app.routes.pending_lead_routes import pending_lead_bp
from app.routes.action_log_routes import action_log_bp
from app.routes.conversation_routes import conversation_bp
from app.routes.appointment_routes import appointment_bp
from app.routes.prospect_routes import prospect_bp
from app.routes.client_routes import client_bp
from app.routes.dossier_routes import dossier_bp
from app.routes.notification_routes import notification_bp
from app.routes.validation_routes import validation_bp
from flasgger import Swagger

app = Flask(__name__)
app.config.from_object(Config)

# Configuration CORS
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://localhost:8080",
            "https://reina630.github.io",
        ],
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 3600
    }
})

# Initialisation des extensions
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# Configuration JWT pour convertir l'identité en string
@jwt.user_identity_loader
def user_identity_lookup(user_id):
    return str(user_id)

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.get(int(identity))

# Gestionnaire d'erreurs JWT
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'message': 'Token expiré'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'message': 'Token invalide'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'message': 'Token manquant'}), 401

# Configuration Swagger avec support JWT
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header. Example: 'Bearer {token}'"
        }
    }
}

swagger = Swagger(app, config=swagger_config)

# Enregistrement des blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(service_bp, url_prefix='/api')
app.register_blueprint(lead_bp, url_prefix='/api')
app.register_blueprint(pending_lead_bp, url_prefix='/api')
app.register_blueprint(action_log_bp, url_prefix='/api')
app.register_blueprint(conversation_bp, url_prefix='/api')
app.register_blueprint(appointment_bp, url_prefix='/api')
app.register_blueprint(notification_bp, url_prefix='/api')
app.register_blueprint(prospect_bp)
app.register_blueprint(client_bp)
app.register_blueprint(dossier_bp)
app.register_blueprint(validation_bp)
