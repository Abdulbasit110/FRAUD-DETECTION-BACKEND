from flask import Blueprint, request, jsonify
import joblib
import numpy as np
import os
import pandas as pd
from flask_socketio import emit
from sqlalchemy.orm.exc import NoResultFound
from app import db, socketio
from app.models import Transaction, Notification, User, SenderFeatures
from datetime import datetime, timedelta
from sqlalchemy import func

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

def extract_features_for_sender(sender_id):
    """
    Perform feature engineering on transactions for a specific sender_id
    Returns a dictionary of features needed for model prediction
    Also stores the features in the database for future use
    """
    # Get all transactions for this sender
    transactions = Transaction.query.filter_by(sender_id=sender_id).all()
    
    if not transactions:
        return None
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame([t.to_dict() for t in transactions])
    
    # Convert date strings to datetime objects
    df['sending_date'] = pd.to_datetime(df['sending_date'])
    
    # Sort by date
    df = df.sort_values('sending_date')
    
    # Calculate features
    features = {}
    
    # Basic count features
    features["Total Trx"] = len(df)
    features["Total Beneficiaries"] = df['beneficiary_client_id'].nunique()
    features["Total Paid out Trx"] = len(df[df['status'] == 'Paid'])
    
    # Transaction frequency features
    if len(df) >= 5:
        # Daily transaction counts
        df['date'] = df['sending_date'].dt.date
        daily_counts = df.groupby('date').size()
        top_5_daily = daily_counts.nlargest(5)
        features["Avg Top 05 Daily Trx"] = top_5_daily.mean()
        
        # Standard deviation of top 5 transactions
        features["SD of Top 5 Trx_M"] = top_5_daily.std() if len(top_5_daily) > 1 else 0
        features["SD of Top 5 Trx_N"] = np.std(top_5_daily) if len(top_5_daily) > 1 else 0
    else:
        features["Avg Top 05 Daily Trx"] = 1
        features["SD of Top 5 Trx_M"] = 0
        features["SD of Top 5 Trx_N"] = 0
    
    # Volume features
    if 'total_sale' in df.columns:
        volumes = df['total_sale']
        top_volumes = volumes.nlargest(5)
        features["Avg top Volumes"] = top_volumes.mean() if not top_volumes.empty else 0
        features["Std Dev Vol_M"] = volumes.std() if len(volumes) > 1 else 0
        features["Std Dev Vol_N"] = np.std(volumes) if len(volumes) > 1 else 0
    else:
        features["Avg top Volumes"] = 0
        features["Std Dev Vol_M"] = 0
        features["Std Dev Vol_N"] = 0
    
    # Date difference features
    if len(df) > 1:
        date_diffs = []
        sorted_dates = sorted(df['sending_date'])
        for i in range(1, len(sorted_dates)):
            diff = (sorted_dates[i] - sorted_dates[i-1]).days
            date_diffs.append(diff)
        
        features["Date Differences Max"] = max(date_diffs) if date_diffs else 0
        features["Date Differences Avg"] = sum(date_diffs) / len(date_diffs) if date_diffs else 0
    else:
        features["Date Differences Max"] = 0
        features["Date Differences Avg"] = 0
    
    # Sequence length
    features["Length of Seq"] = len(df)
    
    # Average Transaction Value features
    if 'total_sale' in df.columns and len(df) >= 5:
        atv = df['total_sale']
        top_atv = atv.nlargest(5)
        bottom_atv = atv.nsmallest(5)
        
        features["Avg Top 05 ATV"] = top_atv.mean() if not top_atv.empty else 0
        features["Avg Bottom ATV"] = bottom_atv.mean() if not bottom_atv.empty else 0
        features["Std Dev ATV"] = atv.std() if len(atv) > 1 else 0
    else:
        features["Avg Top 05 ATV"] = 0
        features["Avg Bottom ATV"] = 0
        features["Std Dev ATV"] = 0
    
    # Paid percentage
    paid_count = len(df[df['status'] == 'Paid'])
    features["Paid %"] = (paid_count / len(df)) * 100 if len(df) > 0 else 0
    
    # Standard deviation of transaction differences
    if len(df) > 2:
        trx_diffs = []
        for i in range(1, len(df)):
            if 'total_sale' in df.columns:
                diff = abs(df.iloc[i]['total_sale'] - df.iloc[i-1]['total_sale'])
                trx_diffs.append(diff)
        
        features["SD Trx Diff"] = np.std(trx_diffs) if len(trx_diffs) > 1 else 0
    else:
        features["SD Trx Diff"] = 0
    
    # Standard deviation of transaction volumes
    if 'total_sale' in df.columns:
        features["SD Trx Vol"] = df['total_sale'].std() if len(df) > 1 else 0
    else:
        features["SD Trx Vol"] = 0
    
    # Store the features in the database
    try:
        print(f"[DEBUG] Storing features for sender ID: {sender_id}")
        
        # Convert NumPy values to native Python types
        db_features = {}
        for key, value in features.items():
            # Check if it's a NumPy type and convert to Python native type
            if hasattr(value, 'item'):
                db_features[key] = value.item()  # Convert NumPy types to native Python types
            else:
                db_features[key] = value
        
        # Check if we already have features for this sender
        existing_features = SenderFeatures.query.filter_by(sender_id=sender_id).first()
        
        if existing_features:
            # Update existing features
            print(f"[DEBUG] Updating existing features for sender ID: {sender_id}")
            existing_features.total_trx = db_features["Total Trx"]
            existing_features.total_beneficiaries = db_features["Total Beneficiaries"]
            existing_features.total_paid_out_trx = db_features["Total Paid out Trx"]
            existing_features.avg_top_05_daily_trx = db_features["Avg Top 05 Daily Trx"]
            existing_features.sd_of_top_5_trx_m = db_features["SD of Top 5 Trx_M"]
            existing_features.sd_of_top_5_trx_n = db_features["SD of Top 5 Trx_N"]
            existing_features.avg_top_volumes = db_features["Avg top Volumes"]
            existing_features.std_dev_vol_m = db_features["Std Dev Vol_M"]
            existing_features.std_dev_vol_n = db_features["Std Dev Vol_N"]
            existing_features.date_differences_max = db_features["Date Differences Max"]
            existing_features.date_differences_avg = db_features["Date Differences Avg"]
            existing_features.length_of_seq = db_features["Length of Seq"]
            existing_features.avg_top_05_atv = db_features["Avg Top 05 ATV"]
            existing_features.avg_bottom_atv = db_features["Avg Bottom ATV"]
            existing_features.std_dev_atv = db_features["Std Dev ATV"]
            existing_features.paid_percentage = db_features["Paid %"]
            existing_features.sd_trx_diff = db_features["SD Trx Diff"]
            existing_features.sd_trx_vol = db_features["SD Trx Vol"]
        else:
            # Create new features entry
            print(f"[DEBUG] Creating new features entry for sender ID: {sender_id}")
            sender_features = SenderFeatures(
                sender_id=sender_id,
                total_trx=db_features["Total Trx"],
                total_beneficiaries=db_features["Total Beneficiaries"],
                total_paid_out_trx=db_features["Total Paid out Trx"],
                avg_top_05_daily_trx=db_features["Avg Top 05 Daily Trx"],
                sd_of_top_5_trx_m=db_features["SD of Top 5 Trx_M"],
                sd_of_top_5_trx_n=db_features["SD of Top 5 Trx_N"],
                avg_top_volumes=db_features["Avg top Volumes"],
                std_dev_vol_m=db_features["Std Dev Vol_M"],
                std_dev_vol_n=db_features["Std Dev Vol_N"],
                date_differences_max=db_features["Date Differences Max"],
                date_differences_avg=db_features["Date Differences Avg"],
                length_of_seq=db_features["Length of Seq"],
                avg_top_05_atv=db_features["Avg Top 05 ATV"],
                avg_bottom_atv=db_features["Avg Bottom ATV"],
                std_dev_atv=db_features["Std Dev ATV"],
                paid_percentage=db_features["Paid %"],
                sd_trx_diff=db_features["SD Trx Diff"],
                sd_trx_vol=db_features["SD Trx Vol"]
            )
            db.session.add(sender_features)
        
        # Commit the changes
        db.session.commit()
        print(f"[DEBUG] Features successfully stored for sender ID: {sender_id}")
    except Exception as e:
        print(f"[ERROR] Failed to store features in the database: {str(e)}")
        db.session.rollback()
    
    return features

