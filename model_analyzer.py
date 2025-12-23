from transformers import pipeline

# Load the sentiment analysis model for Spanish
model = pipeline("sentiment-analysis", model="finiteautomata/beto-sentiment-analysis")

def get_emotion_from_sentiment(sentimiento):
    """
    Get emotion based on sentiment.

    Args:
        sentimiento (str): The sentiment label.

    Returns:
        str: The corresponding emotion.
    """
    if sentimiento == 'Positivo':
        return 'Alegría'
    elif sentimiento == 'Negativo':
        return 'Enojo/Frustración'
    else:
        return 'Neutralidad'

def analyze_text(text_input):
    """
    Analyze the sentiment of the input text.

    Args:
        text_input (str): The text to analyze.

    Returns:
        tuple: (original_text, sentimiento, emocion, probabilidad)
    """
    # Basic preprocessing
    text = text_input.lower().strip()

    # Perform sentiment analysis
    result = model(text)[0]
    label = result['label']  # e.g., 'POS', 'NEG', 'NEU'
    score = result['score']

    # Map the label to sentiment
    if label == 'POS':
        sentimiento = 'Positivo'
    elif label == 'NEG':
        sentimiento = 'Negativo'
    else:
        sentimiento = 'Neutro'

    # Get emotion from sentiment
    emocion = get_emotion_from_sentiment(sentimiento)

    return text_input, sentimiento, emocion, score