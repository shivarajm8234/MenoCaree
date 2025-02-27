# Import required libraries
from flask import Blueprint, request, jsonify, render_template, current_app, session, url_for, redirect
from datetime import datetime, timedelta
import os
import logging
from dotenv import load_dotenv
from groq import Groq

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Initialize blueprint
hormonal_balance = Blueprint('hormonal_balance', __name__)

def calculate_health_score(data):
    """Calculate health score based on user inputs"""
    score = 60  # Base score
    
    # Lifestyle factors (max +20)
    sleep_scores = {'good': 7, 'fair': 4, 'poor': 0}
    score += sleep_scores.get(data.get('sleep_quality', 'fair'), 4)
    
    exercise_scores = {'high': 7, 'moderate': 4, 'low': 0}
    score += exercise_scores.get(data.get('exercise_frequency', 'moderate'), 4)
    
    diet_scores = {'excellent': 6, 'good': 4, 'fair': 2, 'poor': 0}
    score += diet_scores.get(data.get('diet_quality', 'fair'), 2)

    # Symptoms impact (max -15)
    symptoms = data.get('symptoms', [])
    symptom_impact = -len(symptoms) * 2  # Each symptom reduces score
    score += max(-15, symptom_impact)

    # Energy and mood (max +10)
    energy_scores = {'high': 5, 'moderate': 3, 'low': 0}
    score += energy_scores.get(data.get('energy_levels', 'moderate'), 3)
    
    mood_scores = {'stable': 5, 'somewhat_stable': 3, 'unstable': 0}
    score += mood_scores.get(data.get('mood_stability', 'somewhat_stable'), 3)

    # Medical conditions impact (max -10)
    conditions = data.get('medical_conditions', [])
    condition_impact = -len(conditions) * 3
    score += max(-10, condition_impact)
    
    return min(100, max(0, score))

def get_bmi_category(height_cm, weight_kg):
    """Calculate BMI and return category"""
    if not height_cm or not weight_kg:
        return "Unknown"
        
    height_m = height_cm / 100
    bmi = weight_kg / (height_m * height_m)
    
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"

def get_related_content(data):
    """Get related content based on user's symptoms and conditions"""
    content = {
        'articles': [],
        'lifestyle_tips': [],
        'nutrition_advice': [],
        'exercise_tips': []
    }
    
    # Add relevant articles based on symptoms
    if 'symptoms' in data:
        if 'fatigue' in data['symptoms']:
            content['articles'].append({
                'title': 'Understanding and Managing Fatigue',
                'description': 'Learn about the hormonal causes of fatigue and effective management strategies.'
            })
        if 'mood_swings' in data['symptoms']:
            content['articles'].append({
                'title': 'Balancing Mood Through Hormonal Health',
                'description': 'Discover the connection between hormones and mood, and natural ways to maintain balance.'
            })
        if 'weight_changes' in data['symptoms']:
            content['articles'].append({
                'title': 'Hormones and Weight Management',
                'description': 'Understanding how hormones affect weight and metabolism.'
            })
            
    # Add lifestyle tips based on scores
    if data.get('sleep_quality') == 'poor':
        content['lifestyle_tips'].extend([
            'Create a calming bedtime routine',
            'Optimize your sleep environment',
            'Practice relaxation techniques before bed'
        ])
    
    if data.get('stress_level') == 'high':
        content['lifestyle_tips'].extend([
            'Try mindfulness meditation',
            'Practice deep breathing exercises',
            'Consider stress-reducing activities like yoga'
        ])

    # Add nutrition advice based on health status
    if data.get('diet_quality') in ['poor', 'fair']:
        content['nutrition_advice'].extend([
            'Include hormone-balancing foods like leafy greens and healthy fats',
            'Reduce processed foods and added sugars',
            'Stay hydrated with water and herbal teas'
        ])
    
    # Add exercise recommendations
    if data.get('exercise_frequency') == 'low':
        content['exercise_tips'].extend([
            'Start with gentle walking or swimming',
            'Try yoga for hormone balance',
            'Gradually increase activity level'
        ])
    
    return content

