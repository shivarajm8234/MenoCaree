from flask import Blueprint, render_template

games = Blueprint('games', __name__)

@games.route('/games')
def games_dashboard():
    return render_template('games/games_dashboard.html')

@games.route('/games/quiz')
def quiz_game():
    return render_template('games/quiz_game/quiz.html')

@games.route('/games/memory')
def memory_game():
    return render_template('games/memory_match/memory.html')

@games.route('/games/breathing')
def breathing_game():
    return render_template('games/breathing_exercise/breathing.html')

@games.route('/games/mood-matcher')
def mood_matcher_game():
    return render_template('games/mood_matcher/index.html')
