from flask import Blueprint, request, jsonify
import joblib
import numpy as np
import os
from flask_socketio import SocketIO
from app.models import db, Transaction, Notification

# Initialize SocketIO
socketio = SocketIO(cors_allowed_origins="*")

# Define a new blueprint for predictions
predict_bp = Blueprint('predict', __name__)

# Load the trained ML model
MODEL_FILE = os.path.join(os.path.dirname(__file__), '../../random_forest_model.pkl')

if os.path.exists(MODEL_FILE):
    model = joblib.load(MODEL_FILE)
else:
    model = None
    print("ERROR: Model file not found!")

@predict_bp.route('/predict', methods=['POST'])
def predict():
    try:
        # Check if model is loaded
        if model is None:
            return jsonify({'error': 'Model not found. Please check the model file path.'}), 500

        # Parse input JSON
        data = request.get_json(force=True)

        # Create transaction with initial "Pending" status
        transaction = Transaction(
            sending_date=data.get("sending_date"),
            mtn=data.get("mtn"),
            sender_id=data.get("sender_id"),
            sender_legal_name=data.get("sender_legal_name"),
            channel=data.get("channel"),
            payer_rep_code=data.get("payer_rep_code"),
            sender_country=data.get("sender_country"),
            sender_status=data.get("sender_status"),
            sender_date_of_birth=data.get("sender_date_of_birth"),
            sender_email=data.get("sender_email"),
            sender_mobile=data.get("sender_mobile"),
            sender_phone=data.get("sender_phone"),
            beneficiary_client_id=data.get("beneficiary_client_id"),
            beneficiary_name=data.get("beneficiary_name"),
            beneficiary_first_name=data.get("beneficiary_first_name"),
            beneficiary_country=data.get("beneficiary_country"),
            beneficiary_email=data.get("beneficiary_email"),
            beneficiary_mobile=data.get("beneficiary_mobile"),
            beneficiary_phone=data.get("beneficiary_phone"),
            sending_country=data.get("sending_country"),
            payout_country=data.get("payout_country"),
            status="Pending",  # Default status before prediction
            total_sale=data.get("total_sale"),
            sending_currency=data.get("sending_currency"),
            payment_method=data.get("payment_method"),
            compliance_release_date=data.get("compliance_release_date"),
            sender_status_detail=None  # Initially None, will be updated after prediction
        )

        # Save transaction to DB with pending status
        db.session.add(transaction)
        db.session.commit()

        # Extract relevant features for prediction
        try:
            features = [
                data.get("total_sale"),  # Ensure correct feature name
                data.get("payer_rep_code"),  # Match naming convention
                data.get("sending_currency"),
                data.get("payment_method"),
            ]
        except KeyError as e:
            return jsonify({'error': f'Missing feature in input: {str(e)}'}), 400

        # Convert features to NumPy array
        features_array = np.array(features).reshape(1, -1)

        # Predict using the model
        prediction = model.predict(features_array)
        predicted_label = int(prediction[0])  # Convert prediction result to integer

        # Update transaction with prediction result
        transaction.status = f"Predicted: {predicted_label}"
        transaction.sender_status_detail = f"Auto-assigned status based on prediction {predicted_label}"
        db.session.commit()

        # Create notification for the user
        notification = Notification(
            user_id="user_id_here",  # Replace with actual user ID
            message=f"New transaction added. Predicted category: {predicted_label}",
            transaction_id=transaction.id
        )
        db.session.add(notification)
        db.session.commit()

        # Emit real-time notification
        socketio.emit("new_transaction", {
            "message": f"New transaction added. Predicted category: {predicted_label}",
            "transaction_id": transaction.id
        })

        return jsonify({
            "message": "Transaction added and predicted successfully.",
            "transaction_id": transaction.id,
            "predicted_label": predicted_label
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@predict_bp.route('/ping', methods=['GET'])
def ping():
    """Check model status and return feature importance if available"""
    try:
        if model is None:
            return jsonify({'error': 'Model not found'}), 500
        return jsonify({'feature_importance': model.feature_importances_.tolist()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