def analyze_hormonal_health(data, health_score):
    """Generate detailed hormonal health analysis with related content"""
    
    # Get basic analysis
    bmi_category = get_bmi_category(data.get('height'), data.get('weight'))
    related_content = get_related_content(data)
    
    # Build analysis sections
    lifestyle_analysis = f"""
### Lifestyle Assessment

Your current lifestyle shows the following patterns:
- Sleep Quality: {data.get('sleep_quality', 'Not specified').title()}
- Exercise Frequency: {data.get('exercise_frequency', 'Not specified').title()}
- Diet Quality: {data.get('diet_quality', 'Not specified').title()}
- Stress Level: {data.get('stress_level', 'Not specified').title()}
- BMI Category: {bmi_category}

#### Impact on Hormonal Health
Your lifestyle choices play a crucial role in hormonal balance. {get_lifestyle_impact(data)}
"""

    symptoms_analysis = """
### Symptom Analysis

You reported the following symptoms:
"""
    if data.get('symptoms'):
        for symptom in data['symptoms']:
            symptoms_analysis += f"- {symptom.replace('_', ' ').title()}\n"
        symptoms_analysis += "\n#### Symptom Insights\n"
        symptoms_analysis += get_symptom_insights(data['symptoms'])
    else:
        symptoms_analysis += "- No specific symptoms reported\n"

    hormonal_status = """
### Hormonal Status Indicators

Key indicators of your hormonal health:
"""
    if data.get('menstrual_regularity') and data['menstrual_regularity'] != 'not_applicable':
        hormonal_status += f"- Menstrual Cycle: {data['menstrual_regularity'].replace('_', ' ').title()}\n"
    
    hormonal_status += f"- Energy Levels: {data.get('energy_levels', 'Not specified').title()}\n"
    hormonal_status += f"- Mood Stability: {data.get('mood_stability', 'Not specified').replace('_', ' ').title()}\n"

    medical_context = """
### Medical Context
"""
    if data.get('medical_conditions'):
        medical_context += "\nExisting conditions:\n"
        for condition in data['medical_conditions']:
            medical_context += f"- {condition.replace('_', ' ').title()}\n"
            medical_context += get_condition_info(condition)
    
    if data.get('medications') and data['medications'] != 'none':
        medical_context += f"\nCurrent medication: {data['medications'].replace('_', ' ').title()}"
        medical_context += get_medication_info(data['medications'])
    else:
        medical_context += "\nNo current hormone-related medications reported."

    recommendations = """
### Personalized Recommendations

Based on your profile, here are key recommendations:
"""
    # Add lifestyle recommendations
    if related_content['lifestyle_tips']:
        recommendations += "\n#### Lifestyle Adjustments\n"
        for tip in related_content['lifestyle_tips']:
            recommendations += f"- {tip}\n"

    if related_content['nutrition_advice']:
        recommendations += "\n#### Nutrition Guidelines\n"
        for advice in related_content['nutrition_advice']:
            recommendations += f"- {advice}\n"

    if related_content['exercise_tips']:
        recommendations += "\n#### Exercise Recommendations\n"
        for tip in related_content['exercise_tips']:
            recommendations += f"- {tip}\n"

    related_resources = """
### Related Resources

#### Recommended Articles
"""
    if related_content['articles']:
        for article in related_content['articles']:
            related_resources += f"- **{article['title']}**\n  {article['description']}\n"
    else:
        related_resources += "No specific articles recommended based on your profile.\n"

    # Compile final analysis
    final_analysis = f"""
# Comprehensive Hormonal Health Analysis

## Overall Health Score: {health_score}/100

{lifestyle_analysis}
{symptoms_analysis}
{hormonal_status}
{medical_context}
{recommendations}
{related_resources}

### Next Steps

1. Track your symptoms daily using our symptom tracker
2. Schedule regular check-ups with your healthcare provider
3. Implement the recommended lifestyle changes gradually
4. Monitor your progress and adjust as needed
5. Consider consulting with specialists for specific concerns

*Note: This analysis is for informational purposes only and should not replace professional medical advice.*
"""

    return final_analysis

