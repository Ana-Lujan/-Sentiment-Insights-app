import psycopg2
import pandas as pd

# Database connection parameters
# Replace with your actual PostgreSQL credentials
DB_HOST = "localhost"
DB_NAME = "sentiment_db"
DB_USER = "your_postgres_user"
DB_PASS = "your_postgres_password"

def get_db_connection():
    """Get a database connection."""
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

def initialize_db():
    """Connect to the database and create the insights table if it doesn't exist."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS insights (
                id SERIAL PRIMARY KEY,
                comentario TEXT,
                sentimiento VARCHAR(20),
                emocion VARCHAR(20),
                probabilidad REAL,
                fecha_analisis TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")

def insert_analysis(comentario, sentimiento, emocion, probabilidad):
    """Insert a new analysis result into the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO insights (comentario, sentimiento, emocion, probabilidad)
            VALUES (%s, %s, %s, %s)
        ''', (comentario, sentimiento, emocion, probabilidad))
        conn.commit()
        cursor.close()
        conn.close()
        print("Analysis inserted successfully.")
    except Exception as e:
        print(f"Error inserting analysis: {e}")

def fetch_all_results():
    """Fetch all analysis results from the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT comentario, sentimiento, emocion, probabilidad, fecha_analisis FROM insights')
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except Exception as e:
        print(f"Error fetching results: {e}")
        return []