import pandas as pd
from ..models import Transaction
from ..database import db

def load_data(file_path):
    data = pd.read_excel(file_path)
    for _, row in data.iterrows():
        transaction = Transaction(amount=row['amount'], date=row['date'])
        db.session.add(transaction)
    db.session.commit()