def get_lifestyle_impact(data):
    """Generate lifestyle impact analysis"""
    impacts = []
    
    if data.get('sleep_quality') == 'poor':
        impacts.append("Poor sleep can disrupt cortisol rhythms and hormone production")
    elif data.get('sleep_quality') == 'good':
        impacts.append("Good sleep habits support healthy hormone production")
        
    if data.get('exercise_frequency') == 'low':
        impacts.append("Limited physical activity may affect hormone regulation")
    elif data.get('exercise_frequency') == 'high':
        impacts.append("Regular exercise promotes hormonal balance")
        
    if data.get('stress_level') == 'high':
        impacts.append("High stress levels can significantly impact hormone balance")
        
    return " ".join(impacts) if impacts else "Consider tracking your lifestyle habits to understand their impact better."

def get_symptom_insights(symptoms):
    """Provide insights for reported symptoms"""
    insights = ""
    symptom_info = {
        'fatigue': "Fatigue can be related to thyroid function and cortisol levels.",
        'mood_swings': "Mood changes often reflect fluctuations in estrogen and progesterone.",
        'weight_changes': "Weight changes may indicate metabolic or thyroid hormone imbalances.",
        'anxiety': "Anxiety can be influenced by cortisol and thyroid hormone levels.",
        'hot_flashes': "Hot flashes are often related to estrogen level changes.",
        'irregular_periods': "Irregular cycles may indicate imbalances in reproductive hormones.",
        'skin_issues': "Skin problems can be related to androgen hormone levels.",
        'digestive_issues': "Digestive issues may be influenced by cortisol and thyroid function."
    }
    
    for symptom in symptoms:
        if symptom in symptom_info:
            insights += f"- {symptom_info[symptom]}\n"
            
    return insights

def get_condition_info(condition):
    """Provide information about specific conditions"""
    condition_info = {
        'thyroid': "\n  > Thyroid conditions directly affect metabolism and energy levels. Regular monitoring is important.\n",
        'pcos': "\n  > PCOS affects hormone balance and metabolism. Lifestyle management plays a key role.\n",
        'diabetes': "\n  > Diabetes can interact with hormone function. Blood sugar management is crucial.\n",
        'hypertension': "\n  > Hypertension may be influenced by hormone levels. Regular monitoring is recommended.\n"
    }
    return condition_info.get(condition, "")

def get_medication_info(medication):
    """Provide information about medications"""
    medication_info = {
        'hormonal_birth_control': "\n  > Birth control can affect natural hormone cycles. Regular check-ups are important.\n",
        'thyroid_medication': "\n  > Thyroid medication requires careful monitoring and dosage adjustment.\n",
        'other': "\n  > Regular medication review with your healthcare provider is recommended.\n"
    }
    return medication_info.get(medication, "")

@hormonal_balance.route('/analyze-symptoms', methods=['POST'])
def analyze():
    """Analyze form data and redirect to dashboard"""
    try:
        data = request.get_json()
        logging.info(f"Received data: {data}")
        
        if not data:
            logging.error("No data received in request")
            return jsonify({"error": "No data provided"}), 400

        # Validate required fields
        required_fields = ['age', 'gender']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            logging.error(error_msg)
            return jsonify({"error": error_msg}), 400

        # Calculate health score
        health_score = calculate_health_score(data)
        
        # Generate detailed analysis
        analysis = analyze_hormonal_health(data, health_score)
        
        # Store data in session
        session['form_data'] = data
        session['health_score'] = health_score
        session['analysis'] = analysis
        logging.info("Data stored in session successfully")
        
        return jsonify({
            "status": "success",
            "redirect": url_for('hormonal_balance.dashboard')
        })
        
    except Exception as e:
        error_msg = f"Error in analyze: {str(e)}"
        logging.error(error_msg)
        return jsonify({"error": error_msg}), 500

