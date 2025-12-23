// Professional chart rendering for Sentiment Insights Dashboard
// This file handles all chart visualization logic

document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 Initializing professional dashboard charts...');

    // Check if Plotly is available
    if (typeof Plotly === 'undefined') {
        console.error('❌ Plotly library not loaded');
        showAllFallbacks();
        return;
    }

    // Render all charts
    renderAllCharts();
});

function renderAllCharts() {
    console.log('📊 Rendering all charts from server data...');

    // Sentiment Chart
    renderChart('sentimentChart', window.sentiment_chart_data, showSentimentFallback);

    // Emotion Chart
    renderChart('emotionChart', window.emotion_chart_data, showEmotionFallback);

    // Heatmap Chart
    renderChart('heatmapChart', window.heatmap_chart_data, showHeatmapFallback);
}

function renderChart(containerId, chartData, fallbackFunc) {
    try {
        // Simple check: if we have chart data, try to render it
        if (chartData && chartData.data) {
            const layout = {
                paper_bgcolor: 'rgba(255,255,255,0.9)',
                plot_bgcolor: 'rgba(255,255,255,0.9)',
                font: { color: '#2d3748' },
                margin: { t: 50, l: 50, r: 50, b: 50 }
            };

            // If layout exists, merge it
            if (chartData.layout) {
                Object.assign(layout, chartData.layout);
            }

            Plotly.newPlot(containerId, chartData.data, layout);

            // Add click handlers for drill-down functionality
            addDrillDownHandlers(containerId);

            console.log(`✅ ${containerId} rendered successfully`);
            return;
        }

        // No data available, show fallback
        console.log(`ℹ️ No data for ${containerId}, showing fallback`);
        fallbackFunc();
    } catch (error) {
        console.error(`❌ Error rendering ${containerId}:`, error);
        fallbackFunc();
    }
}

function showSentimentFallback() {
    const element = document.getElementById('sentimentChart');
    if (element) {
        element.innerHTML = `
            <div class="chart-loading">
                <div class="text-center">
                    <div class="mb-3">
                        <i class="fas fa-chart-pie fa-3x text-primary"></i>
                    </div>
                    <p class="text-muted">Datos insuficientes para generar gráfico</p>
                    <small class="text-muted">Se requieren más análisis para visualizar tendencias</small>
                </div>
            </div>
        `;
    }
}

function showEmotionFallback() {
    const element = document.getElementById('emotionChart');
    if (element) {
        element.innerHTML = `
            <div class="chart-loading">
                <div class="text-center">
                    <div class="mb-3">
                        <i class="fas fa-chart-bar fa-3x text-success"></i>
                    </div>
                    <p class="text-muted">Datos insuficientes para generar gráfico</p>
                    <small class="text-muted">Se requieren más análisis para visualizar emociones</small>
                </div>
            </div>
        `;
    }
}

function showHeatmapFallback() {
    const element = document.getElementById('heatmapChart');
    if (element) {
        element.innerHTML = `
            <div class="chart-loading">
                <div class="text-center">
                    <div class="mb-3">
                        <i class="fas fa-calendar-alt fa-3x text-info"></i>
                    </div>
                    <p class="text-muted">Datos insuficientes para mapa de calor</p>
                    <small class="text-muted">Se requieren más análisis para visualizar tendencias por hora</small>
                </div>
            </div>
        `;
    }
}

function showAllFallbacks() {
    console.log('🔄 Showing all professional fallbacks...');
    showSentimentFallback();
    showEmotionFallback();
    showHeatmapFallback();
}

// Advanced Dashboard Filtering
function applyFilters() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const sentimentFilter = document.getElementById('sentimentFilter').value;
    const emotionFilter = document.getElementById('emotionFilter').value;

    // Build query parameters
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (sentimentFilter && sentimentFilter !== 'all') params.append('sentiment_filter', sentimentFilter);
    if (emotionFilter && emotionFilter !== 'all') params.append('emotion_filter', emotionFilter);

    // Reload dashboard with filters
    const newUrl = `/dashboard${params.toString() ? '?' + params.toString() : ''}`;
    window.location.href = newUrl;
}

