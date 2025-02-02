from flask import Blueprint, request, jsonify
from app import db
from app.models import ModelParams

model_params_bp = Blueprint("model_params", __name__)

# 📌 Add new model parameters
@model_params_bp.route("/add", methods=["POST"])
def add_model_params():
    try:
        data = request.get_json()

        new_params = ModelParams(
            start_date=data["start_date"],
            end_date=data["end_date"],
            spiking_duration=data["spiking_duration"],
            accuracy=data["accuracy"],
            precision=data["precision"],
            recall=data["recall"],
            f1_score=data["f1_score"],
        )

        db.session.add(new_params)
        db.session.commit()

        return jsonify({"message": "Model parameters added successfully!"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# 📌 Get all model parameters
@model_params_bp.route("/all", methods=["GET"])
def get_all_model_params():
    try:
        params = ModelParams.query.all()
        return jsonify([param.to_dict() for param in params]), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 📌 Get model parameters by ID
@model_params_bp.route("/<int:param_id>", methods=["GET"])
def get_model_param(param_id):
    try:
        param = ModelParams.query.get(param_id)
        if not param:
            return jsonify({"error": "Model parameters not found"}), 404
        return jsonify(param.to_dict()), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 📌 Update model parameters
@model_params_bp.route("/update/<int:param_id>", methods=["PUT"])
def update_model_params(param_id):
    try:
        param = ModelParams.query.get(param_id)
        if not param:
            return jsonify({"error": "Model parameters not found"}), 404

        data = request.get_json()
        param.start_date = data.get("start_date", param.start_date)
        param.end_date = data.get("end_date", param.end_date)
        param.spiking_duration = data.get("spiking_duration", param.spiking_duration)
        param.accuracy = data.get("accuracy", param.accuracy)
        param.precision = data.get("precision", param.precision)
        param.recall = data.get("recall", param.recall)
        param.f1_score = data.get("f1_score", param.f1_score)

        db.session.commit()
        return jsonify({"message": "Model parameters updated successfully!"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# 📌 Delete model parameters
@model_params_bp.route("/delete/<int:param_id>", methods=["DELETE"])
def delete_model_params(param_id):
    try:
        param = ModelParams.query.get(param_id)
        if not param:
            return jsonify({"error": "Model parameters not found"}), 404

        db.session.delete(param)
        db.session.commit()
        return jsonify({"message": "Model parameters deleted successfully!"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
