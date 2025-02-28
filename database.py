import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import time
import logging

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
                    # Get database URL from environment variable
                    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:uPnzIOoMWKueCNawwlhioIekzfSgtack@metro.proxy.rlwy.net:33517/railway')
                    
                    try:
                        self.connection = psycopg2.connect(
                            database_url,
                            cursor_factory=RealDictCursor
                        )
                        self.connection.autocommit = True
                        
                        # Test the connection
                        with self.connection.cursor() as cursor:
                            cursor.execute('SELECT 1')
                        logging.info("Successfully connected to Railway.app database")
                        return
                    except psycopg2.Error as e:
                        logging.error(f"Database connection error: {str(e)}")
                        retry_count += 1
                        if retry_count < self.max_retries:
                            logging.info(f"Database connection attempt {retry_count} failed. Retrying in {self.retry_delay} seconds...")
                            time.sleep(self.retry_delay)
                        else:
                            logging.error("Max retries reached. Could not establish database connection.")
                            raise
            except psycopg2.Error as e:
                logging.error(f"Database connection error: {str(e)}")
                retry_count += 1
                if retry_count < self.max_retries:
                    logging.info(f"Database connection attempt {retry_count} failed. Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logging.error("Max retries reached. Could not establish database connection.")
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
            # First, check and upgrade users table if needed
            self.upgrade_users_table()
            
            # Create tables for hormonal balance tracking
            # First ensure users table is properly created
            self.execute_query("""
                DROP TABLE IF EXISTS users CASCADE;
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            queries = [
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

    def upgrade_users_table(self):
        try:
            # Check if password_hash column exists
            check_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'password_hash';
            """
            result = self.fetch_all(check_query)
            
            if not result:
                # Add password_hash column if it doesn't exist
                alter_query = "ALTER TABLE users ADD COLUMN password_hash VARCHAR(255) NOT NULL DEFAULT '';"
                self.execute_query(alter_query)
                logging.info("Added password_hash column to users table")
        except psycopg2.Error as e:
            logging.error(f"Error upgrading users table: {str(e)}")
            raise

    def close(self):
        if self.connection and not self.connection.closed:
            self.connection.close()
            self.connection = None
