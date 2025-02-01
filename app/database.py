from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

db = SQLAlchemy()
# Initialize SocketIO globally
socketio = SocketIO(cors_allowed_origins="*")