import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor, AdaBoostRegressor
from sklearn.svm import SVR
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.impute import SimpleImputer
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Function to convert height in format "5'6" to inches or handle float values
def convert_height_to_inches(height):
    if isinstance(height, float):
        return height  # Already in numeric format
    if isinstance(height, str):
        try:
            feet, inches = height.split("'")
            return int(feet) * 12 + int(inches)
        except (ValueError, AttributeError):
            return None
    return None

# Function to validate user input for integers
def get_valid_int_input(prompt, min_value=None, max_value=None):
    while True:
        try:
            user_input = int(input(prompt))
            if (min_value is not None and user_input < min_value) or (max_value is not None and user_input > max_value):
                print(f"Please enter a value between {min_value} and {max_value}.")
            else:
                return user_input
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

# Function to validate user input for height (in the "5'6" format)
def get_valid_height_input():
    while True:
        height = input("\nEnter height (format 5'6): ")
        height_in_inches = convert_height_to_inches(height)
        
        # Check if the height is within the valid range (3'0" to 6'0")
        if height_in_inches is None:
            print("Invalid height format. Please enter the height in the format '5'6'.")
        elif height_in_inches < 36 or height_in_inches > 72:  # 3'0" = 36 inches, 6'0" = 72 inches
            print("Height should be between 3'0\" and 6'0\". Please enter a valid height.")
        else:
            return height_in_inches

# Function to validate unusual bleeding input (no/yes)
def get_valid_unusual_bleeding_input():
    while True:
        unusual_bleeding = input("\nEnter unusual bleeding (no/yes): ").lower()
        if unusual_bleeding == "no":
            return 0
        elif unusual_bleeding == "yes":
            return 1
        else:
            print("Invalid input. Please enter 'no' or 'yes'.")

# Load the dataset
data = pd.read_csv('period - Copy.csv')

# Inspect the data
print("\nDataset Info:")
print(data.info())
print("\nMissing Values:")
print(data.isnull().sum())
print("\nSample Data:")
print(data.head())

# Preprocess the dataset
# Convert categorical columns into numerical format
data['Unusual_Bleeding'] = data['Unusual_Bleeding'].map({'no': 0, 'yes': 1})

# Convert 'Height' to numerical format (inches)
print("\nConverting height values to inches...")
data['Height'] = data['Height'].astype(str).apply(convert_height_to_inches)
print("Height conversion completed.")

# Print height statistics
print("\nHeight Statistics:")
print(data['Height'].describe())

# Handle missing values before splitting
print("\nHandling missing values...")
# First, remove rows where target variable (Length_of_cycle) is missing
data = data.dropna(subset=['Length_of_cycle'])

# For feature columns, use median imputation
numeric_columns = data.select_dtypes(include=['float64']).columns
for column in numeric_columns:
    if column != 'Length_of_cycle':  # Don't impute target variable
        median_value = data[column].median()
        data[column].fillna(median_value, inplace=True)

# For categorical columns, use mode imputation
categorical_columns = data.select_dtypes(include=['object']).columns
for column in categorical_columns:
    mode_value = data[column].mode()[0]
    data[column].fillna(mode_value, inplace=True)

print("Missing values handled.")
print("\nRemaining missing values:")
print(data.isnull().sum())

