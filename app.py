import os
import logging
import subprocess
import platform
from typing import Optional
from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException, WebSocket, Query, WebSocketDisconnect
from typing import List
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
import plotly.express as px
import requests
from fpdf import FPDF
from db_manager import initialize_db, insert_analysis, fetch_all_results
from model_analyzer import analyze_text
from file_processor import process_file
from data_extractor import extract_text_from_url, validate_url, ExtractionError
import uvicorn
import json

# WebSocket connection manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # Remove broken connections
                self.active_connections.remove(connection)

# Global WebSocket manager
manager = ConnectionManager()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Sentiment Insights", description="Análisis profesional de sentimientos")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

def start_postgresql_service():
    """Attempt to start PostgreSQL service on macOS."""
    try:
        system = platform.system().lower()
        if system == "darwin":  # macOS
            # Try to start PostgreSQL using brew services
            logger.info("Attempting to start PostgreSQL service...")
            result = subprocess.run(
                ["brew", "services", "start", "postgresql"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                logger.info("PostgreSQL service started successfully.")
                # Wait a moment for the service to be ready
                import time
                time.sleep(3)
                return True
            else:
                logger.warning(f"Failed to start PostgreSQL service: {result.stderr}")
                return False
        else:
            logger.warning(f"PostgreSQL auto-start not supported on {system}")
            return False
    except subprocess.TimeoutExpired:
        logger.warning("PostgreSQL service start timed out")
        return False
    except FileNotFoundError:
        logger.warning("brew command not found. PostgreSQL must be started manually.")
        return False
    except Exception as e:
        logger.warning(f"Error starting PostgreSQL service: {e}")
        return False

def ensure_postgresql_running():
    """Ensure PostgreSQL is running before proceeding."""
    # First try to connect without starting service
    if initialize_db():
        logger.info("PostgreSQL is already running and accessible.")
        return True

    # If connection failed, try to start the service
    logger.info("PostgreSQL not accessible. Attempting to start service...")
    if start_postgresql_service():
        # Try to connect again after starting service
        if initialize_db():
            logger.info("PostgreSQL started and database initialized successfully.")
            return True

    logger.warning("Could not start PostgreSQL service or establish connection.")
    return False

# Initialize database with PostgreSQL startup check
db_initialized = ensure_postgresql_running()
if not db_initialized:
    logger.warning("Database not initialized. Running in demo mode.")

# Global for demo results with timestamp
last_results = None
last_status = None
last_pdf = None
last_analysis_time = None

# Global storage for recent analyses (real-time dashboard)
recent_analyses = []
MAX_RECENT_ANALYSES = 1000  # Keep last 1000 analyses for real-time charts

def convert_numpy_to_list(obj):
    """Recursively convert numpy arrays to lists for JSON serialization."""
    if hasattr(obj, 'tolist'):  # numpy array
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_to_list(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_list(item) for item in obj]
    else:
        return obj

def create_sentiment_chart(df: pd.DataFrame):
    """Crea un gráfico circular de distribución de sentimientos con Plotly."""
    logger.info(f"Creating sentiment chart with {len(df)} rows")
    if df.empty or len(df) < 1:
        logger.warning("DataFrame is empty or too small, cannot create sentiment chart")
        return None

    try:
        # Always try to create chart with available data for real-time feedback
        sentiment_counts = df['sentimiento'].value_counts().reset_index()
        sentiment_counts.columns = ['Sentimiento', 'Cantidad']
        logger.info(f"Sentiment counts: {sentiment_counts.to_dict()}")

        # Ensure we have at least some data to show
        if sentiment_counts.empty:
            logger.warning("No sentiment data available")
            return None

        fig = px.pie(sentiment_counts, values='Cantidad', names='Sentimiento',
                    title=f'Distribución de Sentimientos ({len(df)} análisis)')
        chart_data = convert_numpy_to_list(fig.to_dict())
        logger.info(f"Sentiment chart created successfully with {len(sentiment_counts)} categories")
        return chart_data
    except Exception as e:
        logger.error(f"Error creating sentiment chart: {str(e)}")
        return None

def create_emotion_chart(df: pd.DataFrame):
    """Crea un gráfico de barras de frecuencia de emociones con Plotly."""
    logger.info(f"Creating emotion chart with {len(df)} rows")
    if df.empty or len(df) < 1:
        logger.warning("DataFrame is empty or too small, cannot create emotion chart")
        return None

    try:
        emotion_counts = df['emocion'].value_counts().reset_index()
        emotion_counts.columns = ['Emoción', 'Frecuencia']
        logger.info(f"Emotion counts: {emotion_counts.to_dict()}")

        if emotion_counts.empty:
            logger.warning("No emotion data available")
            return None

        fig = px.bar(emotion_counts, x='Emoción', y='Frecuencia',
                    title=f'Frecuencia de Emociones ({len(df)} análisis)',
                    color='Emoción')
        chart_data = convert_numpy_to_list(fig.to_dict())
        logger.info(f"Emotion chart created successfully with {len(emotion_counts)} emotions")
        return chart_data
    except Exception as e:
        logger.error(f"Error creating emotion chart: {str(e)}")
        return None

def create_sentiment_heatmap(df: pd.DataFrame):
    """Crea un mapa de calor de sentimientos por tiempo."""
    logger.info(f"Creating heatmap with {len(df)} rows")
    if df.empty or len(df) < 2:  # Need at least 2 data points for meaningful heatmap
        logger.warning("DataFrame is empty or too small for heatmap")
        return None

    try:
        df_copy = df.copy()
        df_copy['fecha_analisis'] = pd.to_datetime(df_copy['fecha_analisis'])
        df_copy['hora'] = df_copy['fecha_analisis'].dt.hour
        df_copy['dia'] = df_copy['fecha_analisis'].dt.date

        heatmap_data = df_copy.pivot_table(
            index='hora',
            columns='sentimiento',
            values='confianza',
            aggfunc='mean'
        ).fillna(0)

        if heatmap_data.empty or heatmap_data.shape[0] < 1:
            logger.warning("No temporal data available for heatmap")
            return None

        # Convert hour index to string for JSON serialization
        heatmap_data.index = heatmap_data.index.astype(str)

        fig = px.imshow(
            heatmap_data,
            title=f'Mapa de Calor: Sentimientos por Hora ({len(df)} análisis)',
            labels=dict(x="Sentimiento", y="Hora", color="Confianza Promedio")
        )
        chart_data = convert_numpy_to_list(fig.to_dict())
        logger.info(f"Heatmap created successfully")
        return chart_data
    except Exception as e:
        logger.error(f"Error creating heatmap: {str(e)}")
        return None

def generate_pdf_report(df: pd.DataFrame) -> str:
    """Genera un reporte PDF detallado con los resultados del análisis usando UTF-8."""
    from datetime import datetime

    # Create reports directory if it doesn't exist
    os.makedirs("reports", exist_ok=True)

    pdf = FPDF()
    pdf.add_page()

    # Use UTF-8 compatible font (Arial Unicode MS or similar)
    try:
        pdf.set_font("Arial", size=16, style='B')
    except:
        # Fallback to default font
        pdf.set_font("Helvetica", size=16, style='B')

    # Sanitize title for PDF
    title = "Reporte de Análisis de Sentimiento".encode('latin-1', errors='replace').decode('latin-1')
    pdf.cell(200, 15, txt=title, ln=True, align='C')
    pdf.ln(5)

    # Add timestamp
    pdf.set_font("Arial", size=10)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pdf.cell(200, 8, txt=f"Generado el: {timestamp}", ln=True, align='R')
    pdf.ln(10)

    # Summary statistics
    if not df.empty:
        total_analyses = len(df)
        sentiment_counts = df['sentimiento'].value_counts()
        avg_intensity = df['intensidad'].mean()
        avg_confidence = df['confianza'].mean()

        pdf.set_font("Arial", size=12, style='B')
        summary_title = "Resumen Ejecutivo".encode('latin-1', errors='replace').decode('latin-1')
        pdf.cell(200, 10, txt=summary_title, ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 8, txt=f"Total de análisis realizados: {total_analyses}", ln=True)
        pdf.cell(200, 8, txt=f"Intensidad promedio: {avg_intensity:.2f}", ln=True)
        pdf.cell(200, 8, txt=f"Confianza promedio del modelo: {avg_confidence:.2f}", ln=True)
        pdf.ln(5)

        # Sentiment distribution
        pdf.set_font("Arial", size=12, style='B')
        dist_title = "Distribución de Sentimientos".encode('latin-1', errors='replace').decode('latin-1')
        pdf.cell(200, 10, txt=dist_title, ln=True)
        pdf.set_font("Arial", size=10)
        for sentiment, count in sentiment_counts.items():
            percentage = (count / total_analyses) * 100
            sentiment_text = str(sentiment).encode('latin-1', errors='replace').decode('latin-1')
            pdf.cell(200, 8, txt=f"{sentiment_text}: {count} análisis ({percentage:.1f}%)", ln=True)
        pdf.ln(10)

    # Detailed results
    pdf.set_font("Arial", size=12, style='B')
    details_title = "Resultados Detallados".encode('latin-1', errors='replace').decode('latin-1')
    pdf.cell(200, 10, txt=details_title, ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", size=9)
    for i, (_, row) in enumerate(df.iterrows(), 1):
        pdf.set_font("Arial", size=10, style='B')
        pdf.cell(200, 8, txt=f"Análisis #{i}", ln=True)
        pdf.set_font("Arial", size=9)

        # Handle long comments by wrapping text and sanitizing for PDF
        comment = str(row['comentario'])
        # Sanitize UTF-8 characters for PDF compatibility
        comment = comment.encode('latin-1', errors='replace').decode('latin-1')
        if len(comment) > 80:
            comment = comment[:77] + "..."

        pdf.cell(200, 6, txt=f"Texto: {comment}", ln=True)

        sentiment = str(row['sentimiento']).encode('latin-1', errors='replace').decode('latin-1')
        emocion = str(row['emocion']).encode('latin-1', errors='replace').decode('latin-1')
        pdf.cell(200, 6, txt=f"Sentimiento: {sentiment} | Emoción: {emocion}", ln=True)
        pdf.cell(200, 6, txt=f"Intensidad: {row['intensidad']:.2f} | Confianza: {row['confianza']:.2f}", ln=True)
        pdf.ln(3)

        # Add page break if needed
        if i % 15 == 0 and i < len(df):
            pdf.add_page()

    filename = f"reporte_analisis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join("reports", filename)
    pdf.output(filepath)
    return filename

@app.get("/")
async def landing(request: Request):
    """Página de presentación profesional."""
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/demo")
async def home(request: Request):
    """Página de demo interactiva."""
    from datetime import datetime, timedelta
    global last_results, last_status, last_pdf, last_analysis_time

    # Check if results are expired (older than 5 minutes)
    current_time = datetime.now()
    if last_analysis_time and (current_time - last_analysis_time) > timedelta(minutes=5):
        # Clear expired results
        last_results = None
        last_status = None
        last_pdf = None
        last_analysis_time = None

    status = last_status or ("Listo para analizar." if db_initialized else "⚠️ MODO LIMITADO: Conexión a PostgreSQL Fallida. La aplicación ha entrado en Modo Solo Análisis. Se puede analizar texto en tiempo real, pero el Dashboard Histórico no está disponible.")
    results = last_results
    pdf_file = last_pdf

    # Reset after displaying (one-time display)
    last_results = None
    last_status = None
    last_pdf = None
    last_analysis_time = None

    return templates.TemplateResponse("index.html", {
        "request": request,
        "status": status,
        "results": results,
        "pdf_file": pdf_file,
        "db_initialized": db_initialized
    })

@app.get("/dashboard")
async def dashboard(
    request: Request,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    sentiment_filter: Optional[str] = Query(None),
    emotion_filter: Optional[str] = Query(None),
    source_filter: Optional[str] = Query(None)
):
    """Dashboard con visualizaciones históricas y en tiempo real con filtros avanzados."""
    from datetime import datetime
    try:
        # Get historical data from database
        historical_tuples = fetch_all_results() or []
        logger.info(f"Dashboard: Retrieved {len(historical_tuples)} historical results from database")

        # Convert tuples to dictionaries for consistency
        column_names = ['comentario', 'sentimiento', 'emocion', 'intensidad', 'confianza', 'fecha_analisis']
        historical_results = []
        for row in historical_tuples:
            if len(row) == len(column_names):
                historical_results.append(dict(zip(column_names, row)))

        # Combine with recent analyses for real-time dashboard
        global recent_analyses
        all_analyses = historical_results + recent_analyses

        # Apply advanced filters
        logger.info(f"Filter params - start_date: {start_date}, end_date: {end_date}, sentiment: {sentiment_filter}, emotion: {emotion_filter}, source: {source_filter}")
        if start_date or end_date or sentiment_filter or emotion_filter or source_filter:
            filtered_analyses = []
            for analysis in all_analyses:
                # Date filtering
                if start_date:
                    analysis_date = pd.to_datetime(analysis['fecha_analisis']).date()
                    filter_start = pd.to_datetime(start_date).date()
                    if analysis_date < filter_start:
                        continue
                if end_date:
                    analysis_date = pd.to_datetime(analysis['fecha_analisis']).date()
                    filter_end = pd.to_datetime(end_date).date()
                    if analysis_date > filter_end:
                        continue

                # Sentiment filtering
                if sentiment_filter and sentiment_filter != 'all':
                    if analysis['sentimiento'] != sentiment_filter:
                        continue

                # Emotion filtering
                if emotion_filter and emotion_filter != 'all':
                    if analysis['emocion'] != emotion_filter:
                        continue

                # Source filtering (for future implementation - could be based on input type)
                if source_filter and source_filter != 'all':
                    # This would need additional metadata in the database
                    pass

                filtered_analyses.append(analysis)
            all_analyses = filtered_analyses
            logger.info(f"Applied filters - Original: {len(historical_results) + len(recent_analyses)}, Filtered: {len(all_analyses)}")

        logger.info(f"Dashboard: Total analyses (historical + recent): {len(all_analyses)}")

        if not all_analyses:
            logger.info("Dashboard: No analyses found, showing empty dashboard")
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "total_analyses": 0,
                "recent_analyses_count": 0,
                "sentiment_chart": None,
                "emotion_chart": None,
                "heatmap_chart": None,
                "current_time": datetime.now()
            })

        # Create DataFrame from all analyses (now all dictionaries)
        df = pd.DataFrame(all_analyses)
        logger.info(f"Dashboard: Created DataFrame with {len(df)} rows from combined data")
        logger.info(f"Dashboard: DataFrame columns: {list(df.columns)}")

        # Calculate KPIs with safe column access
        total_analyses = len(df)
        recent_count = len(recent_analyses)

        # Safe column access with fallbacks
        negative_intensity_avg = 0
        average_confidence = 0
        unique_emotions = 0

        if not df.empty:
            try:
                if 'sentimiento' in df.columns and 'intensidad' in df.columns:
                    negative_intensity_avg = df[df['sentimiento'] == 'NEGATIVO']['intensidad'].mean() if len(df[df['sentimiento'] == 'NEGATIVO']) > 0 else 0
                if 'confianza' in df.columns:
                    average_confidence = df['confianza'].mean()
                if 'emocion' in df.columns:
                    unique_emotions = df['emocion'].nunique()
            except Exception as e:
                logger.warning(f"Error calculating KPIs: {e}")
                # Continue with defaults

        logger.info(f"Dashboard: KPIs calculated - Total: {total_analyses}, Recent: {recent_count}, Confidence: {average_confidence:.3f}")

        # Generate charts from filtered data
        filtered_df = pd.DataFrame(all_analyses)
        sentiment_chart = create_sentiment_chart(filtered_df)
        emotion_chart = create_emotion_chart(filtered_df)
        heatmap_chart = create_sentiment_heatmap(filtered_df)

        logger.info(f"Dashboard: Charts generated - Sentiment: {sentiment_chart is not None}, Emotion: {emotion_chart is not None}, Heatmap: {heatmap_chart is not None}")

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "total_analyses": total_analyses,
            "recent_analyses_count": recent_count,
            "negative_intensity_avg": negative_intensity_avg,
            "average_confidence": average_confidence,
            "unique_emotions": unique_emotions,
            "sentiment_chart": sentiment_chart,
            "emotion_chart": emotion_chart,
            "heatmap_chart": heatmap_chart,
            "current_time": datetime.now()
        })

    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}", exc_info=True)
        # Return a safe fallback dashboard
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "total_analyses": 0,
            "recent_analyses_count": 0,
            "sentiment_chart": None,
            "emotion_chart": None,
            "heatmap_chart": None
        })

