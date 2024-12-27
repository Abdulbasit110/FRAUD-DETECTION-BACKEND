from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from ..models import Transaction
from ..database import db
from ..utils.helpers import parse_date, clean_numeric
import pandas as pd
import os

transaction_routes = Blueprint("transactions", __name__)

@transaction_routes.route("/upload", methods=["POST"])
def upload_transactions():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    if not file.filename.endswith(".csv"):
        return jsonify({"error": "Invalid file type. Please upload a CSV file."}), 400

    try:
        df = pd.read_csv(file)

        # Clean and validate data
        cleaned_data, skipped_rows = clean_transaction_data(df)

        # Insert cleaned data into the database
        for row in cleaned_data:
            transaction = Transaction(**row)
            db.session.add(transaction)

        # Commit valid rows
        db.session.commit()

        return jsonify({
            "message": "Transactions uploaded successfully",
            "skipped_rows": skipped_rows
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@transaction_routes.route("/upload-local", methods=["POST"])
def upload_local_transactions():
    data = request.json
    if "file_path" not in data:
        return jsonify({"error": "File path not provided"}), 400

    file_path = data["file_path"]

    if not os.path.exists(file_path):
        return jsonify({"error": "File does not exist"}), 404
    if not file_path.endswith(".csv"):
        return jsonify({"error": "Invalid file type. Please provide a CSV file."}), 400

    try:
        df = pd.read_csv(file_path)

        # Clean and validate data
        cleaned_data, skipped_rows = clean_transaction_data(df)

        # Insert cleaned data into the database
        for row in cleaned_data:
            transaction = Transaction(**row)
            db.session.add(transaction)

        # Commit valid rows
        db.session.commit()

        return jsonify({
            "message": "Local transactions uploaded successfully",
            "skipped_rows": skipped_rows
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def clean_transaction_data(df):
    """
    Cleans and validates transaction data.
    Returns cleaned data and a list of skipped rows with reasons.
    """
    cleaned_rows = []
    skipped_rows = []

    for index, row in df.iterrows():
        try:
            # Validate and clean individual fields
            totalsale = clean_numeric(row.get("TOTALSALE"), default=None)
            payer_repcode = clean_numeric(row.get("PAYER_REPCODE"), default=None)
            sender_mobile = clean_numeric(row.get("SENDER_MOBILE"), default=None)
            beneficiary_mobile = clean_numeric(row.get("BENEFICIARY_MOBILE"), default=None)
            beneficiary_clientid = clean_numeric(row.get("BENEFICIARY_CLIENTID"), default=None)

            # Skip row if critical fields are invalid
            if totalsale is None or payer_repcode is None:
                skipped_rows.append({"index": index, "reason": "Invalid numeric values"})
                continue

            # Append cleaned data
            cleaned_rows.append({
                "sending_date": parse_date(row.get("SENDINGDATE")),
                "mtn": row.get("MTN"),
                "sender_id": row.get("SENDER_ID"),
                "sender_legalname": row.get("SENDER_LEGALNAME"),
                "channel": row.get("CHANNEL"),
                "payer_repcode": payer_repcode,
                "sender_country": row.get("SENDER_COUNTRY"),
                "sender_status": row.get("SENDER_STATUS"),
                "sender_dob": parse_date(row.get("SENDER_DATEOFBIRTH")),
                "sender_email": row.get("SENDER_EMAIL"),
                "sender_mobile": sender_mobile,
                "sender_phone": row.get("SENDER_PHONE"),
                "beneficiary_clientid": beneficiary_clientid,
                "beneficiary_name": row.get("BENEFICIARY_NAME"),
                "beneficiary_firstname": row.get("BENEFICIARY_FIRSTNAME"),
                "beneficiary_country": row.get("BENEFICIARY_COUNTRY"),
                "beneficiary_email": row.get("BENEFICIARY_EMAIL"),
                "beneficiary_mobile": beneficiary_mobile,
                "beneficiary_phone": row.get("BENEFICIARY_PHONE"),
                "sending_country": row.get("SENDING_COUNTRY"),
                "payout_country": row.get("PAYOUTCOUNTRY"),
                "status": row.get("STATUS"),
                "totalsale": totalsale,
                "sending_currency": row.get("SENDINGCURRENCY"),
                "payment_method": row.get("PAYMENTMETHOD"),
                "compliance_release_date": parse_date(row.get("COMPLIANCERELEASEDATE")),
                "sender_status_extra": row.get("Sender_Status"),
            })

        except Exception as e:
            skipped_rows.append({"index": index, "reason": str(e)})

    return cleaned_rows, skipped_rows