@hormonal_balance.route('/')
@hormonal_balance.route('/dashboard')
def dashboard():
    """Render the hormonal balance dashboard"""
    try:
        # Get data from session
        data = session.get('form_data')
        
        if not data:
            logging.info("No form data in session, redirecting to form")
            return redirect(url_for('hormonal_balance.show_form'))  # Updated this line
        
        # Calculate overall score
        overall_score = calculate_health_score(data)
        
        # Calculate BMI and get category
        height = float(data.get('height', 0))
        weight = float(data.get('weight', 0))
        bmi_category = get_bmi_category(height, weight)
        
        # Determine scores and status
        lifestyle_score = get_lifestyle_score(data)
        symptom_score = get_symptom_score(data)
        health_score = get_health_status(overall_score)
        
        # Generate analysis points
        strengths = []
        improvements = []
        recommendations = []
        
        # Analyze lifestyle factors
        if data.get('sleep_quality') == 'good':
            strengths.append("Maintaining healthy sleep habits")
        elif data.get('sleep_quality') == 'poor':
            improvements.append("Sleep quality needs attention")
            recommendations.append("Establish a consistent sleep schedule and create a relaxing bedtime routine")
            
        if data.get('exercise_frequency') == 'high':
            strengths.append("Regular exercise routine")
        elif data.get('exercise_frequency') == 'low':
            improvements.append("Physical activity level is low")
            recommendations.append("Aim for at least 30 minutes of moderate exercise 3-4 times per week")
            
        if data.get('stress_level') == 'low':
            strengths.append("Good stress management")
        elif data.get('stress_level') == 'high':
            improvements.append("High stress levels detected")
            recommendations.append("Consider stress-reduction techniques like meditation, yoga, or deep breathing exercises")
            
        if data.get('diet_quality') in ['excellent', 'good']:
            strengths.append("Maintaining a healthy diet")
        elif data.get('diet_quality') == 'poor':
            improvements.append("Diet quality needs improvement")
            recommendations.append("Focus on incorporating more whole foods, fruits, vegetables, and lean proteins")
            
        # Analyze symptoms
        symptoms = data.get('symptoms', [])
        if symptoms:
            improvements.append(f"Managing {len(symptoms)} reported symptoms")
            if 'hot_flashes' in symptoms:
                recommendations.append("Stay hydrated and avoid trigger foods that may cause hot flashes")
                
        # Analyze medical conditions
        conditions = data.get('medical_conditions', [])
        if conditions:
            if 'diabetes' in conditions:
                recommendations.append("Monitor blood sugar levels regularly and maintain a balanced diet")
                
        # Add general recommendations if needed
        if not recommendations:
            recommendations.extend([
                "Continue maintaining your current healthy lifestyle habits",
                "Schedule regular check-ups with your healthcare provider",
                "Stay hydrated and maintain a balanced diet"
            ])

        return render_template('hormonal_balance_dashboard.html',
                             data=data,
                             overall_score=overall_score,
                             bmi_category=bmi_category,
                             lifestyle_score=lifestyle_score,
                             symptom_score=symptom_score,
                             health_score=health_score,
                             strengths=strengths,
                             improvements=improvements,
                             recommendations=recommendations)
                             
    except Exception as e:
        error_msg = f"Error in dashboard: {str(e)}"
        logging.error(error_msg)
        return render_template('error.html', 
                             error="Could not load the dashboard. Please try again later.")

def get_lifestyle_score(data):
    """Calculate and return lifestyle score category"""
    score = 0
    if data.get('sleep_quality') == 'good': score += 25
    if data.get('exercise_frequency') == 'high': score += 25
    if data.get('stress_level') == 'low': score += 25
    if data.get('diet_quality') in ['excellent', 'good']: score += 25
    
    if score >= 75: return "Excellent"
    elif score >= 50: return "Good"
    else: return "Needs Improvement"

def get_symptom_score(data):
    """Analyze symptoms and return category"""
    symptoms = data.get('symptoms', [])
    if not symptoms:
        return "Optimal"
    elif len(symptoms) <= 2:
        return "Mild"
    elif len(symptoms) <= 4:
        return "Moderate"
    else:
        return "Significant"

def get_health_status(score):
    """Convert overall score to health status category"""
    if score >= 90:
        return "Optimal"
    elif score >= 75:
        return "Good"
    elif score >= 60:
        return "Fair"
    else:
        return "Needs Attention"

@hormonal_balance.route('/form')
def show_form():
    """Show the form"""
    try:
        return render_template('hormonal_balance_form.html',
                             title="Hormonal Balance Analysis",
                             active_page="hormonal_balance")
    except Exception as e:
        logging.error(f"Error showing form: {str(e)}")
        return render_template('error.html', 
                             error="Could not load the form. Please try again later.")
