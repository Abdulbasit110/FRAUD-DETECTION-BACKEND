from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from .config import Config, config
from .database import db, socketio
from .routes.transactions import transaction_routes
from .routes.auth import auth_routes
from .routes.predict import predict_bp
from .routes.model_params import model_params_bp
from .routes.customer_transactions import customer_transaction_routes
# DISABLED: Removed scheduler import since we're not using automated test transactions
# from .utils.scheduler import init_scheduler
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load configuration from app/config.py
    app.config.from_object(config[config_name])
    
    # Set up CORS
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Initialize database and migrations
    db.init_app(app)
    migrate = Migrate(app, db)

    # Initialize SocketIO with Flask app
    socketio.init_app(app, cors_allowed_origins="*")    # Register blueprints
    app.register_blueprint(transaction_routes, url_prefix="/transactions")
    app.register_blueprint(customer_transaction_routes, url_prefix="/customer-transactions")
    app.register_blueprint(auth_routes, url_prefix="/auth")
    app.register_blueprint(predict_bp, url_prefix="/model")
    app.register_blueprint(model_params_bp, url_prefix="/model_params")# Create database tables
    with app.app_context():
        db.create_all()
    
    # Initialize the scheduler for automated test transactions
    # DISABLED: Commenting out the scheduler to stop automated test transactions
    # if app.config.get('ENV') != 'production':
    #     init_scheduler(app)
    #     app.logger.info("Automated test transaction scheduler initialized")

    # Health check endpoint
    @app.route('/')
    def ping():
        return "Server is up and running!", 200

    return app
