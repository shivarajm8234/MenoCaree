import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import time

load_dotenv()

class Database:
    def __init__(self):
        self.connection = None
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        self.connect()
        self.create_tables()  # Create tables on initialization

    def connect(self):
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                if self.connection is None or self.connection.closed:
                    self.connection = psycopg2.connect(
                        host=os.getenv('DB_HOST', 'localhost'),
                        user=os.getenv('DB_USER', 'postgres'),
                        password=os.getenv('DB_PASSWORD'),
                        database=os.getenv('DB_NAME', 'menocare'),
                        cursor_factory=RealDictCursor
                    )
                    self.connection.autocommit = True
                    # Test the connection
                    with self.connection.cursor() as cursor:
                        cursor.execute("SELECT 1")
                    return
            except psycopg2.Error as e:
                retry_count += 1
                print(f"Database connection error: {str(e)}")
                if retry_count < self.max_retries:
                    print(f"Database connection attempt {retry_count} failed. Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"Failed to connect to database after {self.max_retries} attempts: {str(e)}")
                    raise

    def execute_query(self, query, params=None):
        max_attempts = 2
        attempt = 0
        
        while attempt < max_attempts:
            try:
                if not self.connection or self.connection.closed:
                    self.connect()
                    
                with self.connection.cursor() as cursor:
                    cursor.execute(query, params)
                    if query.strip().upper().startswith('SELECT'):
                        return cursor.fetchall()
                    return None
            except psycopg2.Error as e:
                print(f"Database error: {str(e)}")
                attempt += 1
                if attempt == max_attempts:
                    raise
                self.connect()  # Try to reconnect before the next attempt

    def fetch_one(self, query, params=None):
        try:
            if not self.connection or self.connection.closed:
                self.connect()
                
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()
        except psycopg2.Error as e:
            print(f"Database error: {str(e)}")
            raise

    def fetch_all(self, query, params=None):
        try:
            if not self.connection or self.connection.closed:
                self.connect()
                
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except psycopg2.Error as e:
            print(f"Database error: {str(e)}")
            raise

    def create_tables(self):
        try:
            # Create tables for hormonal balance tracking
            queries = [
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS mood_tracker (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    date DATE NOT NULL,
                    mood_rating INTEGER CHECK (mood_rating BETWEEN 1 AND 5),
                    hot_flash_intensity INTEGER CHECK (hot_flash_intensity BETWEEN 0 AND 5),
                    period_status VARCHAR(50),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS nutrition_plan (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    date DATE NOT NULL,
                    meal_type VARCHAR(20),
                    food_items JSONB,
                    nutrients_data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS exercise_tracking (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    date DATE NOT NULL,
                    exercise_type VARCHAR(100),
                    duration INTEGER,
                    intensity VARCHAR(20),
                    calories_burned INTEGER,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS hormonal_metrics (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    date DATE NOT NULL,
                    estrogen_level FLOAT,
                    progesterone_level FLOAT,
                    thyroid_level FLOAT,
                    cortisol_level FLOAT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            ]
            
            for query in queries:
                self.execute_query(query)
            print("Successfully created all required tables")
        except psycopg2.Error as e:
            print(f"Error creating tables: {str(e)}")
            raise

    def close(self):
        if self.connection and not self.connection.closed:
            self.connection.close()
            self.connection = None
