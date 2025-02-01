from flask import Blueprint, request, jsonify
import joblib
import numpy as np
import os
from flask_socketio import emit
from sklearn.preprocessing import StandardScaler
from app import db, socketio  # Import socketio from app/__init__.py
from app.models import Transaction, Notification

# Define a new blueprint for predictions
predict_bp = Blueprint('predict', __name__)

# Load the trained ML model
MODEL_FILE = os.path.join(os.path.dirname(__file__), '../../random_forest_model.pkl')

if os.path.exists(MODEL_FILE):
    model = joblib.load(MODEL_FILE)
    print("✅ Model loaded successfully.")
else:
    model = None
    print("❌ ERROR: Model file not found!")

# Define the feature order used in model training
FEATURES = [
    "Total Trx", "Total Beneficiaries", "Total Paid out Trx", 
    "Avg Top 05 Daily Trx", "SD of Top 5 Trx_M", "SD of Top 5 Trx_N",
    "Avg top Volumes", "Std Dev Vol_M", "Std Dev Vol_N", 
    "Date Differences Max", "Date Differences Avg", "Length of Seq",
    "Avg Top 05 ATV", "Avg Bottom ATV", "Std Dev ATV", 
    "Date Differences Avg", "Date Differences Max", "Paid %", 
    "SD Trx Diff", "SD Trx Vol"
]

# Load StandardScaler if used during training
# SCALER_FILE = os.path.join(os.path.dirname(__file__), '../../scaler.pkl')
# if os.path.exists(SCALER_FILE):
#     scaler = joblib.load(SCALER_FILE)
#     print("✅ Scaler loaded successfully.")
# else:
#     scaler = None
#     print("⚠️ WARNING: Scaler file not found. Prediction may be affected.")

@predict_bp.route('/predict', methods=['POST'])
def predict():
    try:
        # Check if model is loaded
        if model is None:
            return jsonify({'error': 'Model not found. Please check the model file path.'}), 500

        # Parse input JSON
        data = request.get_json(force=True)

        # Extract transaction details
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

        # Save transaction to DB
        db.session.add(transaction)
        db.session.commit()

        # Extract features in the correct order
        features = [data.get(feature, 0) for feature in FEATURES]  # Default missing features to 0
        features_array = np.array(features).reshape(1, -1)

        # Apply scaling if scaler was used during training
        # if scaler:
        #     features_array = scaler.transform(features_array)

        # Predict using the model
        prediction = model.predict(features_array)
        predicted_label = int(prediction[0])  # Convert prediction result to integer

        # Map prediction output to human-readable format
        label_map = {0: "Genuine", 1: "Suspicious"}
        predicted_status = label_map.get(predicted_label, "Unknown")

        # Update transaction with prediction result
        transaction.status = f"Predicted: {predicted_status}"
        transaction.sender_status_detail = f"Auto-assigned status based on prediction: {predicted_status}"
        db.session.commit()

        # Create notification for the user
        notification = Notification(
            user_id="123",  # Replace with actual user ID
            message=f"New transaction added. Predicted category: {predicted_status}",
            transaction_id=transaction.id
        )
        db.session.add(notification)
        db.session.commit()

        # Emit real-time notification
        emit("new_transaction", {
            "message": f"New transaction added. Predicted category: {predicted_status}",
            "transaction_id": transaction.id
        }, broadcast=True, namespace="/")

        return jsonify({
            "message": "Transaction added and predicted successfully.",
            "transaction_id": transaction.id,
            "predicted_label": predicted_status
        }), 201

    except Exception as e:
        db.session.rollback()  # Rollback any failed DB transactions
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
