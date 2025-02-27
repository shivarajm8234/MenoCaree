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
    data = request.form
    
    # Get form data
    age = data.get('age', type=int)
    last_period = data.get('last_period', type=int)
    symptoms = request.form.getlist('symptoms')
    
    if not all([age, last_period, symptoms]):
        return jsonify({'error': 'Please provide all required information'}), 400
    
    # Store in session for reference
    session['menopause_data'] = {
        'age': age,
        'last_period': last_period,
        'symptoms': symptoms
    }
    
    # Get analysis from Groq
    analysis = get_menopause_analysis(symptoms, age, last_period)
    
    return render_template('menopause/results.html', 
                         age=age,
                         last_period=last_period,
                         symptoms=symptoms,
                         analysis=analysis)
