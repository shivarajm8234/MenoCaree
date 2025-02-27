from flask import Flask, render_template, request, jsonify
import joblib
import numpy as np
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)

# Load models and scaler
def load_models():
    models = {
        'random_forest': joblib.load('models/random_forest_model.pkl'),
        'gradient_boosting': joblib.load('models/gradient_boosting_model.pkl'),
        'svm': joblib.load('models/svm_model.pkl')
    }
    scaler = joblib.load('models/scaler.pkl')
    feature_names = joblib.load('models/feature_names.pkl')
    return models, scaler, feature_names

def load_metrics():
    with open('models/model_metrics.json', 'r') as f:
        return json.load(f)

@app.route('/')
def home():
    # Load model metrics
    try:
        metrics = load_metrics()
        has_metrics = True
    except:
        metrics = {}
        has_metrics = False
    
    # Check if visualization images exist
    model_names = ['random_forest', 'gradient_boosting', 'svm']
    images = {
        model: {
            'confusion_matrix': os.path.exists(f'static/images/{model}_confusion_matrix.png'),
            'feature_importance': os.path.exists(f'static/images/{model}_feature_importance.png')
        }
        for model in model_names
    }
    
    return render_template('index.html', metrics=metrics, has_metrics=has_metrics, images=images)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        models, scaler, feature_names = load_models()
        
        # Prepare input data
        input_data = np.array([[
            float(data['age']),
            float(data['pregnancy_week']),
            float(data['weight_kg']),
            float(data['height']),
            float(data['systolic_bp']),
            float(data['diastolic_bp']),
            float(data['anemia']),
            float(data['jaundice']),
            float(data['fetal_heartrate']),
            float(data['vdrl']),
            float(data['hbsag'])
        ]])
        
        # Scale input data
        input_scaled = scaler.transform(input_data)
        
        # Get predictions from all models
        predictions = {}
        for name, model in models.items():
            pred_prob = model.predict_proba(input_scaled)[0][1]
            predictions[name] = float(pred_prob)
        
        # Calculate ensemble average
        avg_probability = np.mean(list(predictions.values()))
        
        # Calculate due date
        current_week = float(data['pregnancy_week'])
        weeks_remaining = 40 - current_week
        due_date = (datetime.now() + timedelta(weeks=weeks_remaining)).strftime('%Y-%m-%d')
        
        return jsonify({
            'predictions': predictions,
            'ensemble_average': float(avg_probability),
            'due_date': due_date,
            'risk_level': 'High' if avg_probability > 0.5 else 'Low'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True) 