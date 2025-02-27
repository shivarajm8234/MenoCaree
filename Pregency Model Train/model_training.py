import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
import joblib
import json
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re

def load_and_preprocess_data(file_path):
    print("Loading dataset...")
    df = pd.read_csv(file_path, skiprows=[0])
    df.columns = [col.strip() for col in df.columns]
    
    column_mapping = {
        'Age': 'age',
        'Gravida': 'pregnancy_number',
        'গর্ভকাল': 'pregnancy_week',
        'ওজন': 'weight_kg',
        'উচ্চতা': 'height',
        'রক্ত চাপ': 'blood_pressure',
        'রক্তস্বল্পতা': 'anemia',
        'ঝুকিপূর্ণ গর্ভ': 'high_risk_pregnancy'
    }
    df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns}, inplace=True)
    
    def extract_number(series, pattern):
        return pd.to_numeric(series.astype(str).str.extract(pattern)[0], errors='coerce')
    
    print("Processing numerical data...")
    # Process pregnancy week (extract number from strings like "38 week")
    df['pregnancy_week'] = extract_number(df['pregnancy_week'], r'(\d+)')
    print("Processed pregnancy week")
    
    # Process weight (remove 'kg' and convert to numeric)
    df['weight_kg'] = extract_number(df['weight_kg'], r'(\d+)')
    print("Processed weight")
    
    # Process height (remove inches symbol and convert to numeric)
    df['height'] = extract_number(df['height'], r'(\d+\.?\d*)')
    print("Processed height")
    
    # Process blood pressure
    if 'blood_pressure' in df.columns:
        bp_pattern = r'(\d+)[/](\d+)'
        bp_cols = df['blood_pressure'].str.extract(bp_pattern)
        df['systolic_bp'] = pd.to_numeric(bp_cols[0], errors='coerce')
        df['diastolic_bp'] = pd.to_numeric(bp_cols[1], errors='coerce')
        print("Processed blood pressure")
    
    # Process age
    df['age'] = pd.to_numeric(df['age'], errors='coerce')
    print("Processed age")
    
    # Calculate BMI
    df['bmi'] = df['weight_kg'] / ((df['height'] * 0.0254) ** 2)  # Convert height to meters
    print("Calculated BMI")
    
    # Process high risk pregnancy (convert Yes/No to 1/0)
    risk_mapping = {
        'Yes': 1, 'No': 0,
        'yes': 1, 'no': 0,
        'YES': 1, 'NO': 0,
        'হ্যাঁ': 1, 'না': 0  # Bengali Yes/No
    }
    df['high_risk_pregnancy'] = df['high_risk_pregnancy'].map(risk_mapping).fillna(0)
    print("Processed high risk pregnancy status")
    
    # If high_risk_pregnancy column is missing or all values are NaN, calculate risk based on medical factors
    if 'high_risk_pregnancy' not in df.columns or df['high_risk_pregnancy'].isna().all():
        print("Generating risk assessment based on medical factors...")
        def assess_risk(row):
            risk_factors = 0
            
            # Age-based risk (under 18 or over 35)
            if pd.notna(row['age']) and (row['age'] > 35 or row['age'] < 18):
                risk_factors += 1
            
            # Blood pressure risk (high BP: systolic > 140 or diastolic > 90)
            if pd.notna(row['systolic_bp']) and pd.notna(row['diastolic_bp']):
                if row['systolic_bp'] > 140 or row['diastolic_bp'] > 90:
                    risk_factors += 1
            
            # BMI-based risk (underweight < 18.5 or obese > 30)
            if pd.notna(row['bmi']):
                if row['bmi'] < 18.5 or row['bmi'] > 30:
                    risk_factors += 1
            
            return 1 if risk_factors >= 2 else 0
        
        df['high_risk_pregnancy'] = df.apply(assess_risk, axis=1)
    
    # Select features for modeling
    features = ['age', 'pregnancy_week', 'weight_kg', 'height', 'systolic_bp', 'diastolic_bp', 'bmi']
    
    # Prepare feature matrix
    X = df[features].copy()
    
    # Handle missing values using median
    print("\nHandling missing values...")
    for feature in features:
        if X[feature].isnull().any():
            median_val = X[feature].median()
            X[feature].fillna(median_val, inplace=True)
            print(f"Filled missing values in {feature}")
    
    # Prepare target variable
    y = df['high_risk_pregnancy'].astype(int)
    
    print("\nData preprocessing completed successfully")
    print(f"Dataset shape: {X.shape}")
    print(f"Number of high-risk pregnancies: {y.sum()} ({(y.sum()/len(y))*100:.2f}%)")
    
    return X, y, features

