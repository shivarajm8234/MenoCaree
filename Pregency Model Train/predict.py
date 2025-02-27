import joblib
import numpy as np
from datetime import datetime, timedelta

def load_models():
    print("Loading models...")
    try:
        models = {
            'random_forest': joblib.load('models/random_forest_model.pkl'),
            'gradient_boosting': joblib.load('models/gradient_boosting_model.pkl'),
            'svm': joblib.load('models/svm_model.pkl')
        }
        scaler = joblib.load('models/scaler.pkl')
        feature_names = joblib.load('models/feature_names.pkl')
        return models, scaler, feature_names
    except Exception as e:
        print(f"Error loading models: {str(e)}")
        print("Please make sure you have trained the models first by running 'python model_training.py'")
        exit(1)

def get_user_input():
    print("\n=== MenoCare Pregnancy Risk Assessment ===")
    print("Please enter the following information:\n")
    
    try:
        age = float(input("Age: "))
        pregnancy_week = float(input("Pregnancy Week (1-40): "))
        weight = float(input("Weight (in kg): "))
        height = float(input("Height (in feet, e.g., 5.4): "))
        
        print("\nBlood Pressure Reading:")
        systolic = float(input("Systolic (top number): "))
        diastolic = float(input("Diastolic (bottom number): "))
        
        print("\nAnemia Level:")
        print("0 - None")
        print("1 - Minimal")
        print("2 - Medium")
        anemia = float(input("Enter anemia level (0-2): "))
        
        print("\nJaundice Status:")
        print("0 - None")
        print("1 - Present")
        jaundice = float(input("Enter jaundice status (0-1): "))
        
        fetal_heartrate = float(input("\nFetal Heart Rate (beats per minute): "))
        
        print("\nVDRL Test Result:")
        print("0 - Negative")
        print("1 - Positive")
        vdrl = float(input("Enter VDRL result (0-1): "))
        
        print("\nHBsAg Test Result:")
        print("0 - Negative")
        print("1 - Positive")
        hbsag = float(input("Enter HBsAg result (0-1): "))
        
        # Calculate BMI
        height_m = height * 0.3048  # Convert feet to meters
        bmi = weight / (height_m ** 2)
        
        return np.array([[
            age,
            pregnancy_week,
            weight,
            height,
            systolic,
            diastolic,
            bmi
        ]])
        
    except ValueError as e:
        print(f"\nError: Please enter valid numerical values. {str(e)}")
        exit(1)

def predict_risk(input_data, models, scaler):
    # Scale the input data
    input_scaled = scaler.transform(input_data)
    
    # Get predictions from all models
    predictions = {}
    for name, model in models.items():
        pred_prob = model.predict_proba(input_scaled)[0][1]
        predictions[name] = pred_prob
    
    # Calculate ensemble average
    avg_probability = np.mean(list(predictions.values()))
    
    return predictions, avg_probability

def display_results(predictions, avg_probability, pregnancy_week):
    print("\n=== Risk Assessment Results ===")
    print("\nIndividual Model Predictions:")
    for model, prob in predictions.items():
        risk_level = "High" if prob > 0.5 else "Low"
        print(f"{model.replace('_', ' ').title()}: {prob:.1%} ({risk_level} Risk)")
    
    print(f"\nEnsemble Average: {avg_probability:.1%}")
    overall_risk = "High" if avg_probability > 0.5 else "Low"
    print(f"Overall Risk Level: {overall_risk}")
    
    # Calculate and display due date
    weeks_remaining = 40 - pregnancy_week
    due_date = (datetime.now() + timedelta(weeks=weeks_remaining)).strftime('%Y-%m-%d')
    print(f"\nEstimated Due Date: {due_date}")
    
    # Display pregnancy progress
    progress = (pregnancy_week / 40) * 100
    print(f"Pregnancy Progress: {progress:.1f}%")
    
    # Provide recommendations based on risk level
    print("\nRecommendations:")
    if overall_risk == "High":
        print("- Schedule more frequent check-ups with your healthcare provider")
        print("- Monitor your blood pressure regularly")
        print("- Keep track of daily fetal movements")
        print("- Maintain a healthy diet and take prescribed supplements")
        print("- Get adequate rest and avoid strenuous activities")
    else:
        print("- Continue regular prenatal check-ups")
        print("- Maintain a healthy lifestyle")
        print("- Take prescribed prenatal vitamins")
        print("- Stay hydrated and eat nutritious meals")
        print("- Exercise moderately as approved by your doctor")

def main():
    # Load the trained models
    models, scaler, feature_names = load_models()
    
    # Get user input
    input_data = get_user_input()
    
    # Make predictions
    predictions, avg_probability = predict_risk(input_data, models, scaler)
    
    # Display results
    display_results(predictions, avg_probability, input_data[0][1])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}") 