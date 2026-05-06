# Init for models package
from app.models.lead import db
from app.models.user import User, UserRole
from app.models.lead import Lead
from app.models.prospect import Prospect
from app.models.service import Service
from app.models.pending_lead import PendingLead
from app.models.conversation import Conversation
from app.models.action_log import ActionLog
from app.models.appointment import Appointment
from app.models.client import Client
from app.models.dossier import Dossier, DossierAction
from app.models.document import Document, DocumentTemplate
from app.models.validation import Validation
from app.models.notification import Notification, NotificationTemplate