# Define features (X) and target (y)
X = data.drop('Length_of_cycle', axis=1)  # Features
y = data['Length_of_cycle']  # Target

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Create preprocessing pipeline (now only for scaling since we've already handled missing values)
preprocessing = Pipeline([
    ('scaler', StandardScaler())
])

# Fit and transform the training data
X_train_processed = preprocessing.fit_transform(X_train)
X_test_processed = preprocessing.transform(X_test)

# Define base models with hyperparameter grids
base_models = {
    'rf': {
        'model': RandomForestRegressor(random_state=42),
        'params': {
            'n_estimators': [100, 200],
            'max_depth': [10, 20, None],
            'min_samples_split': [2, 5]
        }
    },
    'gb': {
        'model': GradientBoostingRegressor(random_state=42),
        'params': {
            'n_estimators': [100, 200],
            'learning_rate': [0.01, 0.1],
            'max_depth': [3, 5]
        }
    },
    'xgb': {
        'model': XGBRegressor(random_state=42),
        'params': {
            'n_estimators': [100, 200],
            'learning_rate': [0.01, 0.1],
            'max_depth': [3, 5]
        }
    },
    'lgbm': {
        'model': LGBMRegressor(random_state=42),
        'params': {
            'n_estimators': [100, 200],
            'learning_rate': [0.01, 0.1],
            'max_depth': [3, 5]
        }
    },
    'ada': {
        'model': AdaBoostRegressor(random_state=42),
        'params': {
            'n_estimators': [50, 100],
            'learning_rate': [0.01, 0.1]
        }
    }
}

# Dictionary to store best models and their scores
best_models = {}
cv_scores = {}
test_scores = {}
predictions = {}

# Train and tune each base model
print("\nTraining and tuning individual models...")
for name, model_info in base_models.items():
    print(f"\nTuning {name}...")
    grid_search = GridSearchCV(
        model_info['model'],
        model_info['params'],
        cv=5,
        scoring='neg_mean_squared_error',
        n_jobs=-1
    )
    grid_search.fit(X_train_processed, y_train)
    
    # Store best model
    best_models[name] = grid_search.best_estimator_
    
    # Get cross-validation score
    cv_scores[name] = cross_val_score(
        best_models[name], 
        preprocessing.transform(X), 
        y, 
        cv=5, 
        scoring='neg_mean_squared_error'
    )
    
    # Get test score
    y_pred = best_models[name].predict(X_test_processed)
    predictions[name] = y_pred
    test_scores[name] = {
        'mae': mean_absolute_error(y_test, y_pred),
        'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
        'r2': r2_score(y_test, y_pred)
    }
    
    print(f"Best parameters for {name}: {grid_search.best_params_}")
    print(f"Test scores for {name}:")
    print(f"MAE: {test_scores[name]['mae']:.2f}")
    print(f"RMSE: {test_scores[name]['rmse']:.2f}")
    print(f"R2: {test_scores[name]['r2']:.2f}")

# Create and train the voting regressor with best models
voting_regressor = VotingRegressor([
    (name, model) for name, model in best_models.items()
])
voting_regressor.fit(X_train_processed, y_train)

# Get ensemble predictions
ensemble_pred = voting_regressor.predict(X_test_processed)
ensemble_scores = {
    'mae': mean_absolute_error(y_test, ensemble_pred),
    'rmse': np.sqrt(mean_squared_error(y_test, ensemble_pred)),
    'r2': r2_score(y_test, ensemble_pred)
}

print("\nEnsemble Model Performance:")
print(f"MAE: {ensemble_scores['mae']:.2f}")
print(f"RMSE: {ensemble_scores['rmse']:.2f}")
print(f"R2: {ensemble_scores['r2']:.2f}")

# Visualization functions
def plot_model_comparison():
    plt.figure(figsize=(15, 5))
    
    # Plot MAE comparison
    plt.subplot(131)
    maes = [scores['mae'] for scores in test_scores.values()]
    maes.append(ensemble_scores['mae'])
    names = list(test_scores.keys()) + ['Ensemble']
    plt.bar(names, maes)
    plt.title('Mean Absolute Error Comparison')
    plt.xticks(rotation=45)
    
    # Plot RMSE comparison
    plt.subplot(132)
    rmses = [scores['rmse'] for scores in test_scores.values()]
    rmses.append(ensemble_scores['rmse'])
    plt.bar(names, rmses)
    plt.title('Root Mean Squared Error Comparison')
    plt.xticks(rotation=45)
    
    # Plot R2 comparison
    plt.subplot(133)
    r2s = [scores['r2'] for scores in test_scores.values()]
    r2s.append(ensemble_scores['r2'])
    plt.bar(names, r2s)
    plt.title('R-squared Score Comparison')
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.show()

def plot_prediction_comparison():
    plt.figure(figsize=(12, 6))
    plt.plot(y_test.values, label='Actual', color='black', linewidth=2)
    
    for name, pred in predictions.items():
        plt.plot(pred, label=name, alpha=0.5)
    
    plt.plot(ensemble_pred, label='Ensemble', linewidth=2)
    plt.title('Prediction Comparison')
    plt.legend()
    plt.show()

def plot_feature_importance():
    # Get feature importance from Random Forest model
    importance = best_models['rf'].feature_importances_
    features = X.columns
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x=importance, y=features)
    plt.title('Feature Importance')
    plt.show()

# Display visualizations
print("\nGenerating performance visualizations...")
plot_model_comparison()
plot_prediction_comparison()
plot_feature_importance()

# Save the final ensemble model and preprocessing pipeline
joblib.dump(voting_regressor, 'menstrual_cycle_predictor_ensemble.pkl')
joblib.dump(preprocessing, 'preprocessing_pipeline.pkl')

# Update prediction function to use preprocessing pipeline
def predict_next_cycle(input_data):
    """Predict the next cycle day using the trained ensemble model."""
    df = pd.DataFrame([input_data], columns=X.columns)
    df_processed = preprocessing.transform(df)
    prediction = voting_regressor.predict(df_processed)
    return prediction

