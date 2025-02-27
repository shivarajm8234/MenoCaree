import os
import json
from flask import jsonify, session

# Language names in their native script
LANGUAGE_NAMES = {
    'en': 'English (US)'
}

# Default translations (English)
DEFAULT_TRANSLATIONS = {
    'title': 'AI Chat Support',
    'subtitle': 'Get personalized support and answers to your questions',
    'welcome': "Hello! I'm your AI assistant. How can I help you with your menopause journey today?",
    'quick_topics': 'Quick Topics:',
    'hot_flashes': 'Hot Flashes',
    'sleep_issues': 'Sleep Issues',
    'mood_changes': 'Mood Changes',
    'chat_placeholder': 'Type your message...',
    'privacy_notice': 'Your conversations are private and secure. We use AI to provide personalized support while maintaining your confidentiality.',
    'error_message': 'An error occurred. Please try again.'
}

def load_translations(lang_code):
    """Load translations for a specific language from JSON file"""
    try:
        translation_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'translations',
            f'{lang_code}.json'
        )
        with open(translation_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            # Merge with default translations to ensure all keys exist
            return {**DEFAULT_TRANSLATIONS, **translations}
    except Exception as e:
        print(f"Error loading translations for {lang_code}: {e}")
        return DEFAULT_TRANSLATIONS

def get_user_language():
    """Get the current user's language preference"""
    return session.get('language', 'en')

def set_user_language(lang_code):
    """Set the user's language preference"""
    if lang_code in LANGUAGE_NAMES:
        session['language'] = lang_code
        return jsonify({'status': 'success'})
    return jsonify({
        'status': 'error',
        'message': 'Language not supported'
    })

def get_translations():
    """Get translations for the current user's language"""
    lang = get_user_language()
    return load_translations(lang)

def get_language_data():
    """Get all language-related data for templates"""
    lang = get_user_language()
    return {
        'translations': get_translations(),
        'language_names': LANGUAGE_NAMES,
        'current_language': LANGUAGE_NAMES[lang]
    }
