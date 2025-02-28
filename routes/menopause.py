from flask import Blueprint, render_template, request, jsonify, session
import groq
import os

menopause = Blueprint('menopause', __name__)
groq_client = groq.Client(api_key=os.getenv('GROQ_API_KEY'))

def get_menopause_analysis(symptoms, age, last_period):
    prompt = f"""Analyze the following menopause-related information and provide detailed insights:
    Age: {age}
    Months since last period: {last_period}
    Symptoms: {', '.join(symptoms)}
    
    Please provide analysis in the following format:
    1. Stage of Menopause
    2. Symptom Analysis
    3. Recommended Lifestyle Changes
    4. Treatment Options
    5. Next Steps
    
    Make the response informative yet compassionate."""

    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a knowledgeable healthcare assistant specializing in menopause care."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="mixtral-8x7b-32768",
        temperature=0.7,
        max_tokens=1024
    )
    
    return chat_completion.choices[0].message.content

@menopause.route('/')
def index():
    return render_template('menopause/index.html')

@menopause.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.form
        
        # Get and validate form data
        age = data.get('age', type=int)
        last_period = data.get('last_period', type=int)
        symptoms = request.form.getlist('symptoms')
        other_symptoms_details = request.form.get('other_symptoms_details', '').strip()
        
        # Validate age
        if not age or age < 35 or age > 65:
            return jsonify({'error': 'Please enter a valid age between 35 and 65 years.'}), 400
        
        # Validate months since last period
        if not last_period or last_period < 0 or last_period > 120:
            return jsonify({'error': 'Please enter a valid number of months since your last period (0-120).'}), 400
        
        if not symptoms:
            return jsonify({'error': 'Please select at least one symptom.'}), 400
        
        # Process symptoms
        processed_symptoms = []
        for symptom in symptoms:
            if symptom == 'Other Symptoms' and other_symptoms_details:
                processed_symptoms.append(f"Other Symptoms: {other_symptoms_details}")
            else:
                processed_symptoms.append(symptom)
        
        # Determine menopause stage
        stage = 'Perimenopause'
        if last_period >= 12:
            stage = 'Postmenopause'
        elif last_period < 2:
            stage = 'Perimenopause (Early)'
        else:
            stage = 'Perimenopause (Late)'
        
        # Store in session for reference
        session['menopause_data'] = {
            'age': age,
            'last_period': last_period,
            'symptoms': processed_symptoms,
            'stage': stage
        }
        
        # Get analysis from Groq
        analysis = get_menopause_analysis(processed_symptoms, age, last_period)
        
        return render_template('menopause/results.html', 
                             age=age,
                             last_period=last_period,
                             symptoms=processed_symptoms,
                             stage=stage,
                             analysis=analysis)
                             
    except Exception as e:
        return jsonify({'error': 'An error occurred while processing your information. Please try again.'}), 500