# Function to get user input and predict next cycle day
def get_user_input():
    print("\nPlease enter the following details for prediction:")
    
    number_of_peak = get_valid_int_input("\nEnter number of peak (1-5): ", min_value=1, max_value=5)
    age = get_valid_int_input("\nEnter age (15-50): ", min_value=15, max_value=50)
    previous_cycle_length = get_valid_int_input("\nEnter previous cycle length (20-50 days): ", min_value=20, max_value=50)
    estimated_ovulation = get_valid_int_input("\nEnter estimated day of ovulation (10-20): ", min_value=10, max_value=20)
    luteal_phase = get_valid_int_input("\nEnter length of luteal phase (10-16 days): ", min_value=10, max_value=16)
    menses_length = get_valid_int_input("\nEnter length of menses (3-7 days): ", min_value=3, max_value=7)
    height_in_inches = get_valid_height_input()
    weight = get_valid_int_input("\nEnter weight (in kg): ", min_value=30, max_value=150)
    income = get_valid_int_input("\nEnter income (0-10): ", min_value=0, max_value=10)
    bmi = weight / ((height_in_inches * 0.0254) ** 2)  # Convert height to meters and calculate BMI
    mean_cycle = get_valid_int_input("\nEnter mean cycle length (20-50 days): ", min_value=20, max_value=50)
    menses_score = float(input("\nEnter menses score (1-5): "))
    unusual_bleeding_num = get_valid_unusual_bleeding_input()
    
    # Prepare the input data for prediction
    input_data = {
        'number_of_peak': number_of_peak,
        'Age': age,
        'Estimated_day_of_ovulution': estimated_ovulation,
        'Length_of_Leutal_Phase': luteal_phase,
        'Length_of_menses': menses_length,
        'Unusual_Bleeding': unusual_bleeding_num,
        'Height': height_in_inches,
        'Weight': weight,
        'Income': income,
        'BMI': bmi,
        'Mean_of_length_of_cycle': mean_cycle,
        'Menses_score': menses_score
    }

    return input_data

def make_predictions(input_data):
    """Make predictions using all models and compare results"""
    # Prepare input data
    df = pd.DataFrame([input_data], columns=X.columns)
    df_processed = preprocessing.transform(df)
    
    # Get predictions from all models
    predictions = {}
    for name, model in best_models.items():
        pred = model.predict(df_processed)[0]
        predictions[name] = pred
    
    # Get ensemble prediction
    ensemble_pred = voting_regressor.predict(df_processed)[0]
    predictions['Ensemble'] = ensemble_pred
    
    return predictions

def visualize_predictions(predictions):
    """Visualize predictions from all models"""
    models = list(predictions.keys())
    values = list(predictions.values())
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(models, values)
    plt.title('Predicted Cycle Length by Different Models')
    plt.xlabel('Models')
    plt.ylabel('Predicted Cycle Length (days)')
    plt.xticks(rotation=45)
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom')
    
    plt.tight_layout()
    plt.show()

def print_prediction_summary(predictions):
    """Print a summary of predictions with confidence analysis"""
    print("\nPrediction Summary:")
    print("-" * 50)
    
    # Print individual predictions
    for model, pred in predictions.items():
        print(f"{model:15} : {pred:.1f} days")
    
    # Calculate prediction statistics
    values = list(predictions.values())
    mean_pred = np.mean(values)
    std_pred = np.std(values)
    min_pred = min(values)
    max_pred = max(values)
    
    print("\nStatistical Analysis:")
    print(f"Mean Prediction     : {mean_pred:.1f} days")
    print(f"Standard Deviation  : {std_pred:.1f} days")
    print(f"Range              : {min_pred:.1f} - {max_pred:.1f} days")
    
    # Determine confidence level based on standard deviation
    if std_pred < 1:
        confidence = "Very High"
    elif std_pred < 2:
        confidence = "High"
    elif std_pred < 3:
        confidence = "Moderate"
    else:
        confidence = "Low"
    
    print(f"\nPrediction Confidence: {confidence}")
    print(f"(Based on agreement between different models)")
    
    # Final recommendation
    print("\nRecommended Prediction:")
    print(f"Your next cycle length is likely to be {predictions['Ensemble']:.1f} days")
    print(f"You should expect your next period between {predictions['Ensemble']-2:.1f} and {predictions['Ensemble']+2:.1f} days")

# Get user input and make predictions
while True:
    print("\n" + "="*50)
    print("Menstrual Cycle Length Prediction")
    print("="*50)
    
    input_data = get_user_input()
    predictions = make_predictions(input_data)
    
    # Show predictions
    print_prediction_summary(predictions)
    visualize_predictions(predictions)
    
    # Ask if user wants to make another prediction
    another = input("\nWould you like to make another prediction? (yes/no): ").lower()
    if another != 'yes':
        break

print("\nThank you for using the Menstrual Cycle Predictor!")