@app.post("/analyze")
async def analyze(
    request: Request,
    text_input: Optional[str] = Form(None),
    file_input: Optional[UploadFile] = File(None),
    url_input: Optional[str] = Form(None)
):
    """Endpoint para analizar texto - funcionalidad más básica y robusta."""
    logger.info(f"Analyze request received - text: {bool(text_input)}, file: {bool(file_input)}, url: {bool(url_input)}")

    try:
        lines = []

        # T1: TEXT ANALYSIS - Most basic and robust functionality
        if text_input and text_input.strip():
            logger.info("Processing direct text input")
            # P3: Ensure text input is treated as UTF-8
            text_input = text_input.encode('utf-8', errors='replace').decode('utf-8')
            # Process direct text input - NO validation blocking
            lines = [line.strip() for line in text_input.split('\n') if line.strip()]
            logger.info(f"Extracted {len(lines)} lines from text input")

        # T2: URL PROCESSING - Direct to web scraping
        elif url_input and url_input.strip():
            logger.info(f"Processing URL input: {url_input}")
            # Basic URL validation only
            if not url_input.startswith(('http://', 'https://')):
                url_input = 'https://' + url_input

            try:
                lines = extract_text_from_url(url_input)
                logger.info(f"Extracted {len(lines)} lines from URL")
            except ExtractionError as e:
                logger.warning(f"URL extraction error: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Fallo en la extracción: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected URL processing error: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Error procesando URL: {str(e)}")

        # T3: FILE PROCESSING - Allow enterprise file formats
        elif file_input:
            logger.info(f"Processing file input: {file_input.filename}")
            # Sanitize filename to handle encoding issues
            filename = file_input.filename
            if filename:
                filename = filename.encode('utf-8', errors='replace').decode('utf-8')
            content_type = file_input.content_type or ""

            # P3: Support all enterprise file formats - no rejection, attempt processing
            supported_extensions = {'.pdf', '.docx', '.xlsx', '.pptx', '.txt', '.csv', '.jpg', '.jpeg', '.png', '.bmp', '.tiff'}

            # Extract file extension
            if not filename or '.' not in filename:
                logger.warning("File without extension - attempting text processing")
                file_extension = '.txt'  # Default to text processing
            else:
                file_extension = '.' + filename.lower().split('.')[-1]

            logger.info(f"Processing file with extension: {file_extension}")

            # P3: Attempt processing for all supported formats, let processing logic handle errors
            if file_extension not in supported_extensions:
                logger.info(f"Unsupported extension {file_extension} - attempting as text file")
                file_extension = '.txt'  # Fallback to text processing

            file_content = await file_input.read()
            try:
                # Use the new process_file function that handles all enterprise formats
                text_content = process_file(file_content, filename)
                lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                logger.info(f"Extracted {len(lines)} lines from file")
            except Exception as e:
                logger.error(f"File processing error: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Error procesando archivo: {str(e)}")

        else:
            logger.warning("No valid input provided")
            raise HTTPException(status_code=400, detail="Debe proporcionar texto, un archivo o una URL para analizar")

        if not lines:
            logger.warning("No valid lines found to analyze")
            raise HTTPException(status_code=400, detail="No se encontraron líneas válidas para analizar.")

        logger.info(f"Starting analysis of {len(lines)} lines")

        results = []
        total_lines = len(lines)

        # Send initial progress
        await manager.broadcast({
            "type": "analysis_progress",
            "data": {
                "current": 0,
                "total": total_lines,
                "percentage": 0,
                "status": "Iniciando análisis..."
            }
        })

        for i, line in enumerate(lines):
            try:
                # Send progress update
                progress = int((i / total_lines) * 100)
                await manager.broadcast({
                    "type": "analysis_progress",
                    "data": {
                        "current": i + 1,
                        "total": total_lines,
                        "percentage": progress,
                        "status": f"Analizando línea {i + 1} de {total_lines}..."
                    }
                })

                # Sanitize line before analysis
                line = line.encode('utf-8', errors='replace').decode('utf-8')
                comentario, sentimiento, emocion, intensidad, confianza = analyze_text(line)
                success = insert_analysis(comentario, sentimiento, emocion, intensidad, confianza)
                results.append({
                    'comentario': comentario,
                    'sentimiento': sentimiento,
                    'emocion': emocion,
                    'intensidad': intensidad,
                    'confianza': confianza
                })
            except Exception as e:
                # Log sanitized error and continue
                error_msg = str(e)
                if len(error_msg) > 100:
                    error_msg = error_msg[:100] + "..."
                error_msg = error_msg.encode('utf-8', errors='replace').decode('utf-8')
                logger.warning(f"Skipping line {i} due to error: {error_msg}")
                # Continue with other lines instead of failing completely
                continue

        # Send completion progress
        await manager.broadcast({
            "type": "analysis_progress",
            "data": {
                "current": total_lines,
                "total": total_lines,
                "percentage": 100,
                "status": "Análisis completado"
            }
        })

        if not results:
            raise HTTPException(status_code=500, detail="No se pudieron analizar las líneas proporcionadas")

        logger.info(f"Analysis completed successfully with {len(results)} results")

        # Store results in recent analyses for real-time dashboard
        global recent_analyses
        from datetime import datetime
        current_time = datetime.now()

        for result in results:
            analysis_record = {
                'comentario': result['comentario'],
                'sentimiento': result['sentimiento'],
                'emocion': result['emocion'],
                'intensidad': result['intensidad'],
                'confianza': result['confianza'],
                'fecha_analisis': current_time
            }
            recent_analyses.append(analysis_record)

        # Keep only the most recent analyses
        if len(recent_analyses) > MAX_RECENT_ANALYSES:
            recent_analyses = recent_analyses[-MAX_RECENT_ANALYSES:]

        logger.info(f"Stored {len(results)} analyses in recent_analyses (total: {len(recent_analyses)})")

        # Generate PDF with error handling
        try:
            df_results = pd.DataFrame(results)
            pdf_file = generate_pdf_report(df_results)
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            pdf_file = None

        # Set globals for demo with timestamp
        global last_results, last_status, last_pdf, last_analysis_time
        last_status = "Análisis completado exitosamente."
        last_results = results
        last_pdf = pdf_file
        last_analysis_time = current_time

        # Broadcast real-time update to all dashboard connections
        await manager.broadcast({
            "type": "batch_analysis_complete",
            "data": {
                "count": len(results),
                "timestamp": current_time.isoformat(),
                "has_pdf": pdf_file is not None
            }
        })

        return {"status": "Análisis completado exitosamente."}

    except HTTPException:
        # Re-raise HTTPExceptions (they're already properly formatted)
        raise
    except Exception as e:
        # Sanitize error message to avoid encoding issues in logging and HTTP response
        error_str = str(e)
        if len(error_str) > 200:
            error_str = error_str[:200] + "..."
        error_str = error_str.encode('utf-8', errors='replace').decode('utf-8')
        logger.error(f"Unexpected error in analyze endpoint: {error_str}", exc_info=True)
        # Use a safe error message for HTTP response
        error_detail = "Error interno del servidor. Por favor, inténtelo de nuevo más tarde."
        raise HTTPException(status_code=500, detail=error_detail)

