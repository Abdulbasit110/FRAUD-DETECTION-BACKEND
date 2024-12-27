from .database import db
from sqlalchemy.sql import func

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    sending_date = db.Column(db.DateTime, nullable=True)
    mtn = db.Column(db.String(50), nullable=True)  # Keep this as string if MTN contains alphanumeric data
    sender_id = db.Column(db.String(50), nullable=True)  # Change to string if IDs can contain non-numeric data
    sender_legalname = db.Column(db.String(200), nullable=True)
    channel = db.Column(db.String(100), nullable=True)
    payer_repcode = db.Column(db.String(50), nullable=True)  # Change to string if it contains non-numeric data
    sender_country = db.Column(db.String(100), nullable=True)
    sender_status = db.Column(db.String(50), nullable=True)  # Change to string to accept statuses like "Approved"
    sender_dob = db.Column(db.DateTime, nullable=True)
    sender_email = db.Column(db.String(120), nullable=True)
    sender_mobile = db.Column(db.String(20), nullable=True)  # Change to string if phone numbers have leading zeros
    sender_phone = db.Column(db.String(20), nullable=True)
    beneficiary_clientid = db.Column(db.String(50), nullable=True)  # Change to string if IDs can contain non-numeric data
    beneficiary_name = db.Column(db.String(200), nullable=True)
    beneficiary_firstname = db.Column(db.String(100), nullable=True)
    beneficiary_country = db.Column(db.String(100), nullable=True)
    beneficiary_email = db.Column(db.String(120), nullable=True)
    beneficiary_mobile = db.Column(db.String(20), nullable=True)
    beneficiary_phone = db.Column(db.String(20), nullable=True)
    sending_country = db.Column(db.String(100), nullable=True)
    payout_country = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), nullable=True)  # Change to string to accept statuses like "Paid Out"
    totalsale = db.Column(db.Float, nullable=True)  # Keep as float for monetary values
    sending_currency = db.Column(db.String(10), nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    compliance_release_date = db.Column(db.DateTime, nullable=True)
    sender_status_extra = db.Column(db.String(50), nullable=True)
