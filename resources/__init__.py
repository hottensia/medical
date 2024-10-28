
from flask import Blueprint
from .user_resources import user_routes
from .appointments_resources import appointments_routes
from .scheduled_appointments_resources import scheduled_appointments_routes
from .patient_notes_resource import patient_notes_routes
from .mood_entries_routes import mood_entries_routes
from .treatment_routes import treatment_routes
from .notification_resource import notification_routes
from .chat_routes import chat_routes

api_routes = Blueprint('api', __name__)

api_routes.register_blueprint(user_routes)
api_routes.register_blueprint(appointments_routes)
api_routes.register_blueprint(scheduled_appointments_routes)
api_routes.register_blueprint(patient_notes_routes)
api_routes.register_blueprint(mood_entries_routes)
api_routes.register_blueprint(treatment_routes)
api_routes.register_blueprint(notification_routes)
api_routes.register_blueprint(chat_routes)