@predict_bp.route('/predict', methods=['POST'])
def predict():
    try:
        # Check if model is loaded
        if model is None:
            return jsonify({'error': 'Model not found. Please check the model file path.'}), 500

        print("[DEBUG] Starting prediction process...")
        
        # Parse input JSON for the transaction
        data = request.get_json(force=True)
        print(f"[DEBUG] Received transaction data: {data}")

        # Ensure user_id exists in the users table - COMMENTED OUT
        user_id = data.get("user_id")
        # user = User.query.filter_by(id=user_id).first()
        # if not user:
        #     return jsonify({'error': f'User with id {user_id} does not exist.'}), 400
        
        print(f"[DEBUG] Using user_id: {user_id}")

        # Create and store the new transaction first
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
        print("[DEBUG] Saving transaction to database...")
        db.session.add(transaction)
        db.session.commit()
        print(f"[DEBUG] Transaction saved with ID: {transaction.id}")

        # Get the sender_id to filter transactions
        sender_id = data.get("sender_id")
        print(f"[DEBUG] Extracting features for sender ID: {sender_id}")
        
        # Perform feature engineering on all transactions for this sender
        features_dict = extract_features_for_sender(sender_id)
        
        # If this is the first transaction, use default values for features
        if not features_dict:
            print("[DEBUG] First transaction for this sender, using default features")
            features_dict = {
                "Total Trx": 1,
                "Total Beneficiaries": 1,
                "Total Paid out Trx": 0,
                "Avg Top 05 Daily Trx": 1,
                "SD of Top 5 Trx_M": 0,
                "SD of Top 5 Trx_N": 0,
                "Avg top Volumes": float(data.get("total_sale", 0)),
                "Std Dev Vol_M": 0,
                "Std Dev Vol_N": 0,
                "Date Differences Max": 0,
                "Date Differences Avg": 0,
                "Length of Seq": 1,
                "Avg Top 05 ATV": float(data.get("total_sale", 0)),
                "Avg Bottom ATV": float(data.get("total_sale", 0)),
                "Std Dev ATV": 0,
                "Paid %": 0,
                "SD Trx Diff": 0,
                "SD Trx Vol": 0
            }
        else:
            print(f"[DEBUG] Extracted features: {features_dict}")
        
        # Create feature array in the correct order
        print("[DEBUG] Creating feature array for model prediction")
        features_array = np.array([features_dict.get(feature, 0) for feature in FEATURES]).reshape(1, -1)
        print(f"[DEBUG] Feature array shape: {features_array.shape}")
        
        # Predict using the model
        print("[DEBUG] Running model prediction...")
        prediction = model.predict(features_array)
        prediction_proba = model.predict_proba(features_array)[0]
        predicted_label = int(prediction[0])
        print(f"[DEBUG] Raw prediction: {prediction}, Probabilities: {prediction_proba}")
        
        # Map prediction output to human-readable format
        label_map = {0: "Genuine", 1: "Suspicious"}
        predicted_status = label_map.get(predicted_label, "Unknown")
        confidence = max(prediction_proba) * 100
        print(f"[DEBUG] Predicted status: {predicted_status}, Confidence: {confidence:.1f}%")
        
        # Update transaction with prediction result
        print("[DEBUG] Updating transaction with prediction result")
        transaction.status = f"Predicted: {predicted_status}"
        transaction.sender_status_detail = predicted_status
        db.session.commit()
        
        # Create notification for the user
        print("[DEBUG] Creating notification")
        notification = Notification(
            user_id=user_id,  # Use user_id directly without validation
            message=f"New transaction added. Predicted category: {predicted_status} (Confidence: {confidence:.1f}%)",
            transaction_id=transaction.id,
            sender_name=transaction.sender_legal_name,
            mobile_number=transaction.sender_mobile,
            amount=transaction.total_sale,
            status=predicted_status,
            high_alert_date=datetime.now() if predicted_status == "Suspicious" else None
        )
        db.session.add(notification)
        db.session.commit()
        
        # Emit real-time notification
        print("[DEBUG] Emitting real-time notification")
        emit("new_transaction", {
            "message": f"New transaction added. Predicted category: {predicted_status}",
            "transaction_id": transaction.id,
            "sender_name": transaction.sender_legal_name,
            "mobile_number": transaction.sender_mobile,
            "amount": transaction.total_sale,
            "status": predicted_status,
            "high_alert_date": datetime.now().isoformat() if predicted_status == "Suspicious" else None,
            "confidence": f"{confidence:.1f}%"
        }, broadcast=True, namespace="/")
        
        print("[DEBUG] Prediction process completed successfully")
        return jsonify({
            "message": "Transaction added and predicted successfully.",
            "transaction_id": transaction.id,
            "predicted_label": predicted_status,
            "confidence": f"{confidence:.1f}%",
            "features_used": features_dict
        }), 201

    except Exception as e:
        print(f"[ERROR] Exception in prediction process: {str(e)}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        db.session.rollback()  # Rollback any failed DB transactions
        return jsonify({'error': str(e)}), 500

@predict_bp.route('/ping', methods=['GET'])
def ping():
    """Check model status and return feature importance if available"""
    try:
        if model is None:
            return jsonify({'error': 'Model not found'}), 500
        return jsonify({'status': 'Model loaded', 'feature_importance': model.feature_importances_.tolist()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@predict_bp.route('/features', methods=['GET'])
def get_all_features():
    """
    Get all sender features from the database
    Returns a list of all features for all senders
    Supports filtering by time range (e.g., last 24 hours)
    """
    try:
        # Get time filter parameter (in hours, default to None for all features)
        hours = request.args.get('hours', type=int)
        
        # Start with base query
        query = SenderFeatures.query
        
        # Apply time filter if specified
        if hours is not None:
            from datetime import datetime, timedelta
            cutoff_time = datetime.now() - timedelta(hours=hours)
            # Filter by either created_at or updated_at within the time range
            query = query.filter(
                db.or_(
                    SenderFeatures.created_at >= cutoff_time,
                    SenderFeatures.updated_at >= cutoff_time
                )
            )
        
        # Order by most recent first
        query = query.order_by(SenderFeatures.updated_at.desc(), SenderFeatures.created_at.desc())
        
        features = query.all()
        return jsonify({
            "message": "Features retrieved successfully",
            "count": len(features),
            "time_filter_hours": hours,
            "features": [feature.to_dict() for feature in features]
        }), 200
    except Exception as e:
        print(f"[ERROR] Exception in retrieving features: {str(e)}")
        return jsonify({'error': str(e)}), 500

@predict_bp.route('/features/<sender_id>', methods=['GET'])
def get_sender_features(sender_id):
    """
    Get features for a specific sender from the database
    Returns the features for the requested sender ID
    """
    try:
        feature = SenderFeatures.query.filter_by(sender_id=sender_id).first()
        if not feature:
            return jsonify({
                "message": f"No features found for sender ID: {sender_id}",
                "features": None
            }), 404
        
        return jsonify({
            "message": "Features retrieved successfully",
            "features": feature.to_dict()
        }), 200
    except Exception as e:
        print(f"[ERROR] Exception in retrieving features for sender {sender_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500
