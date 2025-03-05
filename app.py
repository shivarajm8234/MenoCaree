import os
from dotenv import load_dotenv
import groq
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from database import Database
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import logging
import plotly.graph_objs as go
from plotly.utils import PlotlyJSONEncoder
import json
from datetime import datetime, timedelta
import re
from functools import wraps
from routes.language import get_language_data
import time
import sqlite3
import io
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.colors import HexColor
import PyPDF2
import pytesseract
from PIL import Image
import fitz  # PyMuPDF for PDF processing

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')
app.config['UPLOAD_FOLDER'] = 'uploads'

# Initialize Groq client with API key from environment
try:
    groq_api_key = os.getenv('GROQ_API_KEY')
    if groq_api_key:
        groq_client = groq.Groq(api_key=groq_api_key)
    else:
        print('Warning: GROQ_API_KEY not found in environment variables')
        groq_client = None
except Exception as e:
    print(f'Warning: Failed to initialize Groq client: {e}')
    groq_client = None

# Register blueprints
from routes.period_health import period_health
from routes.hormonal_balance import hormonal_balance
from routes.games import games
from routes.pregnancy import pregnancy
from routes.chat import chat_bp

app.register_blueprint(period_health)
app.register_blueprint(hormonal_balance, url_prefix='/hormonal-balance')
app.register_blueprint(games)
app.register_blueprint(pregnancy, url_prefix='/pregnancy')
app.register_blueprint(chat_bp)

# Initialize database
db = Database()

