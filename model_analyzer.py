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
    Analiza el sentimiento del texto de entrada con métricas avanzadas y explicaciones detalladas.

    Args:
        text_input (str): El texto a analizar.

    Returns:
        tuple: (texto_original, sentimiento, emocion, intensidad, confianza, explicacion)
    """
    # Preprocesamiento mejorado
    cleaned_text = text_input.strip().lower()

    # Eliminación de enlaces
    cleaned_text = re.sub(r'http\S+|www\S+|https\S+', '', cleaned_text, flags=re.MULTILINE)

    # Eliminación de puntuación excesiva pero manteniendo expresiones
    cleaned_text = re.sub(r'[^\w\s¡!¿?.,]', '', cleaned_text)

    if not cleaned_text or len(cleaned_text.strip()) < 3:
        explanation = "El texto es demasiado corto o vacío para realizar un análisis significativo."
        return text_input, 'NEUTRAL', 'VACÍO', 0.0, 0.0, explanation

    # Use enhanced fallback analysis with explanations
    print("Using enhanced keyword-based analysis with explanations")
    return analyze_text_fallback_detailed(text_input)

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

def analyze_text_fallback_detailed(text_input):
    """
    Enhanced fallback analysis method with detailed explanations for professional insights.
    """
    # Ensure UTF-8 compatibility
    text_input = text_input.encode('utf-8', errors='replace').decode('utf-8')
    cleaned_text = text_input.strip().lower()

    # Comprehensive Spanish keyword lists for sentiment analysis
    positive_words = [
        # Emociones positivas
        'feliz', 'alegre', 'contento', 'satisfecho', 'entusiasmado', 'emocionado', 'eufórico', 'júbilo',
        'amor', 'cariño', 'afecto', 'ternura', 'pasión', 'devoción', 'adoración',
        'alegría', 'júbilo', 'felicidad', 'placer', 'gozo', 'éxtasis', 'deleite',
        # Calidad positiva
        'excelente', 'genial', 'perfecto', 'maravilloso', 'increíble', 'fantástico', 'hermoso', 'bello',
        'espectacular', 'magnífico', 'sublime', 'excepcional', 'sobresaliente', 'brillante',
        'estupendo', 'fabuloso', 'fenomenal', 'impresionante', 'asombroso', 'admirable',
        # Éxito y logro
        'éxito', 'triunfo', 'victoria', 'logro', 'conquista', 'realización', 'cumplimiento',
        'bien', 'bueno', 'positivo', 'óptimo', 'ideal', 'superior', 'mejor',
        # Aprobación
        'aprobado', 'aceptado', 'aplaudido', 'elogioso', 'loable', 'meritorio', 'digno',
        'recomendado', 'apoyado', 'respaldado', 'favorecido', 'preferido',
        # Satisfacción
        'satisfecho', 'complacido', 'agradecido', 'reconocido', 'valorado', 'apreciado',
        'útil', 'eficaz', 'eficiente', 'productivo', 'beneficioso', 'provechoso'
    ]

    negative_words = [
        # Emociones negativas
        'triste', 'deprimido', 'desanimado', 'abatido', 'melancólico', 'apenado', 'afligido',
        'enojo', 'ira', 'furia', 'rabia', 'indignación', 'resentimiento', 'amargura',
        'miedo', 'terror', 'pánico', 'angustia', 'ansiedad', 'preocupación', 'temor',
        'odio', 'aversión', 'repulsión', 'desprecio', 'animadversión', 'hostilidad',
        'frustración', 'desesperación', 'desilusión', 'decepción', 'desengaño',
        # Problemas
        'problema', 'dificultad', 'obstáculo', 'impedimento', 'traba', 'complicación',
        'error', 'fallo', 'defecto', 'imperfección', 'falla', 'avería', 'mal funcionamiento',
        'desastre', 'catástrofe', 'calamidad', 'tragedia', 'drama', 'desgracia',
        # Calidad negativa
        'malo', 'terrible', 'horrible', 'espantoso', 'pésimo', 'abominable', 'detestable',
        'deficiente', 'insuficiente', 'inadecuado', 'inapropiado', 'incorrecto',
        'mal', 'negativo', 'desfavorable', 'perjudicial', 'dañino', 'nocivo',
        # Insatisfacción
        'descontento', 'insatisfecho', 'desilusionado', 'decepcionado', 'desengañado',
        'queja', 'reclamo', 'denuncia', 'protesta', 'disconformidad',
        'crítica', 'censura', 'condena', 'reprobación', 'desaprobación'
    ]

    # Intensifiers that can amplify sentiment
    intensifiers = ['muy', 'mucho', 'bastante', 'extremadamente', 'increíblemente', 'terriblemente',
                   'absolutamente', 'completamente', 'totalmente', 'realmente', 'verdaderamente']

    # Negation words that can flip sentiment
    negations = ['no', 'nunca', 'jamás', 'tampoco', 'ni', 'sin', 'menos']

    # Count matches with context awareness
    positive_count = 0
    negative_count = 0
    found_positive_words = []
    found_negative_words = []
    found_intensifiers = []
    found_negations = []

    words = cleaned_text.split()
    for i, word in enumerate(words):
        # Check for negations affecting the next word
        negation_multiplier = 1
        if i > 0 and words[i-1] in negations:
            negation_multiplier = -0.5  # Reduce impact of negated words
            if words[i-1] not in found_negations:
                found_negations.append(words[i-1])

        # Check for intensifiers
        intensifier_multiplier = 1
        if i > 0 and words[i-1] in intensifiers:
            intensifier_multiplier = 1.5
            if words[i-1] not in found_intensifiers:
                found_intensifiers.append(words[i-1])

        if word in positive_words:
            positive_count += (1 * intensifier_multiplier * negation_multiplier)
            if word not in found_positive_words:
                found_positive_words.append(word)
        elif word in negative_words:
            negative_count += (1 * intensifier_multiplier * negation_multiplier)
            if word not in found_negative_words:
                found_negative_words.append(word)

    # Determine sentiment with enhanced logic
    total_sentiment_score = positive_count - negative_count

    if total_sentiment_score > 0.5:
        sentimiento = 'POSITIVO'
        confidence = min(0.5 + (total_sentiment_score * 0.1), 0.95)
    elif total_sentiment_score < -0.5:
        sentimiento = 'NEGATIVO'
        confidence = min(0.5 + (abs(total_sentiment_score) * 0.1), 0.95)
    else:
        sentimiento = 'NEUTRAL'
        confidence = 0.5

    intensity = calculate_intensity(cleaned_text, confidence, sentimiento)
    emocion = get_emotion_from_sentiment(sentimiento, intensity)

    # Generate detailed explanation
    explanation = generate_analysis_explanation(
        text_input, sentimiento, emocion, confidence, intensity,
        found_positive_words, found_negative_words, found_intensifiers, found_negations,
        positive_count, negative_count
    )

    return text_input, sentimiento, emocion, intensity, confidence, explanation

def generate_analysis_explanation(text, sentiment, emotion, confidence, intensity,
                                positive_words, negative_words, intensifiers, negations,
                                pos_count, neg_count):
    """
    Generate a professional explanation for the sentiment analysis result.
    """
    explanation_parts = []

    # Main sentiment explanation
    if sentiment == 'POSITIVO':
        explanation_parts.append(f"✅ Análisis POSITIVO detectado con {confidence:.1%} de confianza.")
        if positive_words:
            explanation_parts.append(f"Palabras positivas identificadas: {', '.join(positive_words)}.")
        if pos_count > 0:
            explanation_parts.append(f"Puntuación positiva: {pos_count:.1f} (basado en {len(positive_words)} términos positivos).")
    elif sentiment == 'NEGATIVO':
        explanation_parts.append(f"❌ Análisis NEGATIVO detectado con {confidence:.1%} de confianza.")
        if negative_words:
            explanation_parts.append(f"Palabras negativas identificadas: {', '.join(negative_words)}.")
        if neg_count > 0:
            explanation_parts.append(f"Puntuación negativa: {neg_count:.1f} (basado en {len(negative_words)} términos negativos).")
    else:
        explanation_parts.append(f"⚪ Análisis NEUTRAL detectado. El texto no muestra polaridad emocional clara.")

    # Emotion explanation
    emotion_explanations = {
        'Alegría Extrema': 'Emoción de máxima satisfacción y entusiasmo.',
        'Alegría': 'Sentimiento positivo de satisfacción y bienestar.',
        'Satisfacción': 'Estado de contentamiento moderado.',
        'Indiferencia': 'Ausencia de emoción fuerte, neutralidad emocional.',
        'Enojo/Frustración': 'Insatisfacción moderada con elementos de molestia.',
        'Ira Extrema': 'Máxima expresión de enfado y descontento.',
        'Sorpresa': 'Reacción emocional ante lo inesperado.',
        'VACÍO': 'Sin contenido emocional detectable.'
    }
    if emotion in emotion_explanations:
        explanation_parts.append(f"🎭 Emoción detectada: {emotion} - {emotion_explanations[emotion]}")

    # Intensity explanation
    intensity_level = "baja" if intensity < 0.4 else "moderada" if intensity < 0.7 else "alta"
    explanation_parts.append(f"📊 Intensidad emocional: {intensity:.1f}/1.0 ({intensity_level}).")

    # Context modifiers explanation
    if intensifiers:
        explanation_parts.append(f"🔥 Intensificadores detectados: {', '.join(intensifiers)} - Aumentan la fuerza emocional.")
    if negations:
        explanation_parts.append(f"🔄 Negaciones detectadas: {', '.join(negations)} - Pueden invertir o reducir el sentimiento.")

    # Professional recommendation
    if sentiment == 'POSITIVO':
        explanation_parts.append("💡 Recomendación: Refuerce estos aspectos positivos en su estrategia de comunicación.")
    elif sentiment == 'NEGATIVO':
        explanation_parts.append("💡 Recomendación: Identifique y aborde las causas de insatisfacción para mejorar la percepción.")
    else:
        explanation_parts.append("💡 Recomendación: Considere agregar elementos que generen mayor engagement emocional.")

    return " ".join(explanation_parts)

def analyze_text_fallback(text_input):
    """
    Legacy fallback method for backward compatibility.
    """
    result = analyze_text_fallback_detailed(text_input)
    # Return without explanation for backward compatibility
    return result[:5]