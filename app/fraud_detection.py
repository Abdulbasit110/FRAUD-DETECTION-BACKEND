import joblib

model = None

def load_model():
    global model
    model = joblib.load('path_to_your_model.pkl')

def predict_fraud(data):
    return model.predict(data)
