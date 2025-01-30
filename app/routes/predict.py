from flask import Blueprint, request, jsonify
import joblib
import numpy as np
import os

# Define a new blueprint for predictions
predict_bp = Blueprint('predict', __name__)

# Load the Random Forest model
model_path = os.path.join(os.path.dirname(__file__), '../../random_forest_model.pkl')
model = joblib.load(model_path)

@predict_bp.route('/predict', methods=['POST'])
def predict():
    try:
        # Parse the input JSON
        data = request.get_json(force=True)

        # Extract features from the input data
        # Update these feature names based on your dataset
        features = [
            data['feature1'],
            data['feature2'],
            data['feature3'],
            # Add all necessary features here
        ]

        # Convert the features into a NumPy array
        features_array = np.array(features).reshape(1, -1)

        # Make a prediction using the model
        prediction = model.predict(features_array)

        # Return the prediction as a JSON response
        return jsonify({'prediction': int(prediction[0])})
    except Exception as e:
        return jsonify({'error': str(e)})

@predict_bp.route('/ping', methods=['GET'])
def ping():
    return model.feature_importances_.__str__(), 200
