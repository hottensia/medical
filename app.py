from flask import Flask
from flask_migrate import Migrate
from config import config
from models import db
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

env = os.environ.get('FLASK_ENV', 'default')

app = Flask(__name__)
app.config.from_object(config[env])

# CORS configuration (consider restricting origins in production)
CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": True}})

# Initialize extensions
mail = Mail(app)
db.init_app(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)

# Register blueprints
from resources import api_routes
from resources.appointments_resources import appointments_routes

app.register_blueprint(api_routes)
app.register_blueprint(appointments_routes)

# Create database tables if they do not exist
with app.app_context():
    db.create_all()

# Global error handler for better feedback
@app.errorhandler(Exception)
def handle_error(e):
    app.logger.error(f"An error occurred: {e}")
    return {"message": "An internal error occurred. Please try again later."}, 500

if __name__ == '__main__':
    app.run(debug=True)  # Change this for production use
