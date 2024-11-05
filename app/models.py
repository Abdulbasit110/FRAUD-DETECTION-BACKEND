# from .database import db

# class Transaction(db.Model):
#     __tablename__ = 'transactions'
#     id = db.Column(db.Integer, primary_key=True)
#     amount = db.Column(db.Float, nullable=False)
#     date = db.Column(db.DateTime, nullable=False)
#     is_fraud = db.Column(db.Boolean, default=False)



# class TestModel(db.Model):
#     __tablename__ = 'test_model'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(50), nullable=False)


from .database import db

class TestModel(db.Model):
    __tablename__ = 'test_model'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    # Temporary column to trigger a change
    temp_column = db.Column(db.String(20), nullable=True)  # Add this line
