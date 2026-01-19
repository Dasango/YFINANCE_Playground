import { renderChart } from './chart_component.js';
import { initControls } from './controls_component.js';

// State
let currentRealData = null;

const API_BASE = "http://127.0.0.1:8000/api";

async function loadRealData() {
    try {
        const response = await fetch(`${API_BASE}/real_data`);
        if (!response.ok) throw new Error("Error loading data");
        currentRealData = await response.json();

        // Render initial chart
        renderChart('chart-container', currentRealData);
        document.getElementById('status-text').textContent = `Datos cargados: ${currentRealData.ticker}`;
    } catch (e) {
        console.error(e);
        document.getElementById('status-text').textContent = "Error cargando datos. Asegúrate que backend corra.";
    }
}

async function handleTrain(featuresStr) {
    document.getElementById('status-text').textContent = `Cargando predicción para: ${featuresStr}...`;
    try {
        const response = await fetch(`${API_BASE}/predict/${featuresStr}`);
        if (!response.ok) {
            alert("No se encontró predicción para esta combinación.");
            // Revert button state visually handled by user click but we should probably tell UI
            // For simplicity, we just alert. logic keeps "Training" state until Stop is clicked.
            return;
        }
        const predData = await response.json();

        // Update Chart with both Real + Pred
        renderChart('chart-container', currentRealData, predData, `Pred: ${featuresStr}`);
        document.getElementById('status-text').textContent = `Mostrando predicción: ${featuresStr}`;

    } catch (e) {
        console.error(e);
        alert("Error cargando predicción");
    }
}

function handleStop() {
    // Clear prediction from chart
    renderChart('chart-container', currentRealData);
    document.getElementById('status-text').textContent = "Visualización detenida.";
}

// Init
window.addEventListener('DOMContentLoaded', () => {
    // Initialize Controls
    const possibleFeatures = ["Close", "High", "Low", "Open", "Volume"];
    initControls('controls-container', possibleFeatures, handleTrain, handleStop);

    // Load Data
    loadRealData();
});