# Initialize cycle data cache
CYCLE_DATA_CACHE = {}

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Auth routes
@app.route('/')
@login_required
def home():
    """Home page"""
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please provide both email and password.')
            return redirect(url_for('login'))
            
        try:
            user = db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))
            
            if user and check_password_hash(user['password_hash'], password):
                session.clear()
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['_fresh'] = True
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)
                
                return redirect(url_for('home'))
            else:
                flash('Invalid email or password.')
        except Exception as e:
            flash('An error occurred. Please try again later.')
            print(f"Login error: {str(e)}")
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        existing_user = db.fetch_one("SELECT * FROM users WHERE email = %s OR username = %s", (email, username))
        if existing_user:
            flash('Email or username already exists.')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        try:
            db.execute_query(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, hashed_password)
            )
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Registration failed. Please try again.')
            print(f"Registration error: {e}")
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Clear session and logout user"""
    user_id = session.get('user_id')
    if user_id in CYCLE_DATA_CACHE:
        del CYCLE_DATA_CACHE[user_id]
    session.clear()
    return redirect(url_for('login'))

@app.route('/clear_cache', methods=['POST'])
@login_required
def clear_cache():
    """Clear all cache data from session"""
    # Keep only essential user data
    user_id = session.get('user_id')
    username = session.get('username')
    
    # Clear everything else
    session.clear()
    
    # Restore essential user data
    session['user_id'] = user_id
    session['username'] = username
    session.modified = True
    
    return jsonify({
        'success': True,
        'message': 'Cache cleared successfully'
    })

# Symptom routes
@app.route('/symptom-tracker')
@login_required
def symptom_tracker():
    return render_template('symptom_tracker.html')

@app.route('/api/symptoms', methods=['POST'])
@login_required
def log_symptoms():
    data = request.json
    try:
        for symptom in data['symptoms']:
            db.execute_query(
                """INSERT INTO symptoms (user_id, symptom_name, severity, notes) 
                   VALUES (%s, %s, %s, %s)""",
                (session['user_id'], symptom['name'], symptom['severity'], data.get('notes', ''))
            )
        return jsonify({'message': 'Symptoms logged successfully'})
    except Exception as e:
        print(f"Error logging symptoms: {e}")
        return jsonify({'error': 'Failed to log symptoms'}), 500

@app.route('/api/symptoms/history')
@login_required
def get_symptom_history():
    try:
        symptoms = db.fetch_all(
            """SELECT symptom_name, severity, notes, recorded_at 
               FROM symptoms WHERE user_id = %s 
               ORDER BY recorded_at DESC""",
            (session['user_id'],)
        )
        return jsonify(symptoms)
    except Exception as e:
        print(f"Error fetching symptom history: {e}")
        return jsonify({'error': 'Failed to fetch symptom history'}), 500

# Community routes
# Predefined forum groups and their topics with permanent messages
menopause_support_topics = {
    'hot_flashes': [
        {
            'username': 'CoolBreeze',
            'message': 'Just discovered that keeping a cold water spray bottle by my bed helps immensely with night sweats!',
            'timestamp': '2025-01-01 20:15:00'
        },
        {
            'username': 'NightComfort',
            'message': '@CoolBreeze That is a great tip! Do you add any essential oils to the water?',
            'timestamp': '2025-01-01 20:30:00'
        },
        {
            'username': 'CoolBreeze',
            'message': '@NightComfort Yes! I add a few drops of lavender - helps with sleep too!',
            'timestamp': '2025-01-01 20:45:00'
        },
        {
            'username': 'HotFlashHelper',
            'message': 'My doctor suggested avoiding spicy foods and caffeine after 4 PM. It has really reduced my night sweats.',
            'timestamp': '2025-01-01 21:00:00'
        },
        {
            'username': 'MindfulJourney',
            'message': '@CoolBreeze What kind of fan do you use? I need something quiet for the office.',
            'timestamp': '2025-01-01 21:15:00'
        },
        {
            'username': 'CoolBreeze',
            'message': '@MindfulJourney I use a small USB desk fan. It is super quiet and has 3 speeds. I can send you the link!',
            'timestamp': '2025-01-01 21:30:00'
        }
    ],
    'sleep_tips': [
        {
            'username': 'RestSeeker',
            'message': 'Started using a white noise machine last week. Finally getting more than 4 hours of continuous sleep!',
            'timestamp': '2025-01-01 19:00:00'
        },
        {
            'username': 'SleepExpert',
            'message': '@RestSeeker That is fantastic! Which model did you get?',
            'timestamp': '2025-01-01 19:15:00'
        },
        {
            'username': 'RestSeeker',
            'message': '@SleepExpert I got the SleepMate Classic. It has different sound options but I love the rain sound.',
            'timestamp': '2025-01-01 19:30:00'
        },
        {
            'username': 'NightPeace',
            'message': 'My sleep improved after I started taking magnesium glycinate supplements. Always check with your doctor first though!',
            'timestamp': '2025-01-01 20:00:00'
        },
        {
            'username': 'DreamCatcher',
            'message': 'The 4-7-8 breathing technique helps me fall back asleep when I wake up at night. Anyone else tried it?',
            'timestamp': '2025-01-01 20:30:00'
        },
        {
            'username': 'PeacefulNights',
            'message': '@DreamCatcher Yes! It works wonders. I combine it with progressive muscle relaxation.',
            'timestamp': '2025-01-01 21:00:00'
        }
    ]
}

lifestyle_topics = {
    'exercise_routines': [
        {
            'username': 'FitAndFabulous',
            'message': 'Started water aerobics classes - perfect for staying cool while exercising!',
            'timestamp': '2025-01-01 18:00:00'
        },
        {
            'username': 'AquaLover',
            'message': '@FitAndFabulous How many times a week do you go? I am thinking of joining.',
            'timestamp': '2025-01-01 18:15:00'
        },
        {
            'username': 'FitAndFabulous',
            'message': '@AquaLover I go 3 times a week. The Tuesday morning class is especially good!',
            'timestamp': '2025-01-01 18:30:00'
        },
        {
            'username': 'YogaFan',
            'message': 'Found a great YouTube channel with gentle yoga specifically for menopause. Anyone interested?',
            'timestamp': '2025-01-01 19:00:00'
        },
        {
            'username': 'StretchLover',
            'message': '@YogaFan Yes please! Would love the link.',
            'timestamp': '2025-01-01 19:15:00'
        },
        {
            'username': 'YogaFan',
            'message': '@StretchLover Sent you a DM with the link. The morning routine is my favorite!',
            'timestamp': '2025-01-01 19:30:00'
        }
    ],
    'diet_changes': [
        {
            'username': 'HealthyPlate',
            'message': 'Made a delicious smoothie with flax seeds and berries this morning. Great for omega-3s!',
            'timestamp': '2025-01-01 17:00:00'
        },
        {
            'username': 'NutriSeeker',
            'message': '@HealthyPlate Would you share the recipe? Always looking for healthy breakfast ideas.',
            'timestamp': '2025-01-01 17:15:00'
        },
        {
            'username': 'HealthyPlate',
            'message': '@NutriSeeker Sure! 1 cup berries, 1 tbsp flax seeds, 1 cup almond milk, handful of spinach, and a banana. Enjoy!',
            'timestamp': '2025-01-01 17:30:00'
        },
        {
            'username': 'MindfulEater',
            'message': 'Anyone tried eliminating sugar? Notice any difference in symptoms?',
            'timestamp': '2025-01-01 18:00:00'
        },
        {
            'username': 'SugarFree',
            'message': '@MindfulEater Yes! Reduced my hot flashes significantly. First week was hard but so worth it.',
            'timestamp': '2025-01-01 18:15:00'
        },
        {
            'username': 'WellnessJourney',
            'message': 'Just discovered chickpea pasta - great protein source and helps keep blood sugar stable!',
            'timestamp': '2025-01-01 18:30:00'
        }
    ]
}

# Pre-defined messages for Lifestyle Changes Group
LIFESTYLE_MESSAGES = {
    'exercise_movement': [
        {
            'username': 'FitnessCoach',
            'message': 'Welcome to Exercise & Movement! Here are some gentle exercises to start with:\n1. Walking: 30 minutes daily\n2. Yoga: Focus on cooling poses\n3. Swimming: Great for joint health',
            'timestamp': '2025-01-01 08:00:00'
        },
        {
            'username': 'YogaLover',
            'message': 'I\'ve found morning yoga really helps with my symptoms. Anyone else tried this?',
            'timestamp': '2025-01-01 08:30:00'
        },
        {
            'username': 'WalkingQueen',
            'message': 'Daily walks have been a game-changer for me. I do 20 minutes in the morning and evening.',
            'timestamp': '2025-01-01 09:00:00'
        }
    ],
    'nutrition_diet': [
        {
            'username': 'NutritionExpert',
            'message': 'Welcome to Nutrition & Diet! Some tips for managing symptoms:\n1. Eat more whole grains\n2. Include plenty of fruits and vegetables\n3. Stay hydrated\n4. Limit caffeine and alcohol',
            'timestamp': '2025-01-01 08:00:00'
        },
        {
            'username': 'HealthyEater',
            'message': 'Adding flaxseeds to my breakfast has really helped with hot flashes!',
            'timestamp': '2025-01-01 08:30:00'
        },
        {
            'username': 'CookingPro',
            'message': 'Here\'s my favorite cooling smoothie recipe: cucumber, mint, apple, and coconut water.',
            'timestamp': '2025-01-01 09:00:00'
        }
    ]
}

FORUM_GROUPS = {
    'symptoms_support': {
        'name': 'Symptoms Support Group',
        'description': 'Share and discuss various menopause symptoms and management techniques',
        'topics': {
            'hot_flashes': {
                'title': 'Hot Flashes & Night Sweats',
                'messages': [
                    {
                        'username': 'MenoCare_Admin',
                        'message': 'Welcome to the Hot Flashes discussion. Here are some common management techniques:\n- Keep a portable fan handy\n- Dress in layers\n- Stay hydrated\n- Practice deep breathing',
                        'timestamp': '2025-01-01 00:00:00'
                    },
                    {
                        'username': 'CoolBreeze55',
                        'message': 'I discovered that bamboo sheets help a lot with night sweats! They are more breathable than cotton.',
                        'timestamp': '2025-01-01 20:30:00'
                    },
                    {
                        'username': 'NatureLover',
                        'message': '@CoolBreeze55 Which brand do you recommend? I need to replace my sheets.',
                        'timestamp': '2025-01-01 20:45:00'
                    },
                    {
                        'username': 'CoolBreeze55',
                        'message': '@NatureLover I use BambooComfort sheets - a bit pricey but worth every penny!',
                        'timestamp': '2025-01-01 21:00:00'
                    },
                    {
                        'username': 'EssentialCalm',
                        'message': 'My favorite cooling spray recipe: Mix peppermint and lavender essential oils with water. So refreshing!',
                        'timestamp': '2025-01-01 21:15:00'
                    },
                    {
                        'username': 'HotFlashFighter',
                        'message': 'Has anyone tried those cooling neck wraps? Thinking of getting one for work.',
                        'timestamp': '2025-01-01 21:30:00'
                    },
                    {
                        'username': 'WellnessGuide',
                        'message': '@HotFlashFighter Yes! The FreezeFlex neck wrap stays cold for hours. Great for the office!',
                        'timestamp': '2025-01-01 21:45:00'
                    }
                ]
            },
            'sleep_issues': {
                'title': 'Sleep Problems & Solutions',
                'messages': [
                    {
                        'username': 'MenoCare_Admin',
                        'message': 'Good sleep hygiene tips:\n- Maintain a regular sleep schedule\n- Keep your bedroom cool\n- Avoid screens before bedtime\n- Practice relaxation techniques',
                        'timestamp': '2025-01-01 00:00:00'
                    },
                    {
                        'username': 'SleepSeeker22',
                        'message': 'The SleepSound white noise machine changed my life! I use the ocean waves setting.',
                        'timestamp': '2025-01-01 20:00:00'
                    },
                    {
                        'username': 'NightOwl',
                        'message': '@SleepSeeker22 Do you use it all night or with a timer?',
                        'timestamp': '2025-01-01 20:15:00'
                    },
                    {
                        'username': 'SleepSeeker22',
                        'message': '@NightOwl All night - it helps me fall back asleep if I wake up.',
                        'timestamp': '2025-01-01 20:30:00'
                    },
                    {
                        'username': 'CalmMind',
                        'message': 'The 4-7-8 breathing technique really helps: Inhale for 4, hold for 7, exhale for 8 counts.',
                        'timestamp': '2025-01-01 21:00:00'
                    },
                    {
                        'username': 'SleepHelper',
                        'message': 'Taking magnesium before bed has improved my sleep quality significantly!',
                        'timestamp': '2025-01-01 21:15:00'
                    },
                    {
                        'username': 'RestfulNights',
                        'message': '@SleepHelper Which magnesium supplement do you take? There are so many!',
                        'timestamp': '2025-01-01 21:30:00'
                    }
                ]
            }
        }
    },
    'lifestyle_changes': {
        'name': 'Lifestyle Changes Group',
        'description': 'Share and discuss lifestyle modifications for managing menopause symptoms',
        'topics': {
            'exercise_movement': {
                'title': 'Exercise & Movement',
                'description': 'Share exercise tips, routines, and experiences',
                'messages': LIFESTYLE_MESSAGES['exercise_movement']
            },
            'nutrition_diet': {
                'title': 'Nutrition & Diet',
                'description': 'Discuss dietary changes, recipes, and nutrition tips',
                'messages': LIFESTYLE_MESSAGES['nutrition_diet']
            }
        }
    }
}

# Sample user messages for topics
SAMPLE_MESSAGES = {
    'hot_flashes': [
        {
            'username': 'Sarah123',
            'message': 'I found that keeping a small fan at my desk really helps during work hours. Also, dressing in layers makes it easier to adjust when hot flashes hit.',
            'timestamp': '2025-01-01 10:15:00'
        },
        {
            'username': 'Emma_W',
            'message': 'My doctor recommended some breathing exercises that have been really helpful. Deep breaths when you feel a hot flash coming can make them less intense.',
            'timestamp': '2025-01-01 11:30:00'
        },
        {
            'username': 'CoolBreeze',
            'message': 'Peppermint tea has been a lifesaver for me. It helps cool down the body naturally.',
            'timestamp': '2025-01-01 12:45:00'
        },
        {
            'username': 'MindfulJourney',
            'message': '@Sarah123 What kind of fan do you use? I need something quiet for the office.',
            'timestamp': '2025-01-01 13:00:00'
        },
        {
            'username': 'Sarah123',
            'message': '@MindfulJourney I use a small USB desk fan. It is super quiet and has 3 speeds. I can send you the link!',
            'timestamp': '2025-01-01 13:15:00'
        },
        {
            'username': 'WellnessSeeker',
            'message': 'Has anyone tried acupuncture for hot flashes? My friend recommended it.',
            'timestamp': '2025-01-01 14:30:00'
        },
        {
            'username': 'Emma_W',
            'message': '@WellnessSeeker Yes! I do acupuncture twice a month. It took a few sessions but really helps with the frequency of hot flashes.',
            'timestamp': '2025-01-01 15:00:00'
        }
    ],
    'sleep_issues': [
        {
            'username': 'NightOwl',
            'message': 'Magnesium supplements before bed have made a huge difference in my sleep quality. Also, keeping the bedroom cool and dark helps.',
            'timestamp': '2025-01-01 09:20:00'
        },
        {
            'username': 'SleepSeeker',
            'message': 'I started doing yoga before bed and it has helped tremendously with sleep. The relaxation techniques are especially useful.',
            'timestamp': '2025-01-01 12:45:00'
        },
        {
            'username': 'PeacefulRest',
            'message': 'Creating a bedtime routine has helped me a lot. I dim the lights and read for 30 minutes before bed.',
            'timestamp': '2025-01-01 14:30:00'
        },
        {
            'username': 'DreamCatcher',
            'message': '@NightOwl Which magnesium supplement do you take? There are so many types!',
            'timestamp': '2025-01-01 15:45:00'
        },
        {
            'username': 'NightOwl',
            'message': '@DreamCatcher I use magnesium glycinate. It is gentle on the stomach and really effective.',
            'timestamp': '2025-01-01 16:00:00'
        },
        {
            'username': 'SleepWell',
            'message': 'The meditation app Calm has been great for me. They have special meditations for menopause sleep issues.',
            'timestamp': '2025-01-01 17:15:00'
        },
        {
            'username': 'PeacefulRest',
            'message': '@SleepWell Thanks for the tip! Just downloaded the app. Looking forward to trying it tonight.',
            'timestamp': '2025-01-01 17:30:00'
        }
    ],
    'exercise': [
        {
            'username': 'FitAt50',
            'message': 'I do 30 minutes of walking every morning and some light weights. It helps with mood and energy levels throughout the day.',
            'timestamp': '2025-01-01 08:30:00'
        },
        {
            'username': 'YogaLover',
            'message': 'Found a great menopause-focused yoga class at my local studio. The instructor really understands our needs.',
            'timestamp': '2025-01-01 13:15:00'
        },
        {
            'username': 'ActiveLife',
            'message': 'Swimming has been amazing for me. It keeps me cool and is gentle on the joints.',
            'timestamp': '2025-01-01 15:45:00'
        },
        {
            'username': 'StrongSpirit',
            'message': '@FitAt50 Do you use any specific workout videos for the weights routine?',
            'timestamp': '2025-01-01 16:00:00'
        },
        {
            'username': 'FitAt50',
            'message': '@StrongSpirit Yes! I follow Silver Sneakers on YouTube. They have great beginner-friendly videos.',
            'timestamp': '2025-01-01 16:30:00'
        },
        {
            'username': 'WalkingQueen',
            'message': 'Just got a fitness tracker and it is so motivating to see my daily steps increase!',
            'timestamp': '2025-01-01 17:45:00'
        },
        {
            'username': 'YogaLover',
            'message': '@WalkingQueen Which tracker did you get? I am thinking of getting one too.',
            'timestamp': '2025-01-01 18:00:00'
        }
    ],
    'nutrition': [
        {
            'username': 'HealthyEats',
            'message': 'Adding more calcium-rich foods and reducing caffeine has helped with my symptoms. Also drinking plenty of water!',
            'timestamp': '2025-01-01 14:20:00'
        },
        {
            'username': 'WellnessJourney',
            'message': 'I have been incorporating more soy products into my diet. The plant estrogens seem to help with hot flashes.',
            'timestamp': '2025-01-01 15:45:00'
        },
        {
            'username': 'NutriBalance',
            'message': 'Found that eating smaller, frequent meals helps maintain stable blood sugar and reduces mood swings.',
            'timestamp': '2025-01-01 16:30:00'
        },
        {
            'username': 'FoodLover',
            'message': '@HealthyEats Can you share some of your favorite calcium-rich recipes?',
            'timestamp': '2025-01-01 17:00:00'
        },
        {
            'username': 'HealthyEats',
            'message': '@FoodLover Sure! I make a great smoothie with greek yogurt, almonds, and leafy greens. Will post the full recipe later!',
            'timestamp': '2025-01-01 17:15:00'
        },
        {
            'username': 'GreenGoddess',
            'message': 'Anyone tried seed cycling? It is supposed to help balance hormones naturally.',
            'timestamp': '2025-01-01 18:30:00'
        },
        {
            'username': 'WellnessJourney',
            'message': '@GreenGoddess Yes! I do flax and pumpkin seeds first half of the month, then sunflower and sesame seeds. Really helps!',
            'timestamp': '2025-01-01 19:00:00'
        }
    ],
    'general_discussion': [
        {
            'username': 'NewHere',
            'message': 'Hi everyone! Just joined the group. Looking forward to connecting with others on this journey.',
            'timestamp': '2025-01-01 10:00:00'
        },
        {
            'username': 'SupportiveHeart',
            'message': '@NewHere Welcome! You will find lots of support here. Feel free to ask any questions!',
            'timestamp': '2025-01-01 10:15:00'
        },
        {
            'username': 'MenoWarrior',
            'message': 'Having a rough day with symptoms. Any tips for staying positive?',
            'timestamp': '2025-01-01 11:30:00'
        },
        {
            'username': 'JoyfulSpirit',
            'message': '@MenoWarrior Sending hugs! I find journaling helps me track good days and remember this is temporary.',
            'timestamp': '2025-01-01 11:45:00'
        },
        {
            'username': 'HopeSeeker',
            'message': '@MenoWarrior Also try to celebrate small wins. Even getting through a tough day is an achievement!',
            'timestamp': '2025-01-01 12:00:00'
        }
    ],
    'introductions': [
        {
            'username': 'BeginnerHere',
            'message': 'Hello everyone! I am Lisa, 48, just starting to experience perimenopause symptoms.',
            'timestamp': '2025-01-01 09:00:00'
        },
        {
            'username': 'WarmWelcome',
            'message': '@BeginnerHere Welcome Lisa! You are in the right place. What symptoms are you experiencing?',
            'timestamp': '2025-01-01 09:15:00'
        },
        {
            'username': 'BeginnerHere',
            'message': '@WarmWelcome Mainly hot flashes and sleep issues. It is all so new and a bit overwhelming!',
            'timestamp': '2025-01-01 09:30:00'
        },
        {
            'username': 'ExperiencedFriend',
            'message': '@BeginnerHere We have all been there! Check out the hot flashes and sleep issues topics for some great tips.',
            'timestamp': '2025-01-01 09:45:00'
        },
        {
            'username': 'BeginnerHere',
            'message': '@ExperiencedFriend Thank you! Will do that now. So glad I found this supportive community!',
            'timestamp': '2025-01-01 10:00:00'
        }
    ]
}

def get_default_messages(topic_name):
    """Generate default messages for new topics"""
    return [
        {
            'username': 'WelcomeGuide',
            'message': f'Welcome to our {topic_name} discussion! Looking forward to sharing experiences.',
            'timestamp': '2025-01-01 09:00:00'
        },
        {
            'username': 'SupportCircle',
            'message': 'This is a safe space to share and learn from each other. Every experience is valuable!',
            'timestamp': '2025-01-01 09:15:00'
        },
        {
            'username': 'MenoCare_Admin',
            'message': 'Feel free to ask questions and support others. We are all in this together!',
            'timestamp': '2025-01-01 09:30:00'
        },
        {
            'username': 'CommunityHelper',
            'message': 'Remember to be respectful and supportive in your responses. Your experiences matter!',
            'timestamp': '2025-01-01 09:45:00'
        },
        {
            'username': 'TopicStarter',
            'message': f'What aspects of {topic_name} would you like to discuss? Share your thoughts!',
            'timestamp': '2025-01-01 10:00:00'
        }
    ]

# Cache for storing user-created groups
USER_CREATED_GROUPS = {}

def get_forum_groups():
    """Get all forum groups including pre-defined and user-created ones"""
    # Combine pre-defined groups with user-created groups
    all_groups = FORUM_GROUPS.copy()
    all_groups.update(USER_CREATED_GROUPS)
    return all_groups

def save_forum_groups(groups):
    """Save only user-created groups to cache"""
    global USER_CREATED_GROUPS
    # Only save groups that aren't in FORUM_GROUPS (user-created ones)
    USER_CREATED_GROUPS.update({
        group_id: group_data
        for group_id, group_data in groups.items()
        if group_id not in FORUM_GROUPS
    })

# Store groups in session to persist changes
def init_session_data():
    """Initialize session data for forum"""
    if 'forum_data' not in session:
        session['forum_data'] = {}
    
    if 'joined_groups' not in session:
        session['joined_groups'] = []
    
    # Get all forum groups
    forum_groups = get_forum_groups()
    
    for group_id, group in forum_groups.items():
        if group_id not in session['forum_data']:
            session['forum_data'][group_id] = {'topics': {}}
            
            # Initialize topics with their messages
            for topic_id, topic in group['topics'].items():
                if topic_id not in session['forum_data'][group_id]['topics']:
                    messages = []
                    # Add pre-defined messages if available
                    if 'messages' in topic:
                        messages.extend(topic['messages'])
                    # Add sample messages if available
                    if topic_id in SAMPLE_MESSAGES:
                        messages.extend(SAMPLE_MESSAGES[topic_id])
                    
                    session['forum_data'][group_id]['topics'][topic_id] = {
                        'posts': messages
                    }
    
    session.modified = True

# Educational Resources Content
EDUCATIONAL_RESOURCES = {
    'what-is-menopause': {
        'title': 'What is Menopause?',
        'content': '''
            <div class="space-y-4">
                <p>Menopause is a natural biological process marking the end of menstrual cycles. It typically occurs in your 40s or 50s.</p>
                <div class="bg-pink-50 p-4 rounded-lg">
                    <h3 class="font-semibold mb-2">Key Points:</h3>
                    <ul class="list-disc pl-6">
                        <li>Natural part of aging</li>
                        <li>Average age is 51 years</li>
                        <li>Diagnosed after 12 months without periods</li>
                        <li>Caused by hormonal changes</li>
                    </ul>
                </div>
            </div>
        '''
    },
    'stages-of-menopause': {
        'title': 'Stages of Menopause',
        'content': '''
            <div class="space-y-4">
                <div class="bg-pink-50 p-4 rounded-lg mb-4">
                    <h3 class="font-semibold mb-2">1. Perimenopause</h3>
                    <ul class="list-disc pl-6">
                        <li>Begins several years before menopause</li>
                        <li>Irregular periods</li>
                        <li>First signs of hormonal changes</li>
                    </ul>
                </div>
                <div class="bg-pink-50 p-4 rounded-lg mb-4">
                    <h3 class="font-semibold mb-2">2. Menopause</h3>
                    <ul class="list-disc pl-6">
                        <li>12 consecutive months without a period</li>
                        <li>End of fertility</li>
                        <li>Significant hormonal changes</li>
                    </ul>
                </div>
                <div class="bg-pink-50 p-4 rounded-lg">
                    <h3 class="font-semibold mb-2">3. Postmenopause</h3>
                    <ul class="list-disc pl-6">
                        <li>Years following menopause</li>
                        <li>Symptoms may continue</li>
                        <li>Focus on health maintenance</li>
                    </ul>
                </div>
            </div>
        '''
    },
    'common-symptoms': {
        'title': 'Common Symptoms',
        'content': '''
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="bg-pink-50 p-4 rounded-lg">
                    <h3 class="font-semibold mb-2">Physical Symptoms</h3>
                    <ul class="list-disc pl-6">
                        <li>Hot flashes</li>
                        <li>Night sweats</li>
                        <li>Sleep problems</li>
                        <li>Weight gain</li>
                        <li>Vaginal dryness</li>
                    </ul>
                </div>
                <div class="bg-pink-50 p-4 rounded-lg">
                    <h3 class="font-semibold mb-2">Emotional Changes</h3>
                    <ul class="list-disc pl-6">
                        <li>Mood swings</li>
                        <li>Anxiety</li>
                        <li>Depression</li>
                        <li>Irritability</li>
                    </ul>
                </div>
            </div>
        '''
    },
    'hormone-therapy': {
        'title': 'Hormone Therapy',
        'content': '''
            <div class="space-y-4">
                <p>Hormone therapy (HT) helps manage menopausal symptoms by replacing declining hormones.</p>
                <div class="bg-blue-50 p-4 rounded-lg">
                    <h3 class="font-semibold mb-2">Types of Hormone Therapy:</h3>
                    <ul class="list-disc pl-6">
                        <li>Estrogen therapy</li>
                        <li>Combined hormone therapy</li>
                        <li>Low-dose vaginal products</li>
                    </ul>
                </div>
            </div>
        '''
    },
    'natural-remedies': {
        'title': 'Natural Remedies',
        'content': '''
            <div class="bg-green-50 p-4 rounded-lg">
                <h3 class="font-semibold mb-2">Natural Solutions:</h3>
                <ul class="list-disc pl-6">
                    <li>Black cohosh</li>
                    <li>Evening primrose oil</li>
                    <li>Flaxseed</li>
                    <li>Soy products</li>
                    <li>Herbal supplements</li>
                </ul>
            </div>
        '''
    },
    'lifestyle-changes': {
        'title': 'Lifestyle Changes',
        'content': '''
            <div class="bg-green-50 p-4 rounded-lg">
                <h3 class="font-semibold mb-2">Recommended Changes:</h3>
                <ul class="list-disc pl-6">
                    <li>Regular exercise</li>
                    <li>Healthy diet</li>
                    <li>Stress management</li>
                    <li>Good sleep habits</li>
                    <li>Avoiding triggers</li>
                </ul>
            </div>
        '''
    },
    'exercise-tips': {
        'title': 'Exercise Tips',
        'content': '''
            <div class="bg-blue-50 p-4 rounded-lg">
                <h3 class="font-semibold mb-2">Recommended Exercises:</h3>
                <ul class="list-disc pl-6">
                    <li>Walking (30 minutes daily)</li>
                    <li>Swimming</li>
                    <li>Yoga</li>
                    <li>Strength training</li>
                    <li>Stretching exercises</li>
                </ul>
            </div>
        '''
    },
    'nutrition-guide': {
        'title': 'Nutrition Guide',
        'content': '''
            <div class="bg-green-50 p-4 rounded-lg">
                <h3 class="font-semibold mb-2">Dietary Recommendations:</h3>
                <ul class="list-disc pl-6">
                    <li>Calcium-rich foods</li>
                    <li>Vitamin D sources</li>
                    <li>Whole grains</li>
                    <li>Lean proteins</li>
                    <li>Fruits and vegetables</li>
                </ul>
            </div>
        '''
    },
    'stress-management': {
        'title': 'Stress Management',
        'content': '''
            <div class="bg-purple-50 p-4 rounded-lg">
                <h3 class="font-semibold mb-2">Stress Relief Techniques:</h3>
                <ul class="list-disc pl-6">
                    <li>Meditation</li>
                    <li>Deep breathing exercises</li>
                    <li>Yoga</li>
                    <li>Regular exercise</li>
                    <li>Adequate sleep</li>
                </ul>
            </div>
        '''
    }
}

@app.route('/api/resource-content/<topic>')
def get_resource_content(topic):
    """Get educational resource content for a specific topic"""
    content = EDUCATIONAL_RESOURCES.get(topic)
    if content:
        return jsonify({
            'status': 'success',
            'data': content
        })
    return jsonify({
        'status': 'error',
        'message': 'Topic not found'
    }), 404

@app.route('/resources/what-is-menopause')
def what_is_menopause():
    return render_template('what_is_menopause.html')

@app.route('/resources/stages-of-menopause')
def stages_of_menopause():
    return render_template('stages_of_menopause.html')

@app.route('/resources/common-symptoms')
def common_symptoms():
    return render_template('common_symptoms.html')

@app.route('/resources/treatment-options')
def treatment_options():
    return render_template('treatment_options.html')

@app.route('/resources/hormone-therapy')
def hormone_therapy():
    return render_template('hormone_therapy.html')

@app.route('/resources/natural-remedies')
def natural_remedies():
    return render_template('natural_remedies.html')

@app.route('/resources/lifestyle-changes')
def lifestyle_changes():
    return render_template('lifestyle_changes.html')

# Supported languages
SUPPORTED_LANGUAGES = {
    'en': 'English'
}

@app.route('/set-language/<language>')
def set_language(language):
    if language in SUPPORTED_LANGUAGES:
        session['language'] = language
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Language not supported'})

@app.route('/community')
@login_required
def community():
    """Display community page with all groups"""
    # Initialize session data if not present
    if 'forum_data' not in session:
        session['forum_data'] = {}
    
    if 'joined_groups' not in session:
        session['joined_groups'] = []
    
    # Get all forum groups
    forum_groups = {**FORUM_GROUPS, **USER_CREATED_GROUPS}
    
    return render_template('community.html', 
                         forum_groups=forum_groups,
                         joined_groups=session.get('joined_groups', []))

@app.route('/community/join/<group_id>', methods=['POST'])
@login_required
def join_group(group_id):
    forum_groups = get_forum_groups()
    if group_id not in forum_groups:
        return jsonify({'error': 'Group not found'}), 404
    
    init_session_data()  # Ensure forum data is initialized
    
    joined_groups = session.get('joined_groups', [])
    if group_id not in joined_groups:
        joined_groups.append(group_id)
        session['joined_groups'] = joined_groups
        session.modified = True
    
    return jsonify({
        'success': True,
        'message': f'Successfully joined {forum_groups[group_id]["name"]}!'
    })

@app.route('/community/group/<group_id>')
@login_required
def view_group(group_id):
    """View a specific group"""
    try:
        # First check user-created groups
        if group_id in USER_CREATED_GROUPS:
            group = USER_CREATED_GROUPS[group_id]
        else:
            # Then check pre-defined groups from session or default
            forum_groups = session.get('forum_groups', FORUM_GROUPS.copy())
            if group_id not in forum_groups:
                flash('Group not found', 'error')
                return redirect(url_for('community'))
            group = forum_groups[group_id]
        
        # Initialize topics if not present
        if 'topics' not in group:
            group['topics'] = {}
        
        # Check if user is a member
        is_member = group_id in session.get('joined_groups', [])
        
        # Ensure forum data is initialized for this group
        if 'forum_data' not in session:
            session['forum_data'] = {}
        if group_id not in session['forum_data']:
            session['forum_data'][group_id] = {'topics': {}}
            session.modified = True
        
        return render_template('group.html',
                             group_id=group_id,
                             group=group,
                             is_member=is_member,
                             session=session)
                             
    except Exception as e:
        print(f"Error viewing group: {str(e)}")
        flash('Error loading group', 'error')
        return redirect(url_for('community'))

@app.route('/community/group/<group_id>/topic/<topic_id>')
@login_required
def view_topic(group_id, topic_id):
    """View a topic and its messages"""
    forum_groups = get_forum_groups()
    if group_id not in forum_groups or topic_id not in forum_groups[group_id]['topics']:
        flash('Topic not found')
        return redirect(url_for('view_group', group_id=group_id))
    
    # Initialize session data
    init_session_data()
    
    # Ensure the forum data structure exists
    if group_id not in session['forum_data']:
        session['forum_data'][group_id] = {'topics': {}}
    
    if 'topics' not in session['forum_data'][group_id]:
        session['forum_data'][group_id]['topics'] = {}
    
    # Initialize topic if it doesn't exist
    if topic_id not in session['forum_data'][group_id]['topics']:
        messages = []
        topic = forum_groups[group_id]['topics'][topic_id]
        
        # Add pre-defined messages if available
        if 'messages' in topic:
            messages.extend(topic['messages'])
        
        # Add sample messages if available
        if topic_id in SAMPLE_MESSAGES:
            messages.extend(SAMPLE_MESSAGES[topic_id])
        
        session['forum_data'][group_id]['topics'][topic_id] = {
            'posts': messages
        }
        session.modified = True
    
    topic_data = session['forum_data'][group_id]['topics'][topic_id]
    topic = forum_groups[group_id]['topics'][topic_id]
    
    return render_template('topic.html',
                         group=forum_groups[group_id],
                         group_id=group_id,
                         topic=topic,
                         topic_id=topic_id,
                         posts=topic_data['posts'],
                         is_member=group_id in session.get('joined_groups', []))

@app.route('/community/group/<group_id>/topic/<topic_id>/post', methods=['POST'])
@login_required
def add_post(group_id, topic_id):
    """Add a new post to a topic"""
    forum_groups = get_forum_groups()
    if group_id not in forum_groups or topic_id not in forum_groups[group_id]['topics']:
        return jsonify({'error': 'Topic not found'}), 404
    
    if group_id not in session.get('joined_groups', []):
        return jsonify({'error': 'Must be a group member to post'}), 403
    
    message = request.form.get('message')
    if not message:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    # Initialize session data
    init_session_data()
    
    # Create new post
    new_post = {
        'username': session['username'],
        'message': message,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Ensure the forum data structure exists
    if group_id not in session['forum_data']:
        session['forum_data'][group_id] = {'topics': {}}
    
    if 'topics' not in session['forum_data'][group_id]:
        session['forum_data'][group_id]['topics'] = {}
    
    # Initialize topic if it doesn't exist
    if topic_id not in session['forum_data'][group_id]['topics']:
        messages = []
        topic = forum_groups[group_id]['topics'][topic_id]
        
        # Add pre-defined messages if available
        if 'messages' in topic:
            messages.extend(topic['messages'])
        
        # Add sample messages if available
        if topic_id in SAMPLE_MESSAGES:
            messages.extend(SAMPLE_MESSAGES[topic_id])
        
        session['forum_data'][group_id]['topics'][topic_id] = {
            'posts': messages
        }
    
    # Add the new post
    session['forum_data'][group_id]['topics'][topic_id]['posts'].append(new_post)
    session.modified = True
    
    return jsonify({
        'success': True,
        'post': new_post,
        'message': 'Post added successfully'
    })

@app.route('/community/create_group', methods=['POST'])
@login_required
def create_group():
    """Create a new group"""
    try:
        data = request.get_json()
        if not data:
            data = request.form.to_dict()
            
        name = data.get('name')
        description = data.get('description', '')
        
        if not name:
            return jsonify({'error': 'Group name is required'}), 400
            
        # Create a URL-safe group ID
        group_id = re.sub(r'[^a-z0-9_]', '_', name.lower())
        
        # Check if group ID already exists
        if group_id in USER_CREATED_GROUPS or group_id in FORUM_GROUPS:
            return jsonify({'error': 'A group with this name already exists'}), 400
            
        # Create new group with proper initialization
        new_group = {
            'id': group_id,
            'name': name,
            'description': description,
            'created_by': session.get('user_id'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'topics': {},  # Initialize empty topics dict
            'members': [session.get('user_id')]  # Add creator as first member
        }
        
        # Add to user created groups
        USER_CREATED_GROUPS[group_id] = new_group
        
        # Add creator to joined groups
        if 'joined_groups' not in session:
            session['joined_groups'] = []
        if group_id not in session['joined_groups']:
            session['joined_groups'].append(group_id)
        
        # Initialize forum data for the new group
        if 'forum_data' not in session:
            session['forum_data'] = {}
        session['forum_data'][group_id] = {
            'topics': {}
        }
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': f'Group "{name}" created successfully!',
            'group_id': group_id,
            'group': new_group
        })
        
    except Exception as e:
        print(f"Error creating group: {str(e)}")
        return jsonify({'error': 'Failed to create group'}), 500

@app.route('/community/group/<group_id>/create_topic', methods=['POST'])
@login_required
def create_topic(group_id):
    """Create a new topic in a group"""
    try:
        data = request.get_json()
        if not data:
            data = request.form.to_dict()
        
        if 'forum_groups' not in session:
            session['forum_groups'] = FORUM_GROUPS.copy()
        
        forum_groups = get_forum_groups()
        
        if group_id not in forum_groups:
            return jsonify({'error': 'Group not found'}), 404
        
        # Check if user is a member
        if group_id not in session.get('joined_groups', []):
            return jsonify({'error': 'Must be a member to create topics'}), 403
        
        title = data.get('title')
        description = data.get('description')
        
        if not title or not description:
            return jsonify({'error': 'Title and description are required'}), 400
        
        # Create a URL-safe topic ID from the title
        topic_id = re.sub(r'[^a-z0-9_]', '_', title.lower())
        
        # Initialize topics if not present
        if 'topics' not in forum_groups[group_id]:
            forum_groups[group_id]['topics'] = {}
            
        if topic_id in forum_groups[group_id]['topics']:
            return jsonify({'error': 'A topic with this title already exists'}), 400
        
        # Create new topic
        new_topic = {
            'title': title,
            'description': description,
            'created_by': session.get('user_id'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'messages': [{
                'username': 'MenoCare_Admin',
                'message': f'Welcome to {title}! Start the discussion by sharing your thoughts.',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }]
        }
        
        # Add topic to the appropriate storage
        if group_id in USER_CREATED_GROUPS:
            # For user-created groups
            USER_CREATED_GROUPS[group_id]['topics'][topic_id] = new_topic
        else:
            # For pre-defined groups
            if 'forum_groups' not in session:
                session['forum_groups'] = {}
            if group_id not in session['forum_groups']:
                session['forum_groups'][group_id] = forum_groups[group_id].copy()
            
            session['forum_groups'][group_id]['topics'][topic_id] = new_topic
            session.modified = True
        
        # Initialize forum data for the new topic
        if 'forum_data' not in session:
            session['forum_data'] = {}
        if group_id not in session['forum_data']:
            session['forum_data'][group_id] = {
                'topics': {}
            }
        
        session['forum_data'][group_id]['topics'][topic_id] = {
            'posts': new_topic['messages']
        }
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': 'Topic created successfully',
            'topic_id': topic_id,
            'topic': new_topic
        })
        
    except Exception as e:
        print(f"Error creating topic: {str(e)}")
        return jsonify({'error': 'Failed to create topic'}), 500

@app.route('/community/group/<group_id>/leave', methods=['POST'])
@login_required
def leave_group(group_id):
    """Leave a joined group"""
    if group_id not in session.get('joined_groups', []):
        return jsonify({'error': 'Not a member of this group'}), 400
    
    session['joined_groups'].remove(group_id)
    return jsonify({'success': True, 'message': 'Successfully left the group'})

@app.route('/community/group/<group_id>/delete', methods=['POST'])
@login_required
def delete_group(group_id):
    """Delete a user-created group"""
    try:
        # Only allow deletion of user-created groups
        if group_id not in USER_CREATED_GROUPS:
            return jsonify({'error': 'Cannot delete pre-defined groups'}), 403
            
        # Check if user is the creator of the group
        group = USER_CREATED_GROUPS[group_id]
        if group['created_by'] != session.get('user_id'):
            return jsonify({'error': 'Only the group creator can delete the group'}), 403
            
        # Remove group from USER_CREATED_GROUPS
        del USER_CREATED_GROUPS[group_id]
        
        # Remove from joined_groups if present
        if 'joined_groups' in session and group_id in session['joined_groups']:
            session['joined_groups'].remove(group_id)
            
        # Remove group data from forum_data
        if 'forum_data' in session and group_id in session['forum_data']:
            del session['forum_data'][group_id]
            
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': 'Group deleted successfully'
        })
        
    except Exception as e:
        print(f"Error deleting group: {str(e)}")
        return jsonify({'error': 'Failed to delete group'}), 500

@app.route('/community/group/<group_id>/topic/<topic_id>/delete', methods=['POST'])
@login_required
def delete_topic(group_id, topic_id):
    """Delete a topic from a group"""
    try:
        # Check if group exists
        if group_id in USER_CREATED_GROUPS:
            group = USER_CREATED_GROUPS[group_id]
        elif group_id in session.get('forum_groups', FORUM_GROUPS):
            group = session['forum_groups'][group_id]
        else:
            return jsonify({'error': 'Group not found'}), 404
            
        # Check if topic exists
        if 'topics' not in group or topic_id not in group['topics']:
            return jsonify({'error': 'Topic not found'}), 404
            
        # Check if user is the creator of the topic or group admin
        topic = group['topics'][topic_id]
        if topic.get('created_by') != session.get('user_id') and group.get('created_by') != session.get('user_id'):
            return jsonify({'error': 'Permission denied'}), 403
            
        # Remove topic
        del group['topics'][topic_id]
        
        # Remove topic from forum_data if present
        if 'forum_data' in session and group_id in session['forum_data']:
            if 'topics' in session['forum_data'][group_id] and topic_id in session['forum_data'][group_id]['topics']:
                del session['forum_data'][group_id]['topics'][topic_id]
        
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': 'Topic deleted successfully'
        })
        
    except Exception as e:
        print(f"Error deleting topic: {str(e)}")
        return jsonify({'error': 'Failed to delete topic'}), 500

@app.route('/community/group/<group_id>/edit', methods=['POST'])
@login_required
def edit_group(group_id):
    """Edit a user-created group"""
    # Only allow editing of user-created groups
    if group_id in FORUM_GROUPS:
        return jsonify({'error': 'Cannot edit pre-defined groups'}), 403
    
    if group_id not in USER_CREATED_GROUPS:
        return jsonify({'error': 'Group not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    name = data.get('name')
    description = data.get('description')
    
    if not name or not description:
        return jsonify({'error': 'Name and description are required'}), 400
    
    # Update group
    USER_CREATED_GROUPS[group_id].update({
        'name': name,
        'description': description
    })
    
    return jsonify({
        'success': True,
        'message': 'Group updated successfully',
        'group': USER_CREATED_GROUPS[group_id]
    })

#AI Chat routes
@app.route('/ai-chat')
@login_required
def ai_chat():
    # Clear any existing language preference when loading the chat page
    language_data = get_language_data()  # This includes translations and language info
    return render_template('ai_chat.html', **language_data)

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    try:
        data = request.json
        if not data:
            data = request.form.to_dict()
            
        user_message = data.get('message', '').strip()

        '''# Available Indian languages with their native names
        indian_languages = {
            'en': {'name': 'English', 'english_name': 'English'},
            'hi': {'name': 'हिंदी', 'english_name': 'Hindi'},
            'te': {'name': 'తెలుగు', 'english_name': 'Telugu'},
            'ta': {'name': 'தமிழ்', 'english_name': 'Tamil'},
            'kn': {'name': 'ಕನ್ನಡ', 'english_name': 'Kannada'},
            'ml': {'name': 'മലയാളം', 'english_name': 'Malayalam'},
            'mr': {'name': 'मराठी', 'english_name': 'Marathi'},
            'bn': {'name': 'বাংলা', 'english_name': 'Bengali'},
            'gu': {'name': 'ગુજરાતી', 'english_name': 'Gujarati'}
        }'''

        # If no language is set or it's the first message
       

        # Regular chat message
        try:
            language = session['chat_language']
            lang_name = indian_languages[language]['name']
            
            chat_prompt = f"""
            The user's message is: {user_message}
            
            Respond ONLY in english language.
            Provide accurate, empathetic, and practical information about menopause care.
            Keep the response clear and focused on addressing the user's question.
            """
            
            completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful and empathetic AI assistant specializing in women's health."},
                    {"role": "user", "content": user_message}
                ],
                model="mixtral-8x7b-32768",  
                temperature=0.7,
                max_tokens=1000
            )
            
            return jsonify({
                'response': completion.choices[0].message.content,
                'awaiting_language': False
            })
            
        except Exception as e:
            print(f"Chat Error: {str(e)}")
            return jsonify({'error': 'Failed to generate response'}), 500
            
    except Exception as e:
        print(f"Server Error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/analyze-symptoms', methods=['POST'])
@login_required
def analyze_symptoms():
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Extract data from JSON
        symptoms = data.get('symptoms', [])
        severity = data.get('severity', [])
        frequency = data.get('frequency', [])
        duration = data.get('duration', [])
        age = data.get('age')
        gender = data.get('gender')
        medical_history = data.get('medical_history')
        current_medications = data.get('medications')
        lifestyle = data.get('lifestyle')
        sleep_quality = data.get('sleep_quality')
        stress_level = data.get('stress_level')
        exercise_frequency = data.get('exercise_frequency')

        # Prepare data for Groq analysis
        prompt = f"""
        Analyze the following hormonal health data and provide detailed insights:

        Personal Information:
        - Age: {age}
        - Gender: {gender}
        
        Symptoms and Severity:
        {', '.join(f'{s} (Severity: {sv}, Frequency: {f}, Duration: {d})' for s, sv, f, d in zip(symptoms, severity, frequency, duration))}
        
        Medical Context:
        - Medical History: {medical_history}
        - Current Medications: {current_medications}
        
        Lifestyle Factors:
        - Sleep Quality: {sleep_quality}
        - Stress Level: {stress_level}
        - Exercise Frequency: {exercise_frequency}
        - Lifestyle Details: {lifestyle}
        
        Please provide a comprehensive analysis including:
        1. Overall health score (0-100)
        2. Health status assessment
        3. Activity level evaluation
        4. Sleep quality analysis
        5. Detailed symptoms analysis with severity levels
        6. Key health metrics
        7. Personalized recommendations
        
        Format the response as a structured JSON object with these exact keys:
        {
            "overall_score": number,
            "health_status": string,
            "activity_level": string,
            "sleep_quality": string,
            "symptoms": [{"name": string, "severity": string, "percentage": number}],
            "metrics": [{"name": string, "value": string, "percentage": number}],
            "recommendations": [{"title": string, "description": string}]
        }
        """

        # Call Groq API
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful and empathetic AI assistant specializing in women's health."},
                {"role": "user", "content": prompt}
            ],
            model="mixtral-8x7b-32768",  
            temperature=0.7,
            max_tokens=1000
        )
        
        # Parse the response
        analysis = response.choices[0].message.content
        try:
            # Safely parse the JSON response
            import json
            analysis_dict = json.loads(analysis)
            return jsonify(analysis_dict)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse API response: {e}")
            raise ValueError("Invalid response format from analysis service")

    except Exception as e:
        logging.error(f"Error in analysis: {str(e)}")
        # Return default analysis in case of error
        return jsonify({
            'overall_score': 75,
            'health_status': 'Moderate',
            'activity_level': 'Average',
            'sleep_quality': 'Fair',
            'symptoms': [
                {'name': 'Fatigue', 'severity': 'Moderate', 'percentage': 60},
                {'name': 'Mood Swings', 'severity': 'Mild', 'percentage': 40},
                {'name': 'Sleep Issues', 'severity': 'Moderate', 'percentage': 65}
            ],
            'metrics': [
                {'name': 'Stress Level', 'value': 'Moderate', 'percentage': 60},
                {'name': 'Energy Level', 'value': 'Fair', 'percentage': 55},
                {'name': 'Emotional Balance', 'value': 'Good', 'percentage': 70},
                {'name': 'Physical Activity', 'value': 'Moderate', 'percentage': 65}
            ],
            'recommendations': [
                {
                    'title': 'Sleep Improvement',
                    'description': 'Establish a regular sleep schedule and create a relaxing bedtime routine.'
                },
                {
                    'title': 'Stress Management',
                    'description': 'Practice daily meditation or deep breathing exercises.'
                },
                {
                    'title': 'Physical Activity',
                    'description': 'Aim for 30 minutes of moderate exercise 3-4 times per week.'
                }
            ]
        })

@app.route('/get_cycle_data')
@login_required
def get_cycle_data():
    try:
        user_id = session['user_id']
        
        if user_id not in CYCLE_DATA_CACHE or not CYCLE_DATA_CACHE[user_id]:
            return jsonify({
                'success': True,
                'cycle_data': None
            })
        
        # Get the most recent cycle data
        latest_data = CYCLE_DATA_CACHE[user_id][-1]
        
        # Ensure predictions are up to date
        latest_data['predictions'] = predict_cycles(
            latest_data['last_period'],
            latest_data['cycle_length']
        )
        
        return jsonify({
            'success': True,
            'cycle_data': latest_data
        })

    except Exception as e:
        print(f"Error getting cycle data: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get cycle data'
        }), 500

def predict_cycles(last_period_date, cycle_length, num_predictions=12):
    """Predict future cycle dates based on last period and cycle length"""
    try:
        last_period = datetime.strptime(last_period_date, '%Y-%m-%d')
        predictions = []
        
        # Past cycles (6 months back)
        for i in range(-6, 0):
            cycle_date = last_period + timedelta(days=i * int(cycle_length))
            predictions.append(cycle_date.strftime('%Y-%m-%d'))
        
        # Future cycles (6 months ahead)
        for i in range(1, num_predictions - 5):  # -5 because we already have 6 past predictions
            cycle_date = last_period + timedelta(days=i * int(cycle_length))
            predictions.append(cycle_date.strftime('%Y-%m-%d'))
            last_cycle_date = cycle_date
        
        return sorted(predictions)  # Sort dates chronologically
    except Exception as e:
        print(f"Error in predict_cycles: {str(e)}")
        return []

@app.route('/log_cycle_data', methods=['POST'])
@login_required
def log_cycle_data():
    try:
        data = request.form
        dob = data.get('dob')
        last_period = data.get('last_period')
        try:
            cycle_length = int(data.get('cycle_length', 28))
        except ValueError:
            return jsonify({'error': 'Cycle length must be a valid number'}), 400
        health_issues = data.get('health_issues', '')

        # Validate required fields
        if not dob or not last_period:
            return jsonify({'error': 'Date of birth and last period date are required'}), 400

        # Validate date of birth
        try:
            dob_date = datetime.strptime(dob, '%Y-%m-%d')
            today = datetime.now()
            min_year = 1985
            
            if dob_date > today:
                return jsonify({'error': 'Date of birth cannot be in the future'}), 400
                
            if dob_date.year < min_year:
                return jsonify({'error': f'Date of birth must be from {min_year} onwards'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid date of birth format'}), 400

        # Validate last period date
        try:
            last_period_date = datetime.strptime(last_period, '%Y-%m-%d')
            today = datetime.now()
            six_months_ago = today - timedelta(days=180)  # Approximately 6 months
            
            if last_period_date > today:
                return jsonify({'error': 'Last period date cannot be in the future'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid last period date format'}), 400

        # Validate cycle length
        if cycle_length < 21 or cycle_length > 35:
            return jsonify({'error': 'Cycle length should be between 21 and 35 days'}), 400

        # Calculate predictions
        predictions = predict_cycles(last_period, cycle_length)

        # Store in cache
        user_id = session['user_id']
        if user_id not in CYCLE_DATA_CACHE:
            CYCLE_DATA_CACHE[user_id] = []
            
        cycle_data = {
            'dob': dob,
            'last_period': last_period,
            'cycle_length': cycle_length,
            'health_issues': health_issues,
            'predictions': predictions,
            'timestamp': datetime.now().isoformat()
        }
        
        CYCLE_DATA_CACHE[user_id].append(cycle_data)

        return jsonify({
            'success': True,
            'message': 'Cycle data logged successfully',
            'cycle_data': cycle_data
        })
    except Exception as e:
        print(f"Error in log_cycle_data: {str(e)}")
        return jsonify({'error': 'An error occurred while logging cycle data'}), 500

@app.route('/get_cycle_report', methods=['POST'])
def get_cycle_report():
    try:
        if not session.get('logged_in'):
            return jsonify({'error': 'Please log in first'}), 401

        # Get form data
        menstrual_health = request.form.get('menstrual_health')
        symptoms = request.form.getlist('symptoms[]')
        cycle_regularity = request.form.get('cycle_regularity')
        concerns = request.form.get('concerns', '')
        concerns_analysis = request.form.get('concerns_analysis', '')

        # Get cycle data from session
        cycle_data = session.get('cycle_data', {})
        if not cycle_data:
            return jsonify({'error': 'Please log your cycle data first'}), 400
        
        # Create the PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        # Add title
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30
        )
        story.append(Paragraph("Your Menstrual Health Report", title_style))

        # Add personal information
        story.append(Paragraph("Personal Information", styles['Heading2']))
        story.append(Paragraph(f"Date of Birth: {cycle_data.get('dob', 'Not provided')}", styles['Normal']))
        story.append(Paragraph(f"Last Period: {cycle_data.get('last_period', 'Not provided')}", styles['Normal']))
        story.append(Paragraph(f"Cycle Length: {cycle_data.get('cycle_length', 'Not provided')} days", styles['Normal']))
        story.append(Spacer(1, 12))

        # Add health assessment
        story.append(Paragraph("Health Assessment", styles['Heading2']))
        story.append(Paragraph(f"Overall Menstrual Health: {menstrual_health}", styles['Normal']))
        story.append(Paragraph(f"Cycle Regularity: {cycle_regularity}", styles['Normal']))
        if symptoms:
            story.append(Paragraph("Reported Symptoms:", styles['Normal']))
            for symptom in symptoms:
                story.append(Paragraph(f"• {symptom.replace('_', ' ').title()}", styles['Normal']))
        story.append(Spacer(1, 12))

        # Add concerns and analysis
        if concerns:
            story.append(Paragraph("Your Concerns", styles['Heading2']))
            story.append(Paragraph(concerns, styles['Normal']))
            if concerns_analysis:
                story.append(Paragraph("Analysis", styles['Heading2']))
                story.append(Paragraph(concerns_analysis, styles['Normal']))
            story.append(Spacer(1, 12))

        # Add predictions
        story.append(Paragraph("Upcoming Cycles", styles['Heading2']))
        predictions = cycle_data.get('predictions', [])[:6]  # Show next 6 predictions
        for date in predictions:
            story.append(Paragraph(f"• Expected period: {date}", styles['Normal']))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name='health_report.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"Error generating report: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/analyze_concerns', methods=['POST'])
@login_required
def analyze_concerns():
    try:
        data = request.json
        user_message = data.get('concerns')
        lang_code = data.get('language', 'en-US')
        
        # Map language codes to full names
        lang_map = {
            'en-US': 'English',
            'hi-IN': 'Hindi',
            'ta-IN': 'Tamil',
            'te-IN': 'Telugu',
            'kn-IN': 'Kannada',
            'ml-IN': 'Malayalam',
            'mr-IN': 'Marathi',
            'gu-IN': 'Gujarati',
            'bn-IN': 'Bengali'
        }
        
        lang_name = lang_map.get(lang_code, 'English')
        
        chat_prompt = f"""
        User Question: {user_message}
        
        Respond ONLY in {lang_name} language.
        Provide accurate, empathetic, and practical information about menopause care.
        Keep the response clear and focused on addressing the user's question.
        """
        
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful and empathetic AI assistant specializing in women's health."},
                {"role": "user", "content": user_message}
            ],
            model="mixtral-8x7b-32768",  
            temperature=0.7,
            max_tokens=1000
        )
        
        response_text = completion.choices[0].message.content
        
        # Generate follow-up questions based on context
        follow_up_questions = generate_follow_up_questions(user_message, lang_code)
        
        return jsonify({
            'success': True,
            'analysis': response_text,
            'follow_up_questions': follow_up_questions
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate response'
        }), 500

def generate_follow_up_questions(context, lang_code):
    # Add language-specific follow-up questions based on context
    questions = {
        'en-US': [
            "Would you like more specific advice about managing these symptoms?",
            "Have you tried any treatments for these symptoms?",
            "How long have you been experiencing these symptoms?"
        ],
        'hi-IN': [
            "क्या आप इन लक्षणों को प्रबंधित करने के बारे में अधिक विशिष्ट सलाह चाहेंगी?",
            "क्या आपने इन लक्षणों के लिए कोई उपचार आजमाया है?",
            "आप कब से इन लक्षणों का अनुभव कर रही हैं?"
        ],
        # Add other languages similarly
    }
    
    return questions.get(lang_code, questions['en-US'])

@app.route('/generate_cycle_report', methods=['POST'])
@login_required
def generate_cycle_report():
    try:
        user_id = str(session['user_id'])
        
        # Get questionnaire data from request
        questionnaire_data = request.get_json()
        if not questionnaire_data:
            return jsonify({"error": "No questionnaire data provided"}), 400
        
        # Convert all values to strings
        questionnaire_data = {
            'menstrual_health': str(questionnaire_data.get('menstrual_health', '')),
            'symptoms': [str(s) for s in questionnaire_data.get('symptoms', [])],
            'cycle_regularity': str(questionnaire_data.get('cycle_regularity', '')),
            'concerns': str(questionnaire_data.get('concerns', ''))
        }
        
        # Fetch user's cycle data
        cycles = db.fetch_all(
            "SELECT * FROM cycles WHERE user_id = %s ORDER BY date DESC LIMIT 12",
            (user_id,)
        )
        
        if not cycles:
            return jsonify({"error": "No cycle data found. Please log your cycle data first."}), 400
        
        # Prepare data for analysis
        cycle_data = [dict(c) for c in cycles]
        
        try:
            # Calculate cycle statistics
            cycle_lengths = []
            for i in range(len(cycle_data) - 1):
                current_date = datetime.strptime(str(cycle_data[i]['date']), '%Y-%m-%d')
                next_date = datetime.strptime(str(cycle_data[i + 1]['date']), '%Y-%m-%d')
                cycle_length = (current_date - next_date).days
                cycle_lengths.append(cycle_length)
            
            avg_cycle_length = sum(cycle_lengths) / len(cycle_lengths) if cycle_lengths else 28
            cycle_regularity = max(cycle_lengths) - min(cycle_lengths) if cycle_lengths else 0
            
            # Predict next cycles
            last_cycle_date = datetime.strptime(str(cycle_data[0]['date']), '%Y-%m-%d') if cycle_data else datetime.now()
            predicted_dates = []
            for i in range(3):
                next_date = last_cycle_date + timedelta(days=int(avg_cycle_length))
                predicted_dates.append(next_date.strftime('%Y-%m-%d'))
                last_cycle_date = next_date
            
            # Generate report using Groq API
            prompt = """ Analyze the following menstrual cycle data and questionnaire responses to generate a comprehensive health report:

