from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from ..models import User
from ..database import db
import uuid

auth_routes = Blueprint("auth", __name__)

# ---------------- SIGNUP ----------------
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


# ---------------- LOGIN ----------------
@auth_routes.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(email=data["email"]).first()
    if user and check_password_hash(user.password, data["password"]):
        return jsonify({"message": "Login successful", "user_id": user.id, "role": user.role}), 200
    return jsonify({"error": "Invalid credentials"}), 401


# ---------------- FORGOT PASSWORD ----------------
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


# ---------------- RESET PASSWORD ----------------
@auth_routes.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.json
    user = User.query.filter_by(email=data["email"]).first()
    if user and check_password_hash(user.password, data["old_password"]):
        user.password = generate_password_hash(data["new_password"], method="sha256")
        db.session.commit()
        return jsonify({"message": "Password reset successful"}), 200
    return jsonify({"error": "Invalid credentials"}), 401


# ---------------- MAKE USER ADMIN ----------------
@auth_routes.route("/make-admin", methods=["POST"])
def make_admin():
    data = request.json
    user = User.query.filter_by(email=data["email"]).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.role = "admin"
    db.session.commit()
    return jsonify({"message": f"User {user.email} is now an admin"}), 200


# ---------------- FETCH ALL USERS ----------------
@auth_routes.route("/users", methods=["GET"])
def get_all_users():
    users = User.query.all()
    result = [{"id": user.id, "email": user.email, "role": user.role, "created_at": user.created_at} for user in users]
    return jsonify(result), 200


# ---------------- FETCH A SPECIFIC USER ----------------
@auth_routes.route("/users/<string:user_id>", methods=["GET"])
def get_user_by_id(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"id": user.id, "email": user.email, "role": user.role, "created_at": user.created_at}), 200


# ---------------- UPDATE USER INFO ----------------
@auth_routes.route("/update-user", methods=["PUT"])
def update_user():
    data = request.json
    user = User.query.filter_by(email=data["email"]).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if "new_email" in data:
        user.email = data["new_email"]
    if "new_password" in data:
        user.password = generate_password_hash(data["new_password"], method="sha256")

    db.session.commit()
    return jsonify({"message": "User information updated successfully"}), 200


# ---------------- DELETE A USER ----------------
@auth_routes.route("/delete-user", methods=["DELETE"])
def delete_user():
    data = request.json
    user = User.query.filter_by(email=data["email"]).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"User {data['email']} deleted successfully"}), 200
