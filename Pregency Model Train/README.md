# MenoCare Pregnancy Journey Tracker

A web application that helps track pregnancy progress and predict potential risks using machine learning models. The application uses an ensemble of three models (Random Forest, Gradient Boosting, and SVM) to provide comprehensive risk assessment.

## Features

- Pregnancy progress tracking
- Due date calculation
- Risk assessment using ensemble machine learning models
- Health metrics monitoring
- Personalized recommendations
- User-friendly interface

## Setup Instructions

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create the models directory:
```bash
mkdir models
```

4. Train the models:
```bash
python model_training.py
```

5. Run the Flask application:
```bash
python app.py
```

6. Open your web browser and navigate to:
```
http://localhost:5000
```

## Input Parameters

The application takes the following inputs:
- Age
- Pregnancy Week
- Weight (kg)
- Height (feet)
- Blood Pressure (Systolic/Diastolic)
- Anemia Level
- Jaundice Status
- Fetal Heart Rate
- VDRL Test Result
- HBsAg Test Result

## Output

The application provides:
- Estimated due date
- Pregnancy progress visualization
- Risk assessment from multiple models
- Ensemble prediction
- Recommended next steps

## Technology Stack

- Python
- Flask
- scikit-learn
- pandas
- numpy
- Bootstrap
- JavaScript

## Note

This application is for informational purposes only and should not replace professional medical advice. Always consult with your healthcare provider for medical decisions. 