Cycle Data Analysis:
- Average Cycle Length: {0:.1f} days
- Cycle Regularity: {1} days variation
- Predicted Next Cycles: {2}

Health Questionnaire Responses:

- Overall Menstrual Health: {3}
- Reported Symptoms: {4}
- Cycle Regularity Rating: {5}
- Specific Concerns: {6}

Patient Information:
- Patient ID: {7}
- Patient Name: {8}

Please provide a detailed analysis including:
1. Overall Cycle Health Assessment
2. Pattern Analysis and Predictions
3. Symptom Analysis and Management Recommendations
4. Potential Health Concerns
5. Lifestyle and Wellness Recommendations
6. When to Seek Medical Attention
""".format(
    float(avg_cycle_length),
    str(cycle_regularity),
    ', '.join(map(str, predicted_dates)),
    str(questionnaire_data['menstrual_health']),
    ', '.join(map(str, questionnaire_data['symptoms'])),
    str(questionnaire_data['cycle_regularity']),
    str(questionnaire_data['concerns']),
    str(session['user_id']),
    str(session['username'])
)
            
            try:
                completion = groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a helpful and empathetic AI assistant specializing in women's health."},
                        {"role": "user", "content": prompt}
                    ],
                    model="mixtral-8x7b-32768",  
                    temperature=0.3,
                    max_tokens=1000
                )
                
                report_content = completion.choices[0].message.content
            except Exception as api_error:
                print(f"API Error: {str(api_error)}")
                return jsonify({"error": "Failed to generate report content. Please try again."}), 500
            
            # Generate PDF report
            try:
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter)
                styles = getSampleStyleSheet()
                story = []

                # Add title
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Title'],
                    fontSize=24,
                    spaceAfter=30,
                    textColor=HexColor('#4A90E2')
                )
                story.append(Paragraph("Personalized Cycle Health Report", title_style))

                # Add date
                date_style = ParagraphStyle(
                    'DateStyle',
                    parent=styles['Normal'],
                    fontSize=12,
                    textColor=HexColor('#666666')
                )
                story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", date_style))
                story.append(Spacer(1, 20))

                # Add cycle statistics
                stats_text = """
                Cycle Statistics:
                • Average Cycle Length: {:.1f} days
                • Cycle Regularity: {} days variation
                • Next Predicted Cycles: {}
                """.format(
                    float(avg_cycle_length),
                    str(cycle_regularity),
                    ', '.join(str(d) for d in predicted_dates)
                )
                
                stats_style = ParagraphStyle(
                    'StatsStyle',
                    parent=styles['Normal'],
                    fontSize=12,
                    leading=14,
                    spaceAfter=12,
                    backColor=HexColor('#F3F4F6')
                )
                
                story.append(Paragraph(stats_text, stats_style))
                
                # Add patient information
                patient_info_text = """
                Patient Information:
                • Patient ID: {}
                • Patient Name: {}
                """.format(
                    str(session['user_id']),
                    str(session['username'])
                )
                
                patient_info_style = ParagraphStyle(
                    'PatientInfoStyle',
                    parent=styles['Normal'],
                    fontSize=12,
                    leading=14,
                    spaceAfter=12,
                    backColor=HexColor('#F3F4F6')
                )
                
                story.append(Paragraph(patient_info_text, patient_info_style))
                story.append(Spacer(1, 12))
                
                # Add main report content
                content_style = ParagraphStyle(
                    'CustomBody',
                    parent=styles['Normal'],
                    fontSize=12,
                    leading=14,
                    spaceAfter=12
                )
                
                for line in report_content.split('\n'):
                    if line.strip():
                        story.append(Paragraph(str(line), content_style))
                        story.append(Spacer(1, 6))
                
                doc.build(story)
                buffer.seek(0)
                
                return send_file(
                    buffer,
                    as_attachment=True,
                    download_name='cycle_report.pdf',
                    mimetype='application/pdf'
                )
            except Exception as pdf_error:
                print(f"PDF Generation Error: {str(pdf_error)}")
                return jsonify({"error": "Failed to generate PDF report. Please try again."}), 500
                
        except Exception as analysis_error:
            print(f"Analysis Error: {str(analysis_error)}")
            return jsonify({"error": "Failed to analyze cycle data. Please try again."}), 500
            
    except Exception as e:
        print(f"General Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Doctor chat and video call routes
@app.route('/doctor-chat')
@login_required
def doctor_chat():
    """Render the doctor chat interface"""
    return render_template('doctor_chat.html', now=datetime.now())

@app.route('/api/doctor-chat', methods=['POST'])
@login_required
def doctor_chat_message():
    """Handle doctor chat messages and file analysis"""
    message = request.form.get('message')
    files = request.files.getlist('files[]')
    # Initialize chat context if not exists
    # Initialize chat context if not exists
    if 'doctor_chat_context' not in session:
        session['doctor_chat_context'] = {
            'symptoms_discussed': [],
            'recommendations_given': [],
            'follow_up_needed': False
        }
    
    context = session['doctor_chat_context']
    # Limit context size by keeping only last 3 items
    if message:
        context['symptoms_discussed'] = context['symptoms_discussed'][-2:] + [message]
    session['doctor_chat_context'] = context
    
    file_analysis = []

    # Process uploaded files
    if files:
        for file in files:
            if file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                try:
                    # Extract text from images using OCR
                    if file.content_type.startswith('image/'):
                        image = Image.open(file_path)
                        extracted_text = pytesseract.image_to_string(image)
                        file_analysis.append(f"Analysis of image {filename}:\n{extracted_text}")
                    
                    # Extract text from PDFs
                    elif file.filename.lower().endswith('.pdf'):
                        pdf_text = []
                        pdf_document = fitz.open(file_path)
                        for page_num in range(pdf_document.page_count):
                            page = pdf_document[page_num]
                            pdf_text.append(page.get_text())
                        pdf_document.close()
                        extracted_text = "\n".join(pdf_text)
                        file_analysis.append(f"Analysis of PDF {filename}:\n{extracted_text}")
                    
                    # Clean up
                    os.remove(file_path)
                    
                except Exception as e:
                    print(f"Error processing file {filename}: {e}")
                    file_analysis.append(f"Error analyzing {filename}")
    
    # Combine message and file analysis for AI processing
    full_context = message
    if file_analysis:
        full_context += "\n\nFile Analysis:\n" + "\n\n".join(file_analysis)
    
    # Process the message using GPT for doctor-like responses
    system_prompt = """You are Dr. Sarah Johnson, a highly experienced gynecologist specializing in menopause and women's health who is gonna have a 1:1 chat with patient.when you are replying make it as simple chat as it is and the response for normal chat should be in one line and dont mention your name everytime it should only relate to the topic. 
    You are analyzing both the patient's message and any medical reports or images they have shared.
    Respond in a professional, empathetic manner while maintaining medical accuracy. if file been share thenFocus on:
    1. Analyzing any test results or medical reports shared
    2. Identifying key health indicators and symptoms
    3. Providing evidence-based information and recommendations
    4. Encouraging healthy lifestyle choices
    5. Knowing when to recommend in-person consultation
    Remember to:
    - Stay within your medical expertise
    - Be warm and supportive
    - Use clear, patient-friendly language
    - Emphasize the importance of regular check-ups
    - Maintain patient privacy and confidentiality"""
    
    conversation = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": full_context}
    ]
    
    try:
        response = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=conversation,
            temperature=0.7,
            max_tokens=800
        )
        
        doctor_response = response.choices[0].message.content
        
        # Update chat context based on the conversation
        context = session['doctor_chat_context']
        if any(keyword in full_context.lower() for keyword in ['pain', 'discomfort', 'symptom']):
            context['symptoms_discussed'].append(message)
        if 'recommend' in doctor_response.lower():
            context['recommendations_given'].append(doctor_response)
        if any(keyword in doctor_response.lower() for keyword in ['visit', 'consult', 'appointment']):
            context['follow_up_needed'] = True
        session['doctor_chat_context'] = context
        
        return jsonify({
            'response': doctor_response,
            'fileAnalysis': "\n".join(file_analysis) if file_analysis else None,
            'context': context
        })
        
    except Exception as e:
        print(f"Error in doctor chat: {e}")
        return jsonify({
            'error': 'I apologize, but I am currently experiencing some technical difficulties. Please try again in a moment.'
        }), 500

@app.route('/doctor-video-call')
@login_required
def doctor_video_call():
    # Redirect to Logstrike Meet
    return redirect('https://logstrike-meet.web.app/')

# Global variable to store articles
ARTICLES = []

def get_db():
    conn = sqlite3.connect('menocare.db')
    return conn

@app.route('/resources/create_article', methods=['POST'])
@login_required
def create_article():
    """Create a new article"""
    try:
        data = request.get_json()
        if not data:
            data = request.form.to_dict()
            
        title = data.get('title')
        content = data.get('content')
        category = data.get('category')
        
        if not all([title, content, category]):
            return jsonify({'error': 'Title, content and category are required'}), 400
            
        # Create article ID from title
        article_id = re.sub(r'[^a-z0-9_]', '_', title.lower()) + '_' + str(int(time.time()))
        
        # Create new article
        new_article = {
            'id': article_id,
            'title': title,
            'content': content,
            'category': category,
            'created_by': session.get('user_id'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Store in database
        db = get_db()
        db.execute(
            'INSERT INTO articles (id, title, content, category, created_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (article_id, title, content, category, session.get('user_id'), new_article['created_at'], new_article['updated_at'])
        )
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Article created successfully',
            'article': new_article
        })
        
    except Exception as e:
        print(f"Error creating article: {str(e)}")
        return jsonify({'error': 'Failed to create article'}), 500

@app.route('/resources/article/<article_id>/edit', methods=['POST'])
@login_required
def edit_article(article_id):
    """Edit an article"""
    try:
        data = request.get_json()
        if not data:
            data = request.form.to_dict()
        
        title = data.get('title')
        content = data.get('content')
        category = data.get('category')
        
        if not all([title, content, category]):
            return jsonify({'error': 'Title, content and category are required'}), 400
            
        # Get article from database
        db = get_db()
        article = db.execute(
            'SELECT * FROM articles WHERE id = ?',
            (article_id,)
        ).fetchone()
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
            
        # Check if user is the creator
        if article['created_by'] != session.get('user_id'):
            return jsonify({'error': 'Only the creator can edit this article'}), 403
            
        # Update article
        updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.execute(
            'UPDATE articles SET title = ?, content = ?, category = ?, updated_at = ? WHERE id = ?',
            (title, content, category, updated_at, article_id)
        )
        db.commit()
        
        updated_article = {
            'id': article_id,
            'title': title,
            'content': content,
            'category': category,
            'created_by': article['created_by'],
            'created_at': article['created_at'],
            'updated_at': updated_at
        }
        
        return jsonify({
            'success': True,
            'message': 'Article updated successfully',
            'article': updated_article
        })
        
    except Exception as e:
        print(f"Error editing article: {str(e)}")
        return jsonify({'error': 'Failed to edit article'}), 500

@app.route('/resources/article/<article_id>/delete', methods=['POST'])
@login_required
def delete_article(article_id):
    """Delete an article"""
    try:
        # Get article from database
        db = get_db()
        article = db.execute(
            'SELECT * FROM articles WHERE id = ?',
            (article_id,)
        ).fetchone()
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
            
        # Check if user is the creator
        if article['created_by'] != session.get('user_id'):
            return jsonify({'error': 'Only the creator can delete this article'}), 403
            
        # Delete article
        db.execute('DELETE FROM articles WHERE id = ?', (article_id,))
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Article deleted successfully'
        })
        
    except Exception as e:
        print(f"Error deleting article: {str(e)}")
        return jsonify({'error': 'Failed to delete article'}), 500

@app.route('/resources')
def resources():
    """Display resources page"""
    db = get_db()
    articles = db.execute(
        'SELECT * FROM articles ORDER BY created_at DESC'
    ).fetchall()
    return render_template('resources.html', articles=articles)

# Create articles table if it doesn't exist
def init_articles_table():
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    db.commit()

# Initialize articles table when app starts
with app.app_context():
    init_articles_table()
    
# Create pregnancy tracking table
def init_pregnancy_table():
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS pregnancy_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            due_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    db.commit()

# Initialize pregnancy table when app starts
with app.app_context():
    init_pregnancy_table()

# Cycle tracking routes
@app.route('/cycle_tracker')
@login_required
def cycle_tracker():
    try:
        current_local_time = datetime.now()
        return render_template('cycle_tracker.html', current_local_time=current_local_time, timedelta=timedelta)
    except Exception as e:
        print(f"Error in cycle_tracker: {str(e)}")
        return "An error occurred", 500

@app.route('/pregnancy')
def pregnancy():
    return render_template('pregnancy/index.html')

@app.route('/pregnancy/results')
def pregnancy_results():
    return render_template('pregnancy/results.html')

@app.route('/pregnancy/track', methods=['POST'])
@login_required
def pregnancy_track():
    due_date = request.form.get('due_date')
    if not due_date:
        flash('Please enter your due date', 'error')
        return redirect(url_for('pregnancy'))
    
    try:
        # Parse the due date
        due_date_obj = datetime.strptime(due_date, '%Y-%m-%d')
        today = datetime.now()
        
        # Save pregnancy tracking data
        db = get_db()
        db.execute(
            "INSERT INTO pregnancy_tracking (user_id, due_date) VALUES (?, ?)",
            (session['user_id'], due_date)
        )
        db.commit()
        
        # Calculate days until due date
        days_until_due = (due_date_obj - today).days
        countdown = max(0, days_until_due)
        
        # Calculate weeks pregnant
        total_pregnancy_days = 280  # 40 weeks * 7 days
        days_pregnant = total_pregnancy_days - days_until_due
        weeks_pregnant = max(0, min(40, days_pregnant // 7))
        
        # Store pregnancy details in session for report generation
        session['pregnancy_details'] = {
            'due_date': due_date,
            'weeks_pregnant': weeks_pregnant,
            'countdown': countdown
        }
        
        # Get next checkup information
        next_checkup = get_next_checkup_info(weeks_pregnant)
        
        # Calculate next checkup date
        if next_checkup:
            weeks_until_checkup = next_checkup["week"] - weeks_pregnant
            next_checkup_date = today + timedelta(weeks=weeks_until_checkup)
            next_checkup["date"] = next_checkup_date.strftime("%B %d, %Y")
        
        # Determine fetal development information based on weeks
        fetal_development = get_fetal_development_info(weeks_pregnant)
        
        # Get prenatal reminders based on current stage
        reminders = get_prenatal_reminders(weeks_pregnant)
        
        # Get periods information
        periods_info = {
            'effects': 'Your menstrual cycle will be paused during pregnancy',
            'restart_date': (due_date_obj + timedelta(weeks=6)).strftime('%B %d, %Y'),
            'symptoms': {
                'stopping': 'Morning sickness may occur in the first trimester',
                'restarting': 'Postpartum bleeding (lochia) is normal after delivery'
            },
            'health_conditions': {
                'stopping': 'Regular monitoring of blood pressure and glucose levels is important',
                'restarting': 'Gradual return to normal hormone levels postpartum'
            },
            'physical_energy': {
                'stopping': 'Fatigue is common, especially in first and third trimesters',
                'restarting': 'Energy levels will gradually improve postpartum'
            },
            'mental_health': {
                'stopping': 'Mood changes are normal due to hormonal changes',
                'restarting': 'Monitor for postpartum depression symptoms'
            }
        }
        
        # Get nutrition plan with week-specific recommendations
        nutrition_plan = get_nutrition_recommendations(weeks_pregnant)
        
        return render_template('pregnancy/results.html',
                             countdown=countdown,
                             weeks_pregnant=weeks_pregnant,
                             next_checkup=next_checkup,
                             fetal_development=fetal_development,
                             reminders=reminders,
                             periods_info=periods_info,
                             nutrition_plan=nutrition_plan,
                             show_reports=True)
                             
    except ValueError:
        flash('Please enter a valid date', 'error')
        return redirect(url_for('pregnancy'))
    except Exception as e:
        flash('Error calculating pregnancy details', 'error')
        return redirect(url_for('pregnancy'))

def get_next_checkup_info(weeks):
    checkup_schedule = {
        0: {"week": 8, "description": "First prenatal visit - Complete physical exam and medical history"},
        8: {"week": 12, "description": "NT scan and blood tests"},
        12: {"week": 16, "description": "Monthly checkup and possible genetic testing"},
        16: {"week": 20, "description": "Anatomy scan ultrasound"},
        20: {"week": 24, "description": "Glucose screening test"},
        24: {"week": 28, "description": "Rhogam shot (if needed) and diabetes test"},
        28: {"week": 30, "description": "Biweekly checkup starts"},
        30: {"week": 32, "description": "Growth scan and position check"},
        32: {"week": 34, "description": "Group B strep test"},
        34: {"week": 36, "description": "Weekly checkup starts"},
        36: {"week": 37, "description": "Weekly cervical checks"},
        37: {"week": 38, "description": "Weekly monitoring"},
        38: {"week": 39, "description": "Discuss delivery plans"},
        39: {"week": 40, "description": "Final preparations for delivery"}
    }
    
    current_week = int(weeks)
    next_checkup = None
    
    for start_week, checkup in checkup_schedule.items():
        if current_week <= start_week:
            next_checkup = checkup
            break
    
    if not next_checkup and current_week < 40:
        # If no specific checkup found but still pregnant, default to weekly
        next_week = current_week + 1
        next_checkup = {"week": next_week, "description": "Weekly monitoring and cervical checks"}
    
    return next_checkup

def get_fetal_development_info(weeks):
    if weeks <= 13:
        return "First Trimester: Major organs and structures are forming. Baby's heart begins to beat, and limbs are developing."
    elif weeks <= 26:
        return "Second Trimester: Baby's movements become noticeable. Features like fingernails and hair are forming."
    else:
        return "Third Trimester: Baby's organs are maturing, and they're gaining weight. Brain development is rapid."

def get_prenatal_reminders(weeks):
    if weeks <= 13:
        return [
            "Schedule your first ultrasound",
            "Take prenatal vitamins",
            "Avoid alcohol and smoking",
            "Stay hydrated"
        ]
    elif weeks <= 26:
        return [
            "Schedule anatomy scan",
            "Start pregnancy exercises",
            "Monitor baby's movements",
            "Plan your birth classes"
        ]
    else:
        return [
            "Prepare hospital bag",
            "Monitor contractions",
            "Complete birth plan",
            "Schedule weekly check-ups"
        ]

def get_nutrition_recommendations(weeks):
    if weeks <= 13:
        return {
            'advice': 'Focus on folic acid and iron-rich foods to support early development',
            'suggestions': [
                'Dark leafy greens (spinach, kale)',
                'Lean proteins (chicken, fish)',
                'Whole grain cereals fortified with folic acid',
                'Citrus fruits for vitamin C',
                'Low-fat dairy products',
                'Nuts and seeds',
                'Stay hydrated with water'
            ]
        }
    elif weeks <= 26:
        return {
            'advice': 'Increase calcium and protein intake for bone and tissue development',
            'suggestions': [
                'Greek yogurt and cheese',
                'Salmon and other fatty fish (twice a week)',
                'Lean meats and poultry',
                'Beans and legumes',
                'Quinoa and whole grains',
                'Fresh fruits and vegetables',
                'Calcium-fortified beverages'
            ]
        }
    else:
        return {
            'advice': 'Focus on energy-rich foods and continued nutrition for final growth',
            'suggestions': [
                'Complex carbohydrates',
                'Protein-rich foods',
                'Healthy fats (avocados, olive oil)',
                'Iron-rich foods',
                'Calcium-rich foods',
                'Fresh fruits and vegetables',
                'Stay well-hydrated'
            ]
        }

@app.route('/menopause')
def menopause():
    return render_template('menopause/index.html')

@app.route('/menopause/results')
def menopause_results():
    if 'menopause_data' not in session:
        flash('Please submit your menopause information first.', 'warning')
        return redirect(url_for('menopause'))
    return render_template('menopause/results.html', **session['menopause_data'])

@app.route('/menopause/track', methods=['POST'])
def menopause_track():
    try:
        # Get form data
        age = request.form.get('age', type=int)
        last_period = request.form.get('last_period', type=int)
        symptoms = request.form.getlist('symptoms')
        
        print(f"Received data - Age: {age}, Last Period: {last_period}, Symptoms: {symptoms}")  # Debug log
        
        if not all([age, last_period, symptoms]):
            flash('Please provide all required information', 'error')
            return redirect(url_for('menopause'))
        
        # Prepare Groq prompt
        prompt = f"""Analyze the following hormonal health data and provide detailed insights:
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

        print("Sending request to Groq...")  # Debug log
        
        # Get analysis from Groq
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful and empathetic AI assistant specializing in women's health."},
                {"role": "user", "content": prompt}
            ],
            model="mixtral-8x7b-32768",  
            temperature=0.7,
            max_tokens=1000
        )
        
        analysis = chat_completion.choices[0].message.content
        print(f"Received analysis from Groq: {analysis[:100]}...")  # Debug log
        
        # Store in session
        session['menopause_data'] = {
            'age': age,
            'last_period': last_period,
            'symptoms': symptoms,
            'analysis': analysis
        }
        
        return render_template('menopause/results.html', 
                             age=age,
                             last_period=last_period,
                             symptoms=symptoms,
                             analysis=analysis)
                             
    except Exception as e:
        print(f"Error in menopause_track: {str(e)}")  # Debug log
        flash(f'Error analyzing menopause data: {str(e)}', 'error')
        return redirect(url_for('menopause'))

