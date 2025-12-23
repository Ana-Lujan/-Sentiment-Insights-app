import gradio as gr
import pandas as pd
import tempfile
import os

# Try to import the analysis modules
try:
    from model_analyzer import analyze_text
    from file_processor import process_file
    from data_extractor import extract_text_from_url, ExtractionError
    MODEL_LOADED = True
except Exception as e:
    MODEL_LOADED = False
    ERROR_MSG = f"Error cargando el modelo: {str(e)}"

def analyze_sentiment(text):
    """Analyze sentiment of input text."""
    if not MODEL_LOADED:
        return ERROR_MSG, "", 0.0, 0.0

    if not text or not text.strip():
        return "Por favor, ingresa un texto para analizar.", "", 0.0, 0.0

    try:
        comentario, sentimiento, emocion, intensidad, confianza = analyze_text(text.strip())
        result = f"**Sentimiento:** {sentimiento}\n\n**Emoción:** {emocion}\n\n**Comentario:** {comentario}"
        return result, sentimiento, intensidad, confianza
    except Exception as e:
        return f"Error en el análisis: {str(e)}", "", 0.0, 0.0

def analyze_file(file):
    """Analyze sentiment from uploaded file."""
    if not MODEL_LOADED:
        return ERROR_MSG, pd.DataFrame()

    if file is None:
        return "Por favor, sube un archivo para analizar.", pd.DataFrame()

    try:
        # Read file content
        with open(file.name, 'rb') as f:
            content = f.read()

        # Process file
        text_content = process_file(content, file.name)
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]

        if not lines:
            return "No se pudo extraer texto del archivo.", pd.DataFrame()

        # Analyze each line
        results = []
        for line in lines[:50]:  # Limit to 50 lines for demo
            try:
                comentario, sentimiento, emocion, intensidad, confianza = analyze_text(line)
                results.append({
                    'Texto': comentario[:100] + '...' if len(comentario) > 100 else comentario,
                    'Sentimiento': sentimiento,
                    'Emoción': emocion,
                    'Intensidad': round(intensidad, 2),
                    'Confianza': round(confianza, 2)
                })
            except:
                continue

        if not results:
            return "No se pudieron analizar las líneas del archivo.", pd.DataFrame()

        df = pd.DataFrame(results)
        summary = f"Análisis completado. {len(results)} líneas analizadas."

        return summary, df

    except Exception as e:
        return f"Error procesando archivo: {str(e)}", pd.DataFrame()

def analyze_url(url):
    """Analyze sentiment from URL."""
    if not MODEL_LOADED:
        return ERROR_MSG, pd.DataFrame()

    if not url or not url.strip():
        return "Por favor, ingresa una URL válida.", pd.DataFrame()

    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        lines = extract_text_from_url(url)

        if not lines:
            return "No se pudo extraer texto de la URL.", pd.DataFrame()

        # Analyze first 50 lines
        results = []
        for line in lines[:50]:
            try:
                comentario, sentimiento, emocion, intensidad, confianza = analyze_text(line)
                results.append({
                    'Texto': comentario[:100] + '...' if len(comentario) > 100 else comentario,
                    'Sentimiento': sentimiento,
                    'Emoción': emocion,
                    'Intensidad': round(intensidad, 2),
                    'Confianza': round(confianza, 2)
                })
            except:
                continue

        if not results:
            return "No se pudieron analizar las líneas de la URL.", pd.DataFrame()

        df = pd.DataFrame(results)
        summary = f"Análisis completado. {len(results)} líneas analizadas de {len(lines)} extraídas."

        return summary, df

    except ExtractionError as e:
        return f"Error extrayendo de URL: {str(e)}", pd.DataFrame()
    except Exception as e:
        return f"Error procesando URL: {str(e)}", pd.DataFrame()

# Create Gradio interface
with gr.Blocks(title="Sentiment Insights - Análisis de Sentimientos", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎯 Sentiment Insights")
    gr.Markdown("Análisis inteligente de sentimientos y emociones en español")

    with gr.Tab("Análisis de Texto"):
        text_input = gr.Textbox(
            label="Ingresa tu texto aquí",
            placeholder="Escribe o pega el texto que quieres analizar...",
            lines=5
        )
        analyze_btn = gr.Button("Analizar Sentimiento", variant="primary")
        result_output = gr.Textbox(label="Resultado del Análisis", interactive=False)
        with gr.Row():
            sentiment_output = gr.Textbox(label="Sentimiento", interactive=False)
            intensity_output = gr.Number(label="Intensidad", interactive=False)
            confidence_output = gr.Number(label="Confianza", interactive=False)

        analyze_btn.click(
            analyze_sentiment,
            inputs=text_input,
            outputs=[result_output, sentiment_output, intensity_output, confidence_output]
        )

    with gr.Tab("Análisis de Archivo"):
        file_input = gr.File(label="Sube un archivo (PDF, Word, Excel, imagen, etc.)")
        analyze_file_btn = gr.Button("Analizar Archivo", variant="primary")
        file_result_output = gr.Textbox(label="Resultado", interactive=False)
        file_table_output = gr.Dataframe(label="Resultados Detallados")

        analyze_file_btn.click(
            analyze_file,
            inputs=file_input,
            outputs=[file_result_output, file_table_output]
        )

    with gr.Tab("Análisis de URL"):
        url_input = gr.Textbox(
            label="Ingresa la URL del sitio web",
            placeholder="https://ejemplo.com"
        )
        analyze_url_btn = gr.Button("Analizar URL", variant="primary")
        url_result_output = gr.Textbox(label="Resultado", interactive=False)
        url_table_output = gr.Dataframe(label="Resultados Detallados")

        analyze_url_btn.click(
            analyze_url,
            inputs=url_input,
            outputs=[url_result_output, url_table_output]
        )

    gr.Markdown("""
    ---
    **💡 Acerca de Sentiment Insights**
    - Utiliza inteligencia artificial avanzada para detectar sentimientos y emociones
    - Soporta múltiples formatos: texto, archivos y URLs
    - Especializado en el idioma español
    - Análisis en tiempo real con alta precisión
    """)

if __name__ == "__main__":
    demo.launch()