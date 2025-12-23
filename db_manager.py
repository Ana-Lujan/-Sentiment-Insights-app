import psycopg2
import pandas as pd
import os
from urllib.parse import urlparse

# Global flag for DB availability
DB_AVAILABLE = False

# Database connection parameters
# Check for DATABASE_URL first (Render, Railway, etc.)
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Parse DATABASE_URL for Render/Railway format
    parsed = urlparse(DATABASE_URL)
    DB_HOST = parsed.hostname
    DB_NAME = parsed.path.lstrip('/')
    DB_USER = parsed.username
    DB_PASS = parsed.password
else:
    # Fallback to individual environment variables
    DB_HOST = os.environ.get("PG_HOST", "localhost")
    DB_NAME = os.environ.get("PG_DB_NAME", "sentiment_db")
    DB_USER = os.environ.get("PG_USER", "postgres")
    DB_PASS = os.environ.get("PG_PASS", "")

def get_db_connection():
    """Establece y retorna la conexión a PostgreSQL con codificación UTF-8."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            connect_timeout=5,
            client_encoding='utf8'  # Force UTF-8 encoding
        )
        return conn
    except psycopg2.OperationalError as e:
        raise ConnectionError(f"Error de conexión a la DB. Verifique PG_HOST, PG_DB_NAME y credenciales. Detalle: {e}")

def initialize_db():
    """
    Conecta a la base de datos y crea la tabla insights si no existe.

    Returns:
        bool: True si la inicialización fue exitosa, False en caso contrario.
    """
    global DB_AVAILABLE
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS insights (
                id SERIAL PRIMARY KEY,
                comentario TEXT,
                sentimiento VARCHAR(20),
                emocion VARCHAR(30),
                intensidad REAL,
                confianza REAL,
                fecha_analisis TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully.")
        DB_AVAILABLE = True
        return True
    except ConnectionError as e:
        print(f"Connection error initializing database: {e}")
        DB_AVAILABLE = False
        return False
    except Exception as e:
        print(f"Error initializing database: {e}")
        DB_AVAILABLE = False
        return False

def insert_analysis(comentario, sentimiento, emocion, intensidad, confianza):
    """
    Inserta un nuevo resultado de análisis en la base de datos con codificación UTF-8.

    Args:
        comentario (str): El texto del comentario.
        sentimiento (str): El sentimiento analizado.
        emocion (str): La emoción correspondiente.
        intensidad (float): La intensidad del sentimiento.
        confianza (float): La confianza del modelo.

    Returns:
        bool: True si la inserción fue exitosa, False en caso contrario.
    """
    if not DB_AVAILABLE:
        print("DB not available, skipping insert.")
        return True  # Skip for demo
    try:
        # Sanitize text: remove null bytes and ensure UTF-8 compatibility
        def sanitize_text(text):
            if not text:
                return ""
            # Remove null bytes and other problematic characters
            text = text.replace('\x00', '').replace('\ufeff', '')
            # Ensure UTF-8 compatibility
            return text.encode('utf-8', errors='replace').decode('utf-8')

        comentario = sanitize_text(comentario)
        sentimiento = sanitize_text(sentimiento)
        emocion = sanitize_text(emocion)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO insights (comentario, sentimiento, emocion, intensidad, confianza)
            VALUES (%s, %s, %s, %s, %s)
        ''', (comentario, sentimiento, emocion, intensidad, confianza))
        conn.commit()
        cursor.close()
        conn.close()
        print("Analysis inserted successfully.")
        return True
    except ConnectionError as e:
        print(f"Connection error inserting analysis: {e}")
        return False
    except Exception as e:
        print(f"Error inserting analysis: {e}")
        return False

def fetch_all_results():
    """
    Obtiene todos los resultados de análisis de la base de datos.

    Returns:
        list: Lista de tuplas con los resultados, o lista vacía si hay error.
    """
    if not DB_AVAILABLE:
        print("DB not available, returning empty results.")
        return []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT comentario, sentimiento, emocion, intensidad, confianza, fecha_analisis FROM insights')
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except ConnectionError as e:
        print(f"Connection error fetching results: {e}")
        return []
    except Exception as e:
        print(f"Error fetching results: {e}")
        return []