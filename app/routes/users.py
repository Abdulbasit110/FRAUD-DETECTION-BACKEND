from flask import Blueprint, jsonify
from ..models import User

user_routes = Blueprint("users", __name__)

@user_routes.route("/", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify([{"id": user.id, "email": user.email} for user in users]), 200
