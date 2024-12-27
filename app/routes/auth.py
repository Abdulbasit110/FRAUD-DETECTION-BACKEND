from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from ..models import User
from ..database import db
import uuid

auth_routes = Blueprint("auth", __name__)

@auth_routes.route("/signup", methods=["POST"])
def signup():
    data = request.json
    try:
        hashed_password = generate_password_hash(data["password"], method="sha256")
        user = User(id=str(uuid.uuid4()), email=data["email"], password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except IntegrityError:
        return jsonify({"error": "User already exists"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_routes.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(email=data["email"]).first()
    if user and check_password_hash(user.password, data["password"]):
        return jsonify({"message": "Login successful", "user_id": user.id}), 200
    return jsonify({"error": "Invalid credentials"}), 401


@auth_routes.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.json
    user = User.query.filter_by(email=data["email"]).first()
    if user:
        new_password = str(uuid.uuid4())[:8]
        user.password = generate_password_hash(new_password, method="sha256")
        db.session.commit()
        return jsonify({"message": f"New password is {new_password}"}), 200
    return jsonify({"error": "Email not found"}), 404


@auth_routes.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.json
    user = User.query.filter_by(email=data["email"]).first()
    if user and check_password_hash(user.password, data["old_password"]):
        user.password = generate_password_hash(data["new_password"], method="sha256")
        db.session.commit()
        return jsonify({"message": "Password reset successful"}), 200
    return jsonify({"error": "Invalid credentials"}), 401
