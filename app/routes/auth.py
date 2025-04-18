from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from ..models import User
from ..database import db
import uuid
import jwt
import datetime
from functools import wraps
import os
import random
import string
from ..utils.email_service import send_verification_code

auth_routes = Blueprint("auth", __name__)

# Generate random verification code
def generate_verification_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

# JWT token generation
def generate_reset_token(user_id):
    return jwt.encode(
        {
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        },
        current_app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )

# Token verification decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        # Handle 'Bearer' prefix if present
        if token.startswith('Bearer '):
            token = token.split(' ')[1]
            
        try:
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'Invalid token'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({'error': f'Invalid token: {str(e)}'}), 401
        except Exception as e:
            return jsonify({'error': f'Token error: {str(e)}'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# ---------------- SIGNUP ----------------
@auth_routes.route("/signup", methods=["POST"])
def signup():
    data = request.json
    try:
        hashed_password = generate_password_hash(data["password"])
        user = User(email=data["email"], password=hashed_password)
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
        if not user.is_approved:
            return jsonify({"error": "User is not approved yet"}), 403
        
        # Generate JWT token
        token = jwt.encode(
            {
                'user_id': user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            },
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        return jsonify({
            "message": "Login successful", 
            "token": token,
            "user": {
                "id": user.id,
                "role": user.role,
                "is_approved": user.is_approved,
                "email": user.email
            }
        }), 200
    return jsonify({"error": "Invalid credentials"}), 401


# ---------------- FORGOT PASSWORD ----------------
@auth_routes.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.json
    user = User.query.filter_by(email=data["email"]).first()
    
    if not user:
        return jsonify({"error": "Email not found"}), 404
    
    # Generate verification code
    verification_code = generate_verification_code()
    user.verification_code = verification_code
    user.verification_code_expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    db.session.commit()
    
    # Send verification code via email
    email_sent = send_verification_code(user.email, verification_code)
    
    if not email_sent:
        # If email fails to send, we still have the code in the database
        # In a production app, you might want to handle this differently
        return jsonify({
            "message": "Failed to send verification code email. Please try again.",
            "code": verification_code  # Only include this for development/testing!
        }), 500
    
    return jsonify({
        "message": "Verification code has been sent to your email"
    }), 200

# ---------------- VERIFY CODE ----------------
@auth_routes.route("/verify-code", methods=["POST"])
def verify_code():
    data = request.json
    if not data.get("email") or not data.get("code"):
        return jsonify({"error": "Email and verification code are required"}), 400
        
    user = User.query.filter_by(email=data["email"]).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    if not user.verification_code:
        return jsonify({"error": "No verification code requested"}), 400
        
    if user.verification_code_expires_at < datetime.datetime.utcnow():
        return jsonify({"error": "Verification code has expired"}), 400
        
    if user.verification_code != data["code"]:
        return jsonify({"error": "Invalid verification code"}), 400
    
    # Generate reset token after successful verification
    reset_token = generate_reset_token(user.id)
    
    return jsonify({
        "message": "Code verified successfully",
        "reset_token": reset_token
    }), 200

# ---------------- RESET PASSWORD ----------------
@auth_routes.route("/reset-password", methods=["POST"])
@token_required
def reset_password(current_user):
    data = request.json
    
    if not data.get("new_password"):
        return jsonify({"error": "New password is required"}), 400
    
    if not data.get("old_password"):
        return jsonify({"error": "old password is required"}), 400
    
    if not check_password_hash(current_user.password, data["old_password"]):
        return jsonify({"error": "Invalid old password"}), 400
    
    # Update password
    current_user.password = generate_password_hash(data["new_password"])
    # Clear verification code after password reset
    current_user.verification_code = None
    current_user.verification_code_expires_at = None
    db.session.commit()
    
    return jsonify({"message": "Password has been reset successfully"}), 200


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
    result = [{"id": user.id, "email": user.email, "role": user.role, "created_at": user.created_at, "is_approved": user.is_approved} for user in users]
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


# ---------------- APPROVE USER ----------------
@auth_routes.route("/approve-user/<int:user_id>", methods=["PUT"])
def approve_user(user_id):
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.is_approved = True
        db.session.commit()
        
        return jsonify({
            "message": f"User {user.email} approved successfully",
            "user": user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
