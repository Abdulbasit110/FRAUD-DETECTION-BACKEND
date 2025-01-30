from .database import db
from sqlalchemy.sql import func


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="user")  # Role field with a default value
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

    id = db.Column(db.Integer, primary_key=True)
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
    status = db.Column(db.String(50), nullable=True)
    total_sale = db.Column(db.Float, nullable=True)
    sending_currency = db.Column(db.String(10), nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    compliance_release_date = db.Column(db.DateTime, nullable=True)
    sender_status_detail = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
