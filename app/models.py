from .database import db
from sqlalchemy.sql import func
from datetime import timedelta


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="user")  # Role field with a default value
    is_approved = db.Column(db.Boolean, nullable=False, default=False)  # Approval status with default False
    verification_code = db.Column(db.String(6), nullable=True)
    verification_code_expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at,
        }


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    sending_date = db.Column(db.DateTime, nullable=True)
    mtn = db.Column(db.String(50), nullable=True)
    sender_id = db.Column(db.String(50), nullable=True)
    sender_legal_name = db.Column(db.String(200), nullable=True)
    channel = db.Column(db.String(100), nullable=True)
    payer_rep_code = db.Column(db.String(50), nullable=True)
    sender_country = db.Column(db.String(100), nullable=True)
    sender_status = db.Column(db.String(50), nullable=True)
    sender_date_of_birth = db.Column(db.DateTime, nullable=True)
    sender_email = db.Column(db.String(120), nullable=True)
    sender_mobile = db.Column(db.String(20), nullable=True)
    sender_phone = db.Column(db.String(20), nullable=True)
    beneficiary_client_id = db.Column(db.String(50), nullable=True)
    beneficiary_name = db.Column(db.String(200), nullable=True)
    beneficiary_first_name = db.Column(db.String(100), nullable=True)
    beneficiary_country = db.Column(db.String(100), nullable=True)
    beneficiary_email = db.Column(db.String(120), nullable=True)
    beneficiary_mobile = db.Column(db.String(20), nullable=True)
    beneficiary_phone = db.Column(db.String(20), nullable=True)
    sending_country = db.Column(db.String(100), nullable=True)
    payout_country = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(255), nullable=True)
    total_sale = db.Column(db.Float, nullable=True)
    sending_currency = db.Column(db.String(10), nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    compliance_release_date = db.Column(db.DateTime, nullable=True)
    sender_status_detail = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    user_id = db.Column(db.String, nullable=False)  # User ID to whom the notification belongs
    message = db.Column(db.String(255), nullable=False)  # Notification message
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=True)  # Related transaction
    sender_name = db.Column(db.String(200), nullable=True)  # Name of the sender
    mobile_number = db.Column(db.String(20), nullable=True)  # Mobile number of the sender
    amount = db.Column(db.Float, nullable=True)  # Transaction amount
    status = db.Column(db.String(50), nullable=True)  # Status of the transaction
    high_alert_date = db.Column(db.DateTime, nullable=True)  # Date when high alert was triggered
    created_at = db.Column(db.DateTime, default=func.now())  # Timestamp for the notification
    is_read = db.Column(db.Boolean, default=False)  # Whether the notification has been read

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "message": self.message,
            "transaction_id": self.transaction_id,
            "sender_name": self.sender_name,
            "mobile_number": self.mobile_number,
            "amount": self.amount,
            "status": self.status,
            "high_alert_date": self.high_alert_date,
            "created_at": self.created_at,
            "is_read": self.is_read,
        }

class ModelParams(db.Model):
    __tablename__ = 'model_params'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    spiking_duration = db.Column(db.Interval, nullable=False)
    accuracy = db.Column(db.Float, nullable=False)
    precision = db.Column(db.Float, nullable=False)
    recall = db.Column(db.Float, nullable=False)
    f1_score = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "start_date": self.start_date.isoformat(),  # Convert datetime to string
            "end_date": self.end_date.isoformat(),  # Convert datetime to string
            "spiking_duration": str(self.spiking_duration),  # Convert timedelta to string
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "created_at": self.created_at.isoformat(),  # Convert datetime to string
        }

class SenderFeatures(db.Model):
    __tablename__ = 'sender_features'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.String(50), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    # Transaction count features
    total_trx = db.Column(db.Integer, nullable=False)
    total_beneficiaries = db.Column(db.Integer, nullable=False)
    total_paid_out_trx = db.Column(db.Integer, nullable=False)
    
    # Transaction frequency features
    avg_top_05_daily_trx = db.Column(db.Float, nullable=False)
    sd_of_top_5_trx_m = db.Column(db.Float, nullable=False)
    sd_of_top_5_trx_n = db.Column(db.Float, nullable=False)
    
    # Volume features
    avg_top_volumes = db.Column(db.Float, nullable=False)
    std_dev_vol_m = db.Column(db.Float, nullable=False)
    std_dev_vol_n = db.Column(db.Float, nullable=False)
    
    # Date difference features
    date_differences_max = db.Column(db.Float, nullable=False)
    date_differences_avg = db.Column(db.Float, nullable=False)
    
    # Sequence length
    length_of_seq = db.Column(db.Integer, nullable=False)
    
    # Transaction value features
    avg_top_05_atv = db.Column(db.Float, nullable=False)
    avg_bottom_atv = db.Column(db.Float, nullable=False)
    std_dev_atv = db.Column(db.Float, nullable=False)
    
    # Paid percentage
    paid_percentage = db.Column(db.Float, nullable=False)
    
    # Standard deviation features
    sd_trx_diff = db.Column(db.Float, nullable=False)
    sd_trx_vol = db.Column(db.Float, nullable=False)
    
    def to_dict(self):
        return {
            "sender_id": self.sender_id,
            "Total Trx": self.total_trx,
            "Total Beneficiaries": self.total_beneficiaries,
            "Total Paid out Trx": self.total_paid_out_trx,
            "Avg Top 05 Daily Trx": self.avg_top_05_daily_trx,
            "SD of Top 5 Trx_M": self.sd_of_top_5_trx_m,
            "SD of Top 5 Trx_N": self.sd_of_top_5_trx_n,
            "Avg top Volumes": self.avg_top_volumes,
            "Std Dev Vol_M": self.std_dev_vol_m,
            "Std Dev Vol_N": self.std_dev_vol_n,
            "Date Differences Max": self.date_differences_max,
            "Date Differences Avg": self.date_differences_avg,
            "Length of Seq": self.length_of_seq,
            "Avg Top 05 ATV": self.avg_top_05_atv,
            "Avg Bottom ATV": self.avg_bottom_atv,
            "Std Dev ATV": self.std_dev_atv,
            "Paid %": self.paid_percentage,
            "SD Trx Diff": self.sd_trx_diff,
            "SD Trx Vol": self.sd_trx_vol,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
