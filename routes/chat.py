from flask import Blueprint, jsonify, request
from flask_login import login_required
import os
from groq import Groq

chat_bp = Blueprint('chat', __name__)

# Initialize Groq client
client = Groq(
    api_key=os.environ.get('GROQ_API_KEY')
)


@chat_bp.route('/api/chat', methods=['POST'])
@login_required
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '')

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

        return jsonify({
            'response': response,
            'error': None
        })

    except Exception as e:
        error_message = "Sorry, there was an error processing your message. Please try again."
        return jsonify({
            'response': None,
            'error': error_message
        }), 500

# Welcome message
WELCOME_MESSAGE = "Hello! I'm your AI assistant. How can I help you with your menopause journey today?"

@chat_bp.route('/api/chat/welcome', methods=['GET'])
def get_welcome_message():
    return jsonify({
        'message': WELCOME_MESSAGE
    })
