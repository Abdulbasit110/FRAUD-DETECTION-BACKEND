from flask import Blueprint, request, jsonify,Response,stream_with_context
from ..models import Transaction, Notification
from ..database import db
import pandas as pd
import os
import json
from sqlalchemy import func
from datetime import datetime, date

transaction_routes = Blueprint("transactions", __name__)

# POST: Upload transactions from a file
@transaction_routes.route("/upload", methods=["POST"])
def upload_transactions():
    try:
        # Check if a file is provided
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file provided"}), 400
        if not file.filename.endswith(".csv"):
            return jsonify({"error": "Invalid file type. Please upload a CSV file."}), 400

        # Read the CSV file into a DataFrame
        df = pd.read_csv(file)

        # Validate and clean the data
        cleaned_data, skipped_rows = clean_transaction_data(df)

        # Bulk insert cleaned data into the database
        transactions = [Transaction(**row) for row in cleaned_data]
        db.session.bulk_save_objects(transactions)
        db.session.commit()

        return jsonify({
            "message": "Transactions uploaded successfully.",
            "skipped_rows": skipped_rows
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@transaction_routes.route("/upload-local", methods=["POST"])
def upload_local_transactions():
    try:
        # Get the file path from the request JSON
        data = request.json
        file_path = data.get("file_path")

        if not file_path:
            return jsonify({"error": "File path not provided"}), 400
        if not os.path.exists(file_path):
            return jsonify({"error": "File does not exist"}), 404
        if not file_path.endswith(".csv"):
            return jsonify({"error": "Invalid file type. Please provide a CSV file."}), 400

        # Load the CSV file into a Pandas DataFrame
        df = pd.read_csv(file_path)

        # Clean and validate the data
        cleaned_data, skipped_rows = clean_transaction_data(df)

        # Bulk insert cleaned data into the database
        transactions = [Transaction(**row) for row in cleaned_data]
        db.session.bulk_save_objects(transactions)
        db.session.commit()

        return jsonify({
            "message": "Local transactions uploaded successfully.",
            "skipped_rows": skipped_rows
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# GET: Fetch all transactions
@transaction_routes.route("/all", methods=["GET"])
def get_all_transactions():
    try:
        # Get the 'limit' parameter from the query string
        limit = request.args.get('limit', default=10, type=int)  # Default to 10 records if no argument is provided
        
        # Query the database and limit the results
        # transactions = Transaction.query.all()
        transactions = Transaction.query.limit(limit).all()
        
        # Serialize the results
        result = [transaction.to_dict() for transaction in transactions]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# GET: Fetch paginated transactions
@transaction_routes.route("/all_page", methods=["GET"])
def get_all_page_transactions():
    try:
        # Get pagination parameters
        page = request.args.get('page', default=1, type=int)  # Default to page 1
        per_page = request.args.get('per_page', default=100, type=int)  # Default 100 records per page
        
        # Query the database with pagination
        transactions = Transaction.query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Serialize results
        result = [transaction.to_dict() for transaction in transactions.items]
        
        return jsonify({
            "total": transactions.total,
            "page": transactions.page,
            "per_page": transactions.per_page,
            "transactions": result
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def json_serial(obj):
    """JSON serializer for objects not serializable by default"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

@transaction_routes.route("/all_stream", methods=["GET"])
def stream_transactions():
    def generate():
        query = Transaction.query.yield_per(500)  # Fetch 500 rows at a time
        for transaction in query:
            yield json.dumps(transaction.to_dict(), default=json_serial) + "\n"
    
    return Response(stream_with_context(generate()), content_type="application/json")

# GET : transaction by id
@transaction_routes.route("/<int:transaction_id>", methods=["GET"])
def get_transaction_by_id(transaction_id):
    try:
        # Fetch the transaction by ID
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return jsonify({"error": "Transaction not found"}), 404

        # Use the to_dict method for serialization
        result = transaction.to_dict()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@transaction_routes.route("/by-date", methods=["GET"])
def get_transactions_by_date():
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        if not start_date or not end_date:
            return jsonify({"error": "Start date and end date are required"}), 400

        transactions = Transaction.query.filter(
            Transaction.sending_date.between(start_date, end_date)
        ).all()

        return jsonify([t.to_dict() for t in transactions]), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@transaction_routes.route("/by-sender", methods=["GET"])
def get_transactions_by_sender():
    try:
        sender_id = request.args.get("sender_id")

        if not sender_id:
            return jsonify({"error": "Sender ID is required"}), 400

        transactions = Transaction.query.filter_by(sender_id=sender_id).all()

        return jsonify([t.to_dict() for t in transactions]), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@transaction_routes.route("/by-beneficiary", methods=["GET"])
def get_transactions_by_beneficiary():
    try:
        beneficiary_id = request.args.get("beneficiary_id")

        if not beneficiary_id:
            return jsonify({"error": "Beneficiary ID is required"}), 400

        transactions = Transaction.query.filter_by(beneficiary_client_id=beneficiary_id).all()

        return jsonify([t.to_dict() for t in transactions]), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@transaction_routes.route("/sales-summary", methods=["GET"])
def get_sales_summary():
    try:
        total_sales = db.session.query(func.sum(Transaction.total_sale)).scalar() or 0

        return jsonify({"total_sales": total_sales}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@transaction_routes.route("/by-status", methods=["GET"])
def get_transactions_by_status():
    try:
        status = request.args.get("status")

        if not status:
            return jsonify({"error": "Status is required"}), 400

        transactions = Transaction.query.filter_by(status=status).all()

        return jsonify([t.to_dict() for t in transactions]), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@transaction_routes.route("/stats", methods=["GET"])
def get_transaction_stats():
    try:
        total_transactions = Transaction.query.count()
        genuine_transactions = Transaction.query.filter(Transaction.sender_status_detail == "Genuine").count()
        suspicious_transactions = Transaction.query.filter(Transaction.sender_status_detail == "Suspicious").count()
        
        # Calculate total transaction volume
        total_volume = db.session.query(func.sum(Transaction.total_sale)).scalar() or 0
        genuine_volume = db.session.query(func.sum(Transaction.total_sale)).filter(
            Transaction.sender_status_detail == "Genuine").scalar() or 0
        suspicious_volume = db.session.query(func.sum(Transaction.total_sale)).filter(
            Transaction.sender_status_detail == "Suspicious").scalar() or 0

        return jsonify({
            "total_transactions": total_transactions,
            "genuine_transactions": genuine_transactions,
            "suspicious_transactions": suspicious_transactions,
            "total_volume": total_volume,
            "genuine_volume": genuine_volume,
            "suspicious_volume": suspicious_volume
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@transaction_routes.route("/create", methods=["POST"])
def create_transaction():
    try:
        data = request.get_json()

        # Create new transaction
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
            status=data.get("status", "Pending"),
            total_sale=data.get("total_sale"),
            sending_currency=data.get("sending_currency"),
            payment_method=data.get("payment_method"),
            compliance_release_date=data.get("compliance_release_date"),
            sender_status_detail=data.get("sender_status_detail")
        )

        db.session.add(transaction)
        db.session.commit()

        return jsonify({
            "message": "Transaction created successfully",
            "transaction": transaction.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
# Function to clean transaction data
def clean_transaction_data(df):
    cleaned_data = []
    skipped_rows = []

    for index, row in df.iterrows():
        try:
            # Perform any necessary validation and cleaning
            cleaned_row = {
                "sending_date": row["SENDINGDATE"],
                "mtn": row["MTN"],
                "sender_id": row["SENDER_ID"],
                "sender_legal_name": row["SENDER_LEGALNAME"],
                "channel": row["CHANNEL"],
                "payer_rep_code": row["PAYER_REPCODE"],
                "sender_country": row["SENDER_COUNTRY"],
                "sender_status": row["SENDER_STATUS"],
                "sender_date_of_birth": row["SENDER_DATEOFBIRTH"],
                "sender_email": row["SENDER_EMAIL"],
                "sender_mobile": row["SENDER_MOBILE"],
                "sender_phone": row["SENDER_PHONE"],
                "beneficiary_client_id": row["BENEFICIARY_CLIENTID"],
                "beneficiary_name": row["BENEFICIARY_NAME"],
                "beneficiary_first_name": row["BENEFICIARY_FIRSTNAME"],
                "beneficiary_country": row["BENEFICIARY_COUNTRY"],
                "beneficiary_email": row["BENEFICIARY_EMAIL"],
                "beneficiary_mobile": row["BENEFICIARY_MOBILE"],
                "beneficiary_phone": row["BENEFICIARY_PHONE"],
                "sending_country": row["SENDING_COUNTRY"],
                "payout_country": row["PAYOUTCOUNTRY"],
                "status": row["STATUS"],
                "total_sale": row["TOTALSALE"],
                "sending_currency": row["SENDINGCURRENCY"],
                "payment_method": row["PAYMENTMETHOD"],
                "compliance_release_date": row["COMPLIANCERELEASEDATE"],
                "sender_status_detail": row.get("Sender_Status", None),
            }
            cleaned_data.append(cleaned_row)
        except Exception as e:
            skipped_rows.append({"index": index, "error": str(e)})

    return cleaned_data, skipped_rows

@transaction_routes.route("/notifications", methods=["GET"])
def get_all_notifications():
    try:
        # Get pagination parameters
        page = request.args.get('page', default=1, type=int)  # Default to page 1
        per_page = request.args.get('per_page', default=20, type=int)  # Default 20 records per page
        user_id = request.args.get('user_id')  # Optional user_id filter
        
        # Base query
        query = Notification.query
        
        # Apply user_id filter if provided
        if user_id:
            query = query.filter_by(user_id=user_id)
            
        # Order by creation date, newest first
        query = query.order_by(Notification.created_at.desc())
        
        # Apply pagination
        notifications = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Serialize results
        result = [notification.to_dict() for notification in notifications.items]
        
        return jsonify({
            "total": notifications.total,
            "page": notifications.page,
            "per_page": notifications.per_page,
            "notifications": result
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@transaction_routes.route("/notifications/<int:notification_id>", methods=["GET"])
def get_notification_by_id(notification_id):
    try:
        # Fetch the notification by ID
        notification = Notification.query.get(notification_id)
        if not notification:
            return jsonify({"error": "Notification not found"}), 404

        # Use the to_dict method for serialization
        result = notification.to_dict()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@transaction_routes.route("/notifications/mark-read/<int:notification_id>", methods=["PUT"])
def mark_notification_read(notification_id):
    try:
        # Fetch the notification by ID
        notification = Notification.query.get(notification_id)
        if not notification:
            return jsonify({"error": "Notification not found"}), 404

        # Mark as read
        notification.is_read = True
        db.session.commit()

        return jsonify({"message": "Notification marked as read"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