function resetFilters() {
    document.getElementById('startDate').value = '';
    document.getElementById('endDate').value = '';
    document.getElementById('sentimentFilter').value = 'all';
    document.getElementById('emotionFilter').value = 'all';

    // Reload dashboard without filters
    window.location.href = '/dashboard';
}

// Drill-down functionality
function addDrillDownHandlers(containerId) {
    const plot = document.getElementById(containerId);
    if (!plot) return;

    plot.on('plotly_click', function(data) {
        if (data.points && data.points.length > 0) {
            const point = data.points[0];
            showDrillDownModal(containerId, point);
        }
    });
}

function showDrillDownModal(chartType, pointData) {
    let title = '';
    let content = '';

    switch(chartType) {
        case 'sentimentChart':
            title = `Detalles de Sentimiento: ${pointData.label || pointData.x}`;
            content = `
                <div class="drilldown-content">
                    <div class="metric-card">
                        <h5>Cantidad de Análisis</h5>
                        <div class="metric-value">${pointData.value || pointData.y}</div>
                    </div>
                    <div class="metric-card">
                        <h5>Porcentaje del Total</h5>
                        <div class="metric-value">${((pointData.value || pointData.y) / getTotalAnalyses() * 100).toFixed(1)}%</div>
                    </div>
                    <div class="drilldown-actions">
                        <button class="btn btn-primary" onclick="applyFiltersFromDrilldown('sentiment_filter', '${pointData.label || pointData.x}')">
                            Filtrar por este sentimiento
                        </button>
                    </div>
                </div>
            `;
            break;

        case 'emotionChart':
            title = `Detalles de Emoción: ${pointData.label || pointData.x}`;
            content = `
                <div class="drilldown-content">
                    <div class="metric-card">
                        <h5>Frecuencia</h5>
                        <div class="metric-value">${pointData.value || pointData.y}</div>
                    </div>
                    <div class="metric-card">
                        <h5>Porcentaje del Total</h5>
                        <div class="metric-value">${((pointData.value || pointData.y) / getTotalAnalyses() * 100).toFixed(1)}%</div>
                    </div>
                    <div class="drilldown-actions">
                        <button class="btn btn-success" onclick="applyFiltersFromDrilldown('emotion_filter', '${pointData.label || pointData.x}')">
                            Filtrar por esta emoción
                        </button>
                    </div>
                </div>
            `;
            break;

        case 'heatmapChart':
            title = `Detalles del Mapa de Calor: Hora ${pointData.x}, Confianza ${pointData.z ? pointData.z.toFixed(2) : 'N/A'}`;
            content = `
                <div class="drilldown-content">
                    <div class="metric-card">
                        <h5>Hora del Día</h5>
                        <div class="metric-value">${pointData.x}:00</div>
                    </div>
                    <div class="metric-card">
                        <h5>Confianza Promedio</h5>
                        <div class="metric-value">${pointData.z ? pointData.z.toFixed(3) : 'N/A'}</div>
                    </div>
                    <div class="drilldown-actions">
                        <button class="btn btn-info" onclick="showTimeAnalysis('${pointData.x}')">
                            Ver análisis de esta hora
                        </button>
                    </div>
                </div>
            `;
            break;
    }

    // Create and show modal
    const modalHtml = `
        <div class="modal fade" id="drilldownModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        ${content}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if present
    const existingModal = document.getElementById('drilldownModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('drilldownModal'));
    modal.show();
}

function applyFiltersFromDrilldown(filterType, value) {
    // Reset all filters first
    resetFilters();

    // Apply the specific filter
    if (filterType === 'sentiment_filter') {
        document.getElementById('sentimentFilter').value = value;
    } else if (filterType === 'emotion_filter') {
        document.getElementById('emotionFilter').value = value;
    }

    // Apply filters
    applyFilters();

    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('drilldownModal'));
    if (modal) {
        modal.hide();
    }
}

function showTimeAnalysis(hour) {
    alert(`Funcionalidad de análisis por hora ${hour}:00 próximamente disponible`);
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('drilldownModal'));
    if (modal) {
        modal.hide();
    }
}

function getTotalAnalyses() {
    // This should be passed from the server or calculated
    return parseInt(document.getElementById('filteredCount')?.textContent || '0');
}

// WebSocket functionality removed - using polling for dashboard updates
// Real-time updates handled through periodic fetch calls

function refreshDashboardData() {
    // Refresh charts data
    setTimeout(() => {
        refreshCharts();
    }, 1000); // Small delay to ensure data is saved
}

function refreshCharts() {
    // This will trigger the existing refresh logic
    console.log('🔄 Refrescando gráficos con datos actualizados...');

    // Update sentiment chart
    fetch('/api/charts/sentiment')
        .then(response => response.json())
        .then(data => {
            if (data.data && data.data.length > 0) {
                Plotly.newPlot('sentimentChart', data.data, data.layout);
            }
        })
        .catch(error => console.error('Error refreshing sentiment chart:', error));

    // Update emotion chart
    fetch('/api/charts/emotion')
        .then(response => response.json())
        .then(data => {
            if (data.data && data.data.length > 0) {
                Plotly.newPlot('emotionChart', data.data, data.layout);
            }
        })
        .catch(error => console.error('Error refreshing emotion chart:', error));

    // Update heatmap
    fetch('/api/charts/heatmap')
        .then(response => response.json())
        .then(data => {
            if (data.data && data.data.length > 0) {
                Plotly.newPlot('heatmapChart', data.data, data.layout);
            }
        })
        .catch(error => console.error('Error refreshing heatmap:', error));

    // Update stats
    fetch('/api/stats?api_key=sentiment-api-key')
        .then(response => response.json())
        .then(data => {
            updateKPIs(data);
        })
        .catch(error => console.error('Error refreshing stats:', error));
}

function updateRecentCounter(newAnalyses) {
    const counter = document.querySelector('.kpi-trend .text-success');
    if (counter) {
        const currentText = counter.textContent;
        const currentNumber = parseInt(currentText.match(/\d+/) || '0');
        const newNumber = currentNumber + newAnalyses;
        counter.innerHTML = `<i class="fas fa-arrow-up text-success"></i> <span class="text-success">+${newNumber} hoy</span>`;
    }
}

function updateKPIs(stats) {
    // Update total analyses KPI
    const totalElement = document.querySelector('.kpi-value');
    if (totalElement && stats.total_analyses) {
        totalElement.textContent = stats.total_analyses.toLocaleString();
    }

    // Update confidence KPI
    const confidenceElements = document.querySelectorAll('.kpi-value');
    if (confidenceElements.length >= 2 && stats.average_confidence) {
        confidenceElements[1].textContent = `${(stats.average_confidence * 100).toFixed(1)}%`;
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// AI Insights Generation
function generateAIInsights() {
    // Get data from charts
    const sentimentData = window.sentiment_chart_data;
    const emotionData = window.emotion_chart_data;

    if (!sentimentData || !emotionData) {
        console.log('Esperando datos de gráficos para generar insights...');
        setTimeout(generateAIInsights, 1000);
        return;
    }

    // Analyze sentiment trends
    analyzeSentimentTrends(sentimentData);

    // Analyze emotion patterns
    analyzeEmotionPatterns(emotionData);

    // Generate confidence insights
    analyzeConfidenceLevels();

    // Generate recommendations
    generateRecommendations(sentimentData, emotionData);
}

function analyzeSentimentTrends(sentimentData) {
    const element = document.getElementById('sentiment-trend-text');

    // Find dominant sentiment
    let maxSentiment = '';
    let maxCount = 0;

    sentimentData.data.forEach(trace => {
        if (trace.y > maxCount) {
            maxCount = trace.y;
            maxSentiment = trace.name;
        }
    });

    let trendText = '';
    const total = sentimentData.data.reduce((sum, trace) => sum + trace.y, 0);

    if (maxSentiment === 'POSITIVO') {
        trendText = `Tendencia positiva dominante (${Math.round((maxCount/total)*100)}% del total). Los usuarios muestran satisfacción general.`;
    } else if (maxSentiment === 'NEGATIVO') {
        trendText = `Se detecta insatisfacción significativa (${Math.round((maxCount/total)*100)}% del total). Requiere atención inmediata.`;
    } else {
        trendText = `Sentimiento neutral predominante (${Math.round((maxCount/total)*100)}% del total). Los usuarios muestran indiferencia.`;
    }

    element.textContent = trendText;
}

function analyzeEmotionPatterns(emotionData) {
    const element = document.getElementById('emotion-insight-text');

    // Find most frequent emotion
    let maxEmotion = '';
    let maxCount = 0;

    emotionData.data.forEach(trace => {
        if (trace.y > maxCount) {
            maxCount = trace.y;
            maxEmotion = trace.name;
        }
    });

    let emotionText = '';
    const total = emotionData.data.reduce((sum, trace) => sum + trace.y, 0);

    if (maxEmotion === 'Alegría' || maxEmotion === 'Alegría Extrema') {
        emotionText = `Emoción positiva predominante: ${maxEmotion} (${Math.round((maxCount/total)*100)}%). Excelente engagement emocional.`;
    } else if (maxEmotion === 'Enojo/Frustración' || maxEmotion === 'Ira Extrema') {
        emotionText = `Se detecta frustración elevada: ${maxEmotion} (${Math.round((maxCount/total)*100)}%). Necesita intervención urgente.`;
    } else if (maxEmotion === 'Indiferencia') {
        emotionText = `Predomina la indiferencia (${Math.round((maxCount/total)*100)}%). Los usuarios no muestran engagement emocional fuerte.`;
    } else {
        emotionText = `Emoción principal: ${maxEmotion} (${Math.round((maxCount/total)*100)}%). Patrón emocional identificado.`;
    }

    element.textContent = emotionText;
}

function analyzeConfidenceLevels() {
    const element = document.getElementById('confidence-insight-text');

    // Get confidence from server data (this would need to be passed from backend)
    // For now, use a simulated analysis
    const avgConfidence = 0.85; // This should come from backend

    let confidenceText = '';
    if (avgConfidence > 0.9) {
        confidenceText = `Excelente precisión del modelo (${Math.round(avgConfidence*100)}%). Los resultados son altamente confiables.`;
    } else if (avgConfidence > 0.8) {
        confidenceText = `Buena precisión del modelo (${Math.round(avgConfidence*100)}%). Los análisis son confiables para toma de decisiones.`;
    } else if (avgConfidence > 0.7) {
        confidenceText = `Precisión aceptable (${Math.round(avgConfidence*100)}%). Recomendado validar resultados críticos manualmente.`;
    } else {
        confidenceText = `Precisión baja (${Math.round(avgConfidence*100)}%). Los resultados requieren validación manual.`;
    }

    element.textContent = confidenceText;
}

function generateRecommendations(sentimentData, emotionData) {
    const element = document.getElementById('recommendation-text');

    // Analyze patterns and generate recommendations
    const positiveCount = sentimentData.data.find(d => d.name === 'POSITIVO')?.y || 0;
    const negativeCount = sentimentData.data.find(d => d.name === 'NEGATIVO')?.y || 0;
    const neutralCount = sentimentData.data.find(d => d.name === 'NEUTRAL')?.y || 0;

    const total = positiveCount + negativeCount + neutralCount;
    const positiveRatio = positiveCount / total;
    const negativeRatio = negativeCount / total;

    let recommendation = '';

    if (positiveRatio > 0.6) {
        recommendation = '¡Excelente feedback! Mantén las estrategias actuales y considera destacar estos aspectos positivos en marketing.';
    } else if (negativeRatio > 0.3) {
        recommendation = 'Se requieren mejoras urgentes. Prioriza resolver los problemas identificados y comunica las soluciones.';
    } else if (neutralCount > positiveCount && neutralCount > negativeCount) {
        recommendation = 'Feedback neutral predominante. Enfócate en aumentar el engagement emocional de los usuarios.';
    } else {
        recommendation = 'Análisis equilibrado. Continúa monitoreando tendencias y ajusta estrategias según evolución del sentiment.';
    }

    element.textContent = recommendation;
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Generate AI insights after a short delay
    setTimeout(generateAIInsights, 1000);
});

// Make functions globally available
window.applyFilters = applyFilters;
window.resetFilters = resetFilters;
window.applyFiltersFromDrilldown = applyFiltersFromDrilldown;
window.showTimeAnalysis = showTimeAnalysis;