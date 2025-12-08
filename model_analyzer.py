import re
import time

# Lazy load the sentiment analysis model for Spanish
model = None

def get_model():
    global model
    if model is None:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Loading sentiment analysis model... (attempt {attempt + 1}/{max_retries})")
                from transformers import pipeline
                model = pipeline("sentiment-analysis", model="finiteautomata/beto-sentiment-analysis")
                print("Model loaded successfully.")
                break
            except Exception as e:
                print(f"Error loading model (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    backoff_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    print(f"Retrying in {backoff_time} seconds...")
                    time.sleep(backoff_time)
                else:
                    raise RuntimeError("No se pudo cargar el modelo de análisis de sentimiento después de varios intentos. Verifique la conexión a internet o el estado del servicio.")
    return model

def get_emotion_from_sentiment(sentimiento, intensity=0.5):
    """
    Obtiene la emoción basada en el sentimiento y su intensidad.

    Args:
        sentimiento (str): La etiqueta de sentimiento.
        intensity (float): Intensidad del sentimiento (0.0-1.0).

    Returns:
        str: La emoción correspondiente.
    """
    if sentimiento == 'POSITIVO':
        if intensity > 0.7:
            return 'Alegría Extrema'
        elif intensity > 0.5:
            return 'Alegría'
        else:
            return 'Satisfacción'
    elif sentimiento == 'NEGATIVO':
        if intensity > 0.7:
            return 'Ira Extrema'
        elif intensity > 0.5:
            return 'Enojo/Frustración'
        else:
            return 'Descontento'
    else:  # NEUTRAL
        if intensity > 0.6:
            return 'Sorpresa'
        elif intensity > 0.4:
            return 'Indiferencia'
        else:
            return 'NEUTRALIDAD'

def analyze_text(text_input):
    """
    Analiza el sentimiento del texto de entrada con métricas avanzadas.

    Args:
        text_input (str): El texto a analizar.

    Returns:
        tuple: (texto_original, sentimiento, emocion, intensidad, confianza)
    """
    # Preprocesamiento mejorado
    cleaned_text = text_input.strip().lower()

    # Eliminación de enlaces
    cleaned_text = re.sub(r'http\S+|www\S+|https\S+', '', cleaned_text, flags=re.MULTILINE)

    # Eliminación de puntuación excesiva pero manteniendo expresiones
    cleaned_text = re.sub(r'[^\w\s¡!¿?.,]', '', cleaned_text)

    if not cleaned_text or len(cleaned_text.strip()) < 3:
        return text_input, 'NEUTRAL', 'VACÍO', 0.0, 0.0

    # Try AI model first for better accuracy
    try:
        model = get_model()
        result = model(cleaned_text)[0]
        label = result['label']  # e.g., 'POS', 'NEG', 'NEU'
        confidence = result['score']

        # Map the label to sentiment
        if label == 'POS':
            sentimiento = 'POSITIVO'
        elif label == 'NEG':
            sentimiento = 'NEGATIVO'
        else:
            sentimiento = 'NEUTRAL'

    except Exception as e:
        print(f"AI model failed, using fallback analysis: {e}")
        # Fallback to simple keyword analysis
        return analyze_text_fallback(text_input)

    # Calculate intensity based on confidence and text characteristics
    intensity = calculate_intensity(cleaned_text, confidence, sentimiento)

    # Get emotion from sentiment and intensity
    emocion = get_emotion_from_sentiment(sentimiento, intensity)

    return text_input, sentimiento, emocion, intensity, confidence

def calculate_intensity(text, confidence, sentiment):
    """
    Calculate sentiment intensity based on text characteristics and model confidence.

    Args:
        text (str): The input text
        confidence (float): Model confidence score
        sentiment (str): Sentiment label

    Returns:
        float: Intensity score between 0.0 and 1.0
    """
    base_intensity = confidence

    # Text-based intensity modifiers
    text_length = len(text.split())
    exclamation_count = text.count('!') + text.count('¡')
    question_count = text.count('?') + text.count('¿')
    caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0

    # Intensity boosters
    intensity_multiplier = 1.0

    # Length factor (longer texts might be more intense)
    if text_length > 20:
        intensity_multiplier *= 1.1
    elif text_length < 5:
        intensity_multiplier *= 0.9

    # Punctuation intensity
    if exclamation_count > 0:
        intensity_multiplier *= (1.0 + min(exclamation_count * 0.1, 0.3))
    if question_count > 0:
        intensity_multiplier *= (1.0 + min(question_count * 0.05, 0.2))

    # Capitalization intensity (shouting)
    if caps_ratio > 0.3:
        intensity_multiplier *= (1.0 + min(caps_ratio * 0.5, 0.4))

    # Sentiment-specific adjustments
    if sentiment == 'NEGATIVO':
        # Negative sentiments can be more intense
        intensity_multiplier *= 1.1
    elif sentiment == 'POSITIVO':
        # Positive sentiments are often more expressive
        intensity_multiplier *= 1.05

    final_intensity = min(base_intensity * intensity_multiplier, 1.0)
    return round(final_intensity, 3)

def analyze_text_fallback(text_input):
    """
    Fallback analysis method using simple keyword matching when AI model is unavailable.
    """
    # Ensure UTF-8 compatibility
    text_input = text_input.encode('utf-8', errors='replace').decode('utf-8')
    cleaned_text = text_input.strip().lower()

    # Simple keyword-based sentiment analysis
    positive_words = ['feliz', 'bueno', 'excelente', 'genial', 'perfecto', 'maravilloso', 'increíble', 'fantástico', 'hermoso', 'amor', 'alegría', 'éxito', 'triunfo', 'bien', 'positivo', 'contento']
    negative_words = ['triste', 'malo', 'terrible', 'horrible', 'odio', 'enojo', 'frustración', 'problema', 'error', 'fallo', 'desastre', 'miedo', 'angustia', 'mal', 'negativo', 'descontento']

    positive_count = sum(1 for word in positive_words if word in cleaned_text)
    negative_count = sum(1 for word in negative_words if word in cleaned_text)

    if positive_count > negative_count:
        sentimiento = 'POSITIVO'
        confidence = min(0.5 + (positive_count * 0.1), 0.9)
    elif negative_count > positive_count:
        sentimiento = 'NEGATIVO'
        confidence = min(0.5 + (negative_count * 0.1), 0.9)
    else:
        sentimiento = 'NEUTRAL'
        confidence = 0.5

    intensity = calculate_intensity(cleaned_text, confidence, sentimiento)
    emocion = get_emotion_from_sentiment(sentimiento, intensity)

    return text_input, sentimiento, emocion, intensity, confidence