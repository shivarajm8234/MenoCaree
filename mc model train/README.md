# Menstrual Cycle Length Prediction System

An advanced machine learning system that predicts menstrual cycle length using ensemble learning techniques and provides comprehensive analysis.

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Data Description](#data-description)
5. [Model Architecture](#model-architecture)
6. [Usage Guide](#usage-guide)
7. [Technical Details](#technical-details)
8. [Output Interpretation](#output-interpretation)

## Overview

This system uses multiple machine learning models in an ensemble to predict menstrual cycle length based on various physiological and lifestyle factors. It employs advanced techniques like cross-validation, hyperparameter tuning, and model voting to provide accurate predictions with confidence levels.

## Features

- **Multiple Model Integration:**
  - Random Forest Regressor
  - Gradient Boosting Regressor
  - XGBoost Regressor
  - LightGBM Regressor
  - Ensemble Model (Voting Regressor)

- **Advanced Analytics:**
  - Cross-validation
  - Hyperparameter optimization
  - Feature importance analysis
  - Model performance comparison
  - Prediction confidence assessment

- **Interactive Interface:**
  - Guided data input
  - Input validation
  - Visual results
  - Comprehensive prediction reports

## Installation

```bash
# Required packages
pip install numpy pandas scikit-learn xgboost lightgbm seaborn matplotlib

# Clone the repository (if applicable)
git clone [repository-url]
cd [repository-name]
```

## Data Description

### Input Features:
1. **number_of_peak** (1-5)
   - Number of peaks in hormone levels
   - Indicates ovulation patterns

2. **Age** (15-50)
   - User's age in years
   - Affects cycle regularity

3. **Estimated_day_of_ovulation** (10-20)
   - Day of cycle when ovulation occurs
   - Key indicator for cycle prediction

4. **Length_of_Luteal_Phase** (10-16 days)
   - Days between ovulation and menstruation
   - Important biological marker

5. **Length_of_menses** (3-7 days)
   - Duration of menstrual flow
   - Indicates hormonal balance

6. **Unusual_Bleeding** (yes/no)
   - Presence of irregular bleeding
   - Important health indicator

7. **Height** (in feet and inches)
   - User's height
   - Used for BMI calculation

8. **Weight** (in kg)
   - User's weight
   - Used for BMI calculation

9. **Income** (0-10 scale)
   - Socioeconomic indicator
   - May affect stress levels

10. **BMI**
    - Calculated from height and weight
    - Important health indicator

11. **Mean_of_length_of_cycle** (20-50 days)
    - Average cycle length
    - Historical data point

12. **Menses_score** (1-5)
    - Severity of menstrual symptoms
    - Qualitative assessment

## Model Architecture

### Preprocessing Pipeline:
1. **Data Cleaning:**
   - Missing value detection
   - Outlier handling
   - Type conversion

2. **Feature Engineering:**
   - Height conversion to inches
   - BMI calculation
   - Categorical encoding

3. **Scaling:**
   - StandardScaler for numerical features
   - Ensures model stability

### Model Training:
1. **Cross-Validation:**
   - 5-fold cross-validation
   - Ensures robust model evaluation

2. **Hyperparameter Tuning:**
   - GridSearchCV for each model
   - Optimizes model performance

3. **Ensemble Creation:**
   - Combines predictions from all models
   - Weighted voting system

## Usage Guide

### Running the System:
1. Launch the script:
   ```bash
   python period_predict.py
   ```

2. Follow the interactive prompts:
   - Enter personal measurements
   - Provide cycle information
   - Input health indicators

3. Review the results:
   - View individual model predictions
   - Check confidence levels
   - Analyze visualization graphs

### Input Guidelines:
- Provide accurate measurements
- Follow the specified ranges
- Use consistent units (kg for weight, etc.)

## Technical Details

### Model Parameters:
```python
base_models = {
    'rf': {
        'n_estimators': [100, 200],
        'max_depth': [10, 20, None],
        'min_samples_split': [2, 5]
    },
    'gb': {
        'n_estimators': [100, 200],
        'learning_rate': [0.01, 0.1],
        'max_depth': [3, 5]
    },
    'xgb': {
        'n_estimators': [100, 200],
        'learning_rate': [0.01, 0.1],
        'max_depth': [3, 5]
    },
    'lgbm': {
        'n_estimators': [100, 200],
        'learning_rate': [0.01, 0.1],
        'max_depth': [3, 5]
    }
}
```

### Performance Metrics:
- Mean Absolute Error (MAE)
- Root Mean Square Error (RMSE)
- R-squared (R²) Score

## Output Interpretation

### Prediction Summary:
```
Prediction Summary:
--------------------------------------------------
RandomForest     : XX.X days
GradientBoost    : XX.X days
XGBoost          : XX.X days
LightGBM         : XX.X days
Ensemble         : XX.X days

Statistical Analysis:
Mean Prediction     : XX.X days
Standard Deviation  : XX.X days
Range              : XX.X - XX.X days

Prediction Confidence: [Very High/High/Moderate/Low]
```

### Confidence Levels:
- **Very High:** Standard deviation < 1 day
- **High:** Standard deviation < 2 days
- **Moderate:** Standard deviation < 3 days
- **Low:** Standard deviation ≥ 3 days

### Visualizations:
1. **Model Comparison Plot:**
   - Bar chart of predictions
   - Easy visual comparison
   - Includes error bars

2. **Feature Importance Plot:**
   - Shows key factors
   - Helps understand predictions

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Thanks to all contributors
- Special thanks to medical professionals for domain expertise
- Dataset contributors and maintainers
