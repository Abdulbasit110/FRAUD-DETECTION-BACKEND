from flask import Blueprint, request, jsonify
from ..fraud_detection import predict_fraud

bp = Blueprint('transaction', __name__, url_prefix='/transaction')

@bp.route('/predict', methods=['POST'])
def predict_transaction():
    transaction_data = request.get_json()
    prediction = predict_fraud(transaction_data)
    return jsonify({'is_fraud': bool(prediction)})
