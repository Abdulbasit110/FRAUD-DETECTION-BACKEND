from flask import Flask
from .config import Config
from .database import db
# from .fraud_detection import load_model
from flask_migrate import Migrate
from sqlalchemy import text 

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    migrate = Migrate(app, db)

    @app.route('/ping')
    def ping():
        return "Hello, World! Server is up and running!"
    

    # @app.route('/check-db')
    # def check_db():
    #     from .models import TestModel
    #     try:
    #         # Attempt to query the TestModel table
    #         test_data = TestModel.query.all()
    #         return "Database is connected!", 200
    #     except Exception as e:
    #         return f"Database connection failed: {e}", 500
        

    # with app.app_context():
    #     from .views import transaction  # Import blueprint
    #     app.register_blueprint(transaction.bp)
        
    #     db.create_all()  # Initialize database tables
    #     load_model()


    @app.route('/check-db')
    def check_db():
        try:
            # Use text() to wrap the raw SQL expression
            result = db.session.execute(text('SELECT 1'))
            return "Database is connected!", 200
        except Exception as e:
            return f"Database connection failed: {e}", 500

    return app