@app.post("/api/analyze")
async def api_analyze(
    text: str = Form(...),
    api_key: Optional[str] = Form(None)
):
    """API endpoint for external integrations."""
    # Simple API key check (in production, use proper auth)
    if api_key != "sentiment-api-key":
        raise HTTPException(status_code=401, detail="API key inválida")

    try:
        comentario, sentimiento, emocion, intensidad, confianza = analyze_text(text.strip())
        return {
            "text": comentario,
            "sentiment": sentimiento,
            "emotion": emocion,
            "intensity": intensidad,
            "confidence": confianza
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en análisis: {str(e)}")

@app.get("/api/stats")
async def api_stats(api_key: Optional[str] = None):
    """API endpoint to get statistics."""
    if api_key != "sentiment-api-key":
        raise HTTPException(status_code=401, detail="API key inválida")

    all_results = fetch_all_results()
    if not all_results:
        return {"total_analyses": 0, "sentiment_distribution": {}}

    df = pd.DataFrame(all_results, columns=['comentario', 'sentimiento', 'emocion', 'intensidad', 'confianza', 'fecha_analisis'])
    sentiment_counts = df['sentimiento'].value_counts().to_dict()

    return {
        "total_analyses": len(df),
        "sentiment_distribution": sentiment_counts,
        "average_confidence": df['confianza'].mean()
    }

@app.get("/api/charts/sentiment")
async def api_sentiment_chart():
    """API endpoint to get sentiment chart data."""
    all_results = fetch_all_results()
    if not all_results:
        return {"data": [], "layout": {}}

    df = pd.DataFrame(all_results, columns=['comentario', 'sentimiento', 'emocion', 'intensidad', 'confianza', 'fecha_analisis'])
    chart = create_sentiment_chart(df)
    return chart if chart else {"data": [], "layout": {}}

@app.get("/api/charts/emotion")
async def api_emotion_chart():
    """API endpoint to get emotion chart data."""
    all_results = fetch_all_results()
    if not all_results:
        return {"data": [], "layout": {}}

    df = pd.DataFrame(all_results, columns=['comentario', 'sentimiento', 'emocion', 'intensidad', 'confianza', 'fecha_analisis'])
    chart = create_emotion_chart(df)
    return chart if chart else {"data": [], "layout": {}}

@app.get("/api/charts/heatmap")
async def api_heatmap_chart():
    """API endpoint to get heatmap chart data."""
    all_results = fetch_all_results()
    if not all_results:
        return {"data": [], "layout": {}}

    df = pd.DataFrame(all_results, columns=['comentario', 'sentimiento', 'emocion', 'intensidad', 'confianza', 'fecha_analisis'])
    chart = create_sentiment_heatmap(df)
    return chart if chart else {"data": [], "layout": {}}

@app.post("/clear_results")
async def clear_results():
    """Clear the current analysis results."""
    global last_results, last_status, last_pdf, last_analysis_time
    last_results = None
    last_status = None
    last_pdf = None
    last_analysis_time = None
    return {"status": "Resultados limpiados exitosamente"}

@app.get("/download/{filename}")
async def download_pdf(filename: str):
    """Descargar archivo PDF."""
    # Check both current directory and reports directory
    possible_paths = [
        os.path.join(os.getcwd(), filename),
        os.path.join(os.getcwd(), "reports", filename)
    ]

    for file_path in possible_paths:
        if os.path.exists(file_path):
            return FileResponse(
                file_path,
                media_type='application/pdf',
                filename=filename,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

    raise HTTPException(status_code=404, detail="Archivo no encontrado")

@app.websocket("/ws/analyze")
async def websocket_analyze(websocket: WebSocket):
    """WebSocket endpoint for real-time analysis."""
    from datetime import datetime
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            text_input = data.get('text', '')
            if text_input.strip():
                await websocket.send_json({"status": "Procesando..."})
                comentario, sentimiento, emocion, intensidad, confianza = analyze_text(text_input.strip())
                success = insert_analysis(comentario, sentimiento, emocion, intensidad, confianza)
                result = {
                    "comentario": comentario,
                    "sentimiento": sentimiento,
                    "emocion": emocion,
                    "intensidad": intensidad,
                    "confianza": confianza,
                    "success": success
                }
                await websocket.send_json({"result": result})

                # Broadcast update to all dashboard connections
                await manager.broadcast({
                    "type": "analysis_complete",
                    "data": result,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                await websocket.send_json({"error": "Texto vacío"})
    except Exception as e:
        await websocket.send_json({"error": str(e)})

@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and wait for client messages
            data = await websocket.receive_json()
            # Handle any client messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent error format."""
    # Sanitize detail to avoid encoding issues
    detail = exc.detail
    if isinstance(detail, str):
        detail = detail.encode('utf-8', errors='replace').decode('utf-8')
        if len(detail) > 500:  # Truncate very long messages
            detail = detail[:500] + "..."

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": detail, "type": "http_error"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with logging."""
    # Sanitize error message to avoid encoding issues
    error_msg = str(exc)
    if len(error_msg) > 200:  # Truncate very long error messages
        error_msg = error_msg[:200] + "..."

    # Log the original error for debugging
    logger.error(f"Unexpected error: {error_msg}", exc_info=True)

    # Return a safe, properly encoded error message
    safe_error_msg = "Error interno del servidor. Por favor, inténtelo de nuevo más tarde."
    return JSONResponse(
        status_code=500,
        content={
            "detail": safe_error_msg,
            "type": "server_error"
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)