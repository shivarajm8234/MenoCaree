from flask import Blueprint, jsonify, request
from flask_login import login_required
import os
import logging
from groq import Groq
from deep_translator import GoogleTranslator

# Set up logging
logging.basicConfig(level=logging.DEBUG)

chat_bp = Blueprint('chat', __name__)

# Initialize Groq client
try:
    client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
    logging.info("Groq client initialized successfully in chat.py")
except Exception as e:
    logging.error("Failed to initialize Groq client in chat.py: %s", str(e))
    client = None
translator = Translator()

# Language codes for translation
LANGUAGE_CODES = {
    'en-US': 'en',  # English
    'hi-IN': 'hi',  # Hindi
    'ta-IN': 'ta',  # Tamil
    'te-IN': 'te',  # Telugu
    'kn-IN': 'kn',  # Kannada
    'ml-IN': 'ml',  # Malayalam
    'mr-IN': 'mr',  # Marathi
    'gu-IN': 'gu',  # Gujarati
    'bn-IN': 'bn'   # Bengali
}

@chat_bp.route('/api/chat', methods=['POST'])
@login_required
def chat():
    try:
        # Verify Groq client is initialized
        if not client:
            error_message = "Chat service is temporarily unavailable. Please try again later."
            return jsonify({
                'response': None,
                'error': error_message
            }), 503

        data = request.get_json()
        message = data.get('message', '')
        language_code = data.get('language', 'en-US')
        
        # Get the target language code for translation
        target_lang = LANGUAGE_CODES.get(language_code, 'en')
        
        # If message is not in English, translate it to English for the AI
        if target_lang != 'en':
            translator = GoogleTranslator(source=target_lang, target='en')
            message = translator.translate(text=message)

        # Create chat completion with Groq
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a knowledgeable and empathetic AI assistant specializing in menopause-related topics. Provide accurate, helpful, and supportive responses."
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
            model="mixtral-8x7b-32768",
            temperature=0,
            max_tokens=2048,
            top_p=1,
            stream=False
        )

        # Get the AI's response
        response = chat_completion.choices[0].message.content

        # If target language is not English, translate the response
        if target_lang != 'en':
            translator = GoogleTranslator(source='en', target=target_lang)
            response = translator.translate(text=response)

        return jsonify({
            'response': response,
            'error': None
        })

    except Exception as e:
        # Get error message in the target language
        error_message = "Sorry, there was an error processing your message. Please try again."
        if target_lang != 'en':
            try:
                translator = GoogleTranslator(source='en', target=target_lang)
                error_message = translator.translate(text=error_message)
            except:
                pass  # If translation fails, use English error message
                
        return jsonify({
            'response': None,
            'error': error_message
        }), 500

# Add welcome messages in different languages
WELCOME_MESSAGES = {
    'en-US': "Hello! I'm your AI assistant. How can I help you with your menopause journey today?",
    'hi-IN': "नमस्ते! मैं आपका AI सहायक हूं। आज मैं आपकी मेनोपॉज यात्रा में कैसे मदद कर सकता हूं?",
    'ta-IN': "வணக்கம்! நான் உங்கள் AI உதவியாளர். இன்று உங்கள் மாதவிடாய் நிறுத்த பயணத்தில் நான் எவ்வாறு உதவ முடியும்?",
    'te-IN': "నమస్కారం! నేను మీ AI సహాయకుడిని. ఈరోజు మీ మెనోపాజ్ ప్రయాణంలో నేను ఎలా సహాయపడగలను?",
    'kn-IN': "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ AI ಸಹಾಯಕ. ಇಂದು ನಿಮ್ಮ ಮೆನೋಪಾಸ್ ಪ್ರಯಾಣದಲ್ಲಿ ನಾನು ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?",
    'ml-IN': "നമസ്കാരം! ഞാൻ നിങ്ങളുടെ AI അസിസ്റ്റന്റ് ആണ്. ഇന്ന് നിങ്ങളുടെ മെനോപോസ് യാത്രയിൽ എനിക്ക് എങ്ങനെ സഹായിക്കാൻ കഴിയും?",
    'mr-IN': "नमस्कार! मी तुमचा AI सहाय्यक आहे. आज मी तुमच्या मेनोपॉझ प्रवासात कशी मदत करू शकतो?",
    'gu-IN': "નમસ્તે! હું તમારો AI સહાયક છું. આજે હું તમારી મેનોપોઝ યાત્રામાં કેવી રીતે મદદ કરી શકું?",
    'bn-IN': "নমস্কার! আমি আপনার AI সহকারী। আজ আমি আপনার মেনোপজ যাত্রায় কীভাবে সাহায্য করতে পারি?"
}

@chat_bp.route('/api/chat/welcome', methods=['GET'])
def get_welcome_message():
    language = request.args.get('language', 'en-US')
    return jsonify({
        'message': WELCOME_MESSAGES.get(language, WELCOME_MESSAGES['en-US'])
    })
