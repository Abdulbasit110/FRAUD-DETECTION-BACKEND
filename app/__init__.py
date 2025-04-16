from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from .config import Config
from .database import db, socketio
from .routes.transactions import transaction_routes
from .routes.auth import auth_routes
from .routes.predict import predict_bp
from .routes.model_params import model_params_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Enable CORS for all routes
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Initialize database and migrations
    db.init_app(app)
    migrate = Migrate(app, db)

    # Initialize SocketIO with Flask app
    socketio.init_app(app, cors_allowed_origins="*")

    # Register blueprints
    app.register_blueprint(transaction_routes, url_prefix="/transactions")
    app.register_blueprint(auth_routes, url_prefix="/auth")
    app.register_blueprint(predict_bp, url_prefix="/model")
    app.register_blueprint(model_params_bp, url_prefix="/model_params")

    # Health check endpoint
    @app.route('/')
    def ping():
        return "Server is up and running!", 200

    return app
