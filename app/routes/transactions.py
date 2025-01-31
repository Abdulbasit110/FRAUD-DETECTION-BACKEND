from flask import Blueprint, request, jsonify
from ..models import Transaction
from ..database import db
import pandas as pd
import os

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
        transactions = Transaction.query.limit(limit).all()
        
        # Serialize the results
        result = [transaction.to_dict() for transaction in transactions]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
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