def evaluate_model(model, X_train, X_test, y_train, y_test):
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred),
        'roc_auc': roc_auc_score(y_test, y_pred_proba),
        'train_accuracy': accuracy_score(y_train, model.predict(X_train))
    }
    
    metrics['cv_mean'] = cross_val_score(model, X_train, y_train, cv=5).mean()
    return metrics

def plot_confusion_matrix(model, X_test, y_test, name, save_dir='static/images'):
    y_pred = model.predict(X_test)
    cm = confusion_matrix(y_test, y_pred)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title(f'Confusion Matrix - {name}')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    os.makedirs(save_dir, exist_ok=True)
    plt.savefig(f'{save_dir}/{name}_confusion_matrix.png')
    plt.close()

def plot_feature_importance(model, features, name, save_dir='static/images'):
    if hasattr(model, 'feature_importances_'):
        importance = model.feature_importances_
    elif hasattr(model, 'coef_'):
        importance = np.abs(model.coef_[0])
    else:
        return
    
    plt.figure(figsize=(10, 6))
    importance_df = pd.DataFrame({'feature': features, 'importance': importance})
    importance_df = importance_df.sort_values('importance', ascending=True)
    
    plt.barh(importance_df['feature'], importance_df['importance'])
    plt.title(f'Feature Importance - {name}')
    plt.xlabel('Importance')
    plt.tight_layout()
    os.makedirs(save_dir, exist_ok=True)
    plt.savefig(f'{save_dir}/{name}_feature_importance.png')
    plt.close()

def train_and_evaluate_models(file_path):
    X, y, features = load_and_preprocess_data(file_path)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Define parameter grids for GridSearchCV
    param_grids = {
        'random_forest': {
            'estimator': RandomForestClassifier(random_state=42),
            'param_grid': {
                'n_estimators': [100],
                'max_depth': [5, 7],
                'min_samples_split': [15],
                'min_samples_leaf': [6],
                'max_features': ['sqrt']
            }
        },
        'gradient_boosting': {
            'estimator': GradientBoostingClassifier(random_state=42),
            'param_grid': {
                'n_estimators': [100],
                'max_depth': [3, 4],
                'min_samples_split': [15],
                'min_samples_leaf': [6],
                'learning_rate': [0.05],
                'subsample': [0.7]
            }
        },
        'svm': {
            'estimator': SVC(probability=True, random_state=42),
            'param_grid': {
                'C': [0.5, 1.0],
                'kernel': ['rbf'],
                'gamma': ['scale']
            }
        }
    }
    
    results = {}
    for name, params in param_grids.items():
        print(f"\nTraining {name}...")
        
        # Perform GridSearchCV
        grid_search = GridSearchCV(
            estimator=params['estimator'],
            param_grid=params['param_grid'],
            cv=5,
            scoring='accuracy',
            n_jobs=-1
        )
        
        # Train model
        grid_search.fit(X_train_scaled, y_train)
        best_model = grid_search.best_estimator_
        
        # Evaluate model
        results[name] = evaluate_model(best_model, X_train_scaled, X_test_scaled, y_train, y_test)
        results[name]['best_params'] = grid_search.best_params_
        
        # Save model
        os.makedirs('models', exist_ok=True)
        joblib.dump(best_model, f'models/{name}_model.pkl')
        
        # Create visualizations
        plot_confusion_matrix(best_model, X_test_scaled, y_test, name)
        plot_feature_importance(best_model, features, name)
        print(f"{name} training completed with best parameters: {grid_search.best_params_}")
    
    # Save model artifacts
    joblib.dump(scaler, 'models/scaler.pkl')
    joblib.dump(features, 'models/feature_names.pkl')
    with open('models/model_metrics.json', 'w') as f:
        json.dump(results, f, indent=4)
    
    return results

if __name__ == "__main__":
    os.makedirs('models', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)
    
    try:
        print("Starting model training process...")
        results = train_and_evaluate_models('Pregnancy dataset.csv')
        
        print("\nModel Performance Metrics:")
        print("=========================")
        for model_name, metrics in results.items():
            print(f"\n{model_name.replace('_', ' ').title()}:")
            print(f"Best Parameters: {metrics['best_params']}")
            print(f"Accuracy: {metrics['accuracy']:.3f}")
            print(f"Precision: {metrics['precision']:.3f}")
            print(f"Recall: {metrics['recall']:.3f}")
            print(f"F1 Score: {metrics['f1']:.3f}")
            print(f"ROC AUC: {metrics['roc_auc']:.3f}")
            print(f"Training Accuracy: {metrics['train_accuracy']:.3f}")
            print(f"Cross-validation Score: {metrics['cv_mean']:.3f}")
            
            # Calculate overfitting score
            overfit_score = metrics['train_accuracy'] - metrics['accuracy']
            print(f"Overfitting Score: {overfit_score:.3f} (closer to 0 is better)")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        import traceback
        print("\nFull traceback:")
        print(traceback.format_exc())
