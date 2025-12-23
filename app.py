import gradio as gr
import pandas as pd
import matplotlib.pyplot as plt
from db_manager import initialize_db, insert_analysis, fetch_all_results
from model_analyzer import analyze_text

# Initialize the database
initialize_db()

def create_sentiment_chart(df):
    """Create sentiment distribution pie chart."""
    fig, ax = plt.subplots()
    sentiment_counts = df['sentimiento'].value_counts()
    sentiment_counts.plot(kind='pie', autopct='%1.1f%%', ax=ax)
    ax.set_title('Distribución de Sentimientos')
    ax.set_ylabel('')
    return fig

def create_emotion_chart(df):
    """Create emotion frequency bar chart."""
    fig, ax = plt.subplots()
    emotion_counts = df['emocion'].value_counts()
    emotion_counts.plot(kind='bar', ax=ax)
    ax.set_title('Frecuencia de Emociones')
    ax.set_xlabel('Emoción')
    ax.set_ylabel('Frecuencia')
    return fig

def process_and_update_dashboard(text_input):
    """
    Process the input text, analyze each line, save to DB, and update dashboard.

    Args:
        text_input (str): Multi-line text input.

    Returns:
        tuple: (results_df, sentiment_plot, emotion_plot)
    """
    lines = [line.strip() for line in text_input.split('\n') if line.strip()]
    results = []
    for line in lines:
        comentario, sentimiento, emocion, prob = analyze_text(line)
        insert_analysis(comentario, sentimiento, emocion, prob)
        results.append({'Comentario': comentario, 'Sentimiento': sentimiento, 'Emoción': emocion, 'Probabilidad': prob})

    # Fetch all results for charts
    all_results = fetch_all_results()
    df = pd.DataFrame(all_results, columns=['comentario', 'sentimiento', 'emocion', 'probabilidad', 'fecha_analisis'])

    sentiment_chart = create_sentiment_chart(df)
    emotion_chart = create_emotion_chart(df)

    results_df = pd.DataFrame(results)
    return results_df, sentiment_chart, emotion_chart

# Create Gradio Blocks interface
with gr.Blocks() as demo:
    gr.Markdown("# Análisis de Sentimiento")

    with gr.Row():
        input_text = gr.Textbox(lines=5, label="Ingresa comentarios (uno por línea)")
        btn = gr.Button("Analizar")

    with gr.Row():
        results_table = gr.Dataframe(label="Resultados Inmediatos")

    with gr.Row():
        sentiment_plot = gr.Plot(label="Distribución de Sentimientos")
        emotion_plot = gr.Plot(label="Frecuencia de Emociones")

    btn.click(process_and_update_dashboard, inputs=input_text, outputs=[results_table, sentiment_plot, emotion_plot])

if __name__ == "__main__":
    demo.launch(inbrowser=True)