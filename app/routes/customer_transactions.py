from flask import Blueprint, request, jsonify
from ..models import CustomerTransaction, Notification
from ..database import db
from sqlalchemy import func
from datetime import datetime, date

customer_transaction_routes = Blueprint("customer_transactions", __name__)

@customer_transaction_routes.route("/stats", methods=["GET"])
def get_customer_transaction_stats():
    """Get statistics for live customer transactions only"""
    try:
        total_transactions = CustomerTransaction.query.count()
        genuine_transactions = CustomerTransaction.query.filter(CustomerTransaction.sender_status_detail == "Genuine").count()
        suspicious_transactions = CustomerTransaction.query.filter(CustomerTransaction.sender_status_detail == "Suspicious").count()
        
        # Calculate unique customers (using customer_id as primary identifier)
        total_customers = db.session.query(CustomerTransaction.customer_id).distinct().count()
        
        # Calculate pure genuine customers (customers with ONLY genuine transactions)
        genuine_only_customers = db.session.query(CustomerTransaction.customer_id).filter(
            CustomerTransaction.sender_status_detail == "Genuine"
        ).distinct().except_(
            db.session.query(CustomerTransaction.customer_id).filter(
                CustomerTransaction.sender_status_detail == "Suspicious"
            ).distinct()
        ).count()
        
        # Calculate pure suspicious customers (customers with ONLY suspicious transactions)
        suspicious_only_customers = db.session.query(CustomerTransaction.customer_id).filter(
            CustomerTransaction.sender_status_detail == "Suspicious"
        ).distinct().except_(
            db.session.query(CustomerTransaction.customer_id).filter(
                CustomerTransaction.sender_status_detail == "Genuine"
            ).distinct()
        ).count()
        
        # Calculate mixed customers (customers with both genuine and suspicious transactions)
        mixed_customers = total_customers - genuine_only_customers - suspicious_only_customers
        
        # Calculate total transaction volume
        total_volume = db.session.query(func.sum(CustomerTransaction.total_sale)).scalar() or 0
        genuine_volume = db.session.query(func.sum(CustomerTransaction.total_sale)).filter(
            CustomerTransaction.sender_status_detail == "Genuine").scalar() or 0
        suspicious_volume = db.session.query(func.sum(CustomerTransaction.total_sale)).filter(
            CustomerTransaction.sender_status_detail == "Suspicious").scalar() or 0

        return jsonify({
            "total_transactions": total_transactions,
            "total_customers": total_customers,
            "genuine_transactions": genuine_transactions,
            "suspicious_transactions": suspicious_transactions,
            "genuine_customers": genuine_only_customers,
            "suspicious_customers": suspicious_only_customers,
            "mixed_customers": mixed_customers,
            "total_volume": total_volume,
            "genuine_volume": genuine_volume,
            "suspicious_volume": suspicious_volume,
            "data_source": "live_customer_transactions"  # Indicator that this is live data
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@customer_transaction_routes.route("/all", methods=["GET"])
def get_all_customer_transactions():
    """Get all customer transactions with pagination"""
    try:
        # Get pagination parameters
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=50, type=int)
        
        # Query the database with pagination
        transactions = CustomerTransaction.query.order_by(
            CustomerTransaction.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        # Serialize results
        result = [transaction.to_dict_with_metadata() for transaction in transactions.items]
        
        return jsonify({
            "total": transactions.total,
            "page": transactions.page,
            "per_page": transactions.per_page,
            "total_pages": transactions.pages,
            "transactions": result,
            "data_source": "live_customer_transactions"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@customer_transaction_routes.route("/by-date", methods=["GET"])
def get_customer_transactions_by_date():
    """Get customer transactions by date range"""
    try:
        # Get date range parameters
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        if not start_date or not end_date:
            return jsonify({"error": "Start date and end date are required"}), 400

        # Get pagination parameters
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=50, type=int)
        
        # Build the query with date filter
        query = CustomerTransaction.query.filter(
            CustomerTransaction.sending_date.between(start_date, end_date)
        )
        
        # Add sorting for consistent pagination
        query = query.order_by(CustomerTransaction.sending_date.desc(), CustomerTransaction.id.desc())
        
        # Apply pagination
        paginated_transactions = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Serialize the paginated results
        results = [t.to_dict_with_metadata() for t in paginated_transactions.items]
        
        return jsonify({
            "total": paginated_transactions.total,
            "page": page,
            "per_page": per_page,
            "total_pages": paginated_transactions.pages,
            "transactions": results,
            "data_source": "live_customer_transactions"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@customer_transaction_routes.route("/by-customer", methods=["GET"])
def get_transactions_by_customer():
    """Get transactions by customer ID"""
    try:
        customer_id = request.args.get("customer_id")

        if not customer_id:
            return jsonify({"error": "Customer ID is required"}), 400

        # Get pagination parameters
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=50, type=int)
        
        # Build the query with customer filter
        query = CustomerTransaction.query.filter_by(customer_id=customer_id)
        
        # Add sorting for consistent pagination
        query = query.order_by(CustomerTransaction.sending_date.desc(), CustomerTransaction.id.desc())
        
        # Apply pagination
        paginated_transactions = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Serialize the paginated results
        results = [t.to_dict_with_metadata() for t in paginated_transactions.items]
        
        return jsonify({
            "total": paginated_transactions.total,
            "page": page,
            "per_page": per_page,
            "total_pages": paginated_transactions.pages,
            "transactions": results,
            "customer_id": customer_id,
            "data_source": "live_customer_transactions"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@customer_transaction_routes.route("/create", methods=["POST"])
def create_customer_transaction():
    """Create a new customer transaction with prediction"""
    try:
        data = request.get_json()

        # Create new customer transaction
        transaction = CustomerTransaction(
            customer_id=data.get("customer_id"),
            session_id=data.get("session_id"),
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
            sender_status_detail=data.get("sender_status_detail"),
            prediction_confidence=data.get("prediction_confidence"),
            model_version=data.get("model_version", "1.0"),
            risk_score=data.get("risk_score"),
            risk_factors=data.get("risk_factors")
        )

        db.session.add(transaction)
        db.session.commit()

        return jsonify({
            "message": "Customer transaction created successfully",
            "transaction": transaction.to_dict_with_metadata()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@customer_transaction_routes.route("/flagged", methods=["GET"])
def get_flagged_transactions():
    """Get all flagged transactions requiring review"""
    try:
        # Get pagination parameters
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=50, type=int)
        
        # Query flagged transactions
        query = CustomerTransaction.query.filter_by(is_flagged=True)
        query = query.order_by(CustomerTransaction.created_at.desc())
        
        # Apply pagination
        paginated_transactions = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Serialize results
        results = [t.to_dict_with_metadata() for t in paginated_transactions.items]
        
        return jsonify({
            "total": paginated_transactions.total,
            "page": page,
            "per_page": per_page,
            "total_pages": paginated_transactions.pages,
            "transactions": results,
            "data_source": "flagged_customer_transactions"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@customer_transaction_routes.route("/review/<int:transaction_id>", methods=["PUT"])
def review_transaction(transaction_id):
    """Review a flagged transaction"""
    try:
        data = request.get_json()
        
        transaction = CustomerTransaction.query.get(transaction_id)
        if not transaction:
            return jsonify({"error": "Transaction not found"}), 404

        # Update review fields
        transaction.review_status = data.get("review_status", "approved")
        transaction.reviewed_by = data.get("reviewed_by")
        transaction.reviewed_at = datetime.utcnow()
        transaction.is_flagged = False  # Remove flag after review

        db.session.commit()

        return jsonify({
            "message": "Transaction reviewed successfully",
            "transaction": transaction.to_dict_with_metadata()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