@app.route('/analyze_report', methods=['POST'])
def analyze_report():
    try:
        if 'report' not in request.files:
            return jsonify({'error': 'No report file uploaded'}), 400
        
        file = request.files['report']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        concerns = request.form.get('concerns', '')
        
        # Read and process the PDF file
        pdf_text = ""
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                pdf_text += page.extract_text()
        except Exception as e:
            return jsonify({'error': f'Error reading PDF: {str(e)}'}), 400

        # Prepare the prompt for Groq
        prompt = f"""Analyze the following health report and patient concerns. Provide a detailed clinical analysis in the following format:

Health Report Content:
{pdf_text}

Patient Concerns:
{concerns}

Please provide a comprehensive analysis covering these aspects:
1. Clinical Analysis: Current symptoms, severity, and patterns
2. Diagnostic Findings: Key observations and potential underlying factors
3. Treatment Recommendations: Evidence-based suggestions for management
4. Follow-up Plan: Next steps and monitoring recommendations

Important: Format your response with HTML tags. Use <strong> tags to emphasize key medical terms, findings, and recommendations. Make sure the response is well-structured with paragraphs (<p> tags) and bullet points (<ul> and <li> tags) where appropriate.

Example format:
<p>Clinical findings indicate <strong>moderate hypertension</strong> with...</p>
<ul>
    <li>Blood pressure shows <strong>consistent elevation</strong> in...</li>
</ul>"""

        # Call Groq API
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful and empathetic AI assistant specializing in women's health."},
                {"role": "user", "content": prompt}
            ],
            model="mixtral-8x7b-32768",  
            temperature=0.3,
            max_tokens=1000
        )

        # Process the response
        response_text = completion.choices[0].message.content

        # Parse the response into sections
        sections = {
            'clinical_analysis': '',
            'diagnostic_findings': '',
            'recommendations': '',
            'follow_up_plan': ''
        }

        current_section = None
        section_content = []
        
        for line in response_text.split('\n'):
            if 'Clinical Analysis:' in line:
                current_section = 'clinical_analysis'
                section_content = []
                continue
            elif 'Diagnostic Findings:' in line:
                if current_section:
                    sections[current_section] = '\n'.join(section_content)
                current_section = 'diagnostic_findings'
                section_content = []
                continue
            elif 'Treatment Recommendations:' in line:
                if current_section:
                    sections[current_section] = '\n'.join(section_content)
                current_section = 'recommendations'
                section_content = []
                continue
            elif 'Follow-up Plan:' in line:
                if current_section:
                    sections[current_section] = '\n'.join(section_content)
                current_section = 'follow_up_plan'
                section_content = []
                continue
            
            if current_section and line.strip():
                # Ensure proper HTML formatting
                if not line.strip().startswith(('<p>', '<ul>', '<li>', '</ul>', '</p>')):
                    line = f"<p>{line}</p>"
                section_content.append(line.strip())

        # Add the last section
        if current_section and section_content:
            sections[current_section] = '\n'.join(section_content)

        # Clean up the sections and ensure proper HTML structure
        for key in sections:
            content = sections[key]
            if not content.strip().startswith('<'):
                content = f"<p>{content}</p>"
            sections[key] = content.strip()

        return jsonify({
            'success': True,
            'analysis': sections
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/hormonal-balance/analyze', methods=['POST'])
@login_required
def analyze_hormonal_balance():
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            data = request.form.to_dict()
            
        logging.info(f"Received form data: {data}")
            
        # Extract data safely
        symptoms = data.get('symptoms', [])
        if isinstance(symptoms, str):
            symptoms = [symptoms]
        elif not symptoms:
            symptoms = []
        
        # Get user information
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, username FROM users WHERE id = ?", (session['user_id'],))
        user_data = cursor.fetchone()

        if not user_data:
            flash('User information not found', 'error')
            return redirect(url_for('pregnancy_results'))

        # Add patient information to report content
        report_content = f"Patient ID: {user_data[0]}\nPatient Name: {user_data[1]}\n\n" + report_content
        
        # Get user's language from session
        user_language = session.get('language', 'en')
        
        # Language-specific instructions for the AI
        language_instructions = {
            'en': 'Respond in English',
            'es': 'Responde en Español',
            'hi': 'हिंदी में जवाब दें',
            'ta': 'தமிழில் பதிலளிக்கவும்',
            'te': 'తెలుగులో సమాధానం ఇవ్వండి'
        }
        
        # Simplified prompt with language support
        prompt = f"""Return a JSON object with text in {language_instructions.get(user_language, 'English')}. The structure must be exactly as shown below:
{{
    "overall_score": <number between 0-100>,
    "health_status": <status in {SUPPORTED_LANGUAGES.get(user_language, 'English')}>,
    "activity_level": <level in {SUPPORTED_LANGUAGES.get(user_language, 'English')}>,
    "sleep_quality": <quality in {SUPPORTED_LANGUAGES.get(user_language, 'English')}>,
    "symptoms": [
        {{
            "name": <symptom name in {SUPPORTED_LANGUAGES.get(user_language, 'English')}>,
            "severity": <severity in {SUPPORTED_LANGUAGES.get(user_language, 'English')}>,
            "percentage": <number between 0-100>
        }}
    ],
    "metrics": [
        {{
            "name": <metric name in {SUPPORTED_LANGUAGES.get(user_language, 'English')}>,
            "value": <value in {SUPPORTED_LANGUAGES.get(user_language, 'English')}>,
            "percentage": <number between 0-100>
        }}
    ],
    "recommendations": [
        {{
            "title": <title in {SUPPORTED_LANGUAGES.get(user_language, 'English')}>,
            "description": <advice in {SUPPORTED_LANGUAGES.get(user_language, 'English')}>
        }}
    ]
}}

Health data to analyze:
- Age: {data.get('age', 'Not provided')}
- Gender: {data.get('gender', 'Not provided')}
- Symptoms: {', '.join(symptoms) if symptoms else 'None'}
- Sleep Quality: {data.get('sleep_quality', 'Not provided')}
- Exercise Frequency: {data.get('exercise_frequency', 'Not provided')}
- Stress Level: {data.get('stress_level', 'Not provided')}"""

        logging.info("Sending request to Groq API...")
            
        try:
            # Call Groq API with language support
            response = groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
                        "content": f"""You are a health analysis assistant that returns JSON responses in {SUPPORTED_LANGUAGES.get(user_language, 'English')}.
                        All text fields in the JSON must be in {SUPPORTED_LANGUAGES.get(user_language, 'English')} only.
                        Maintain consistent language throughout the response.
                        Do not include any markdown formatting or additional explanations."""
                    },
                    {"role": "user", "content": prompt}
                ],
                model="mixtral-8x7b-32768",
                temperature=0.3,
                max_tokens=500
            )
            
            logging.info("Received response from Groq API")
            
            # Parse response
            analysis_text = response.choices[0].message.content.strip()
            if analysis_text.startswith('```json'):
                analysis_text = analysis_text[7:]
            if analysis_text.endswith('```'):
                analysis_text = analysis_text[:-3]
            
            try:
                analysis = json.loads(analysis_text)
                logging.info("Successfully parsed JSON response")
                
                # Validate required fields
                required_fields = ['overall_score', 'health_status', 'symptoms', 'recommendations']
                for field in required_fields:
                    if field not in analysis:
                        raise ValueError(f"Missing required field: {field}")
                
                # Limit recommendations to 3
                if len(analysis.get('recommendations', [])) > 3:
                    analysis['recommendations'] = analysis['recommendations'][:3]
                
                # Store in session
                session['hormonal_analysis'] = analysis
                return jsonify({"status": "success", "data": analysis})

            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON response: {e}")
                logging.error(f"Raw response: {analysis_text}")
                return jsonify({
                    "status": "error",
                    "message": "Failed to process the analysis results. Please try again."
                }), 500

        except Exception as e:
            logging.error(f"Groq API error: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "Failed to generate analysis. Please try again later."
            }), 500

    except Exception as e:
        logging.error(f"General error in analysis: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred. Please try again."
        }), 500

@app.route('/hormonal-balance/dashboard')
def show_hormonal_dashboard():
    try:
        # Get analysis from session
        analysis = session.get('hormonal_analysis')
        if not analysis:
            flash('No analysis data found. Please complete the assessment first.', 'error')
            return redirect(url_for('show_hormonal_form'))
        
        return render_template('hormonal_balance_dashboard.html', data=analysis)
    except Exception as e:
        logging.error(f"Error showing dashboard: {str(e)}")
        flash('Error displaying analysis. Please try again.', 'error')
        return redirect(url_for('show_hormonal_form'))

@app.route('/hormonal-balance/form')
def show_hormonal_form():
    return render_template('hormonal_balance_form.html')

if __name__ == '__main__':
    app.run(debug=True, port=5099)