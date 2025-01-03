from flask import Flask
from flask_migrate import Migrate
from .config import Config
from .database import db
from .routes.transactions import transaction_routes
from .routes.auth import auth_routes
from .routes.users import user_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate = Migrate(app, db)

    # Register blueprints
    app.register_blueprint(transaction_routes, url_prefix="/transactions")
    app.register_blueprint(auth_routes, url_prefix="/auth")
    app.register_blueprint(user_routes, url_prefix="/users")

    @app.route('/ping')
    def ping():
        return "Server is up and running!", 200

    return app
