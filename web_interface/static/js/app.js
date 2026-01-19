import { renderChart, renderTrainingChart } from './chart_component.js';
import { initControls } from './controls_component.js';

// State
let currentRealData = null;
let currentPredictionData = null; // Store fetched prediction
let animationInterval = null;

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
    const statusEl = document.getElementById('status-text');
    const trainChartContainer = document.getElementById('training-chart');

    statusEl.textContent = `Iniciando entrenamiento virtual para: ${featuresStr}...`;
    trainChartContainer.style.display = 'block';

    try {
        // 1. Fetch Logs
        const logsResponse = await fetch(`${API_BASE}/logs/${featuresStr}`);
        if (!logsResponse.ok) throw new Error("Logs no encontrados");
        const logsData = await logsResponse.json();

        // Group by Epoch
        const epochs = {};
        for (let i = 0; i < logsData.epoch.length; i++) {
            const ep = logsData.epoch[i];
            if (!epochs[ep]) epochs[ep] = { batch: [], loss: [] };
            epochs[ep].batch.push(logsData.batch[i]);
            epochs[ep].loss.push(logsData.loss[i]);
        }

        const epochKeys = Object.keys(epochs).sort((a, b) => a - b);

        // 1.1 Fetch Prediction Data EARLY (to use in loop)
        try {
            const predResponse = await fetch(`${API_BASE}/predict/${featuresStr}`);
            if (predResponse.ok) {
                currentPredictionData = await predResponse.json();
            } else {
                console.warn("Prediction not found early");
            }
        } catch (e) { console.error("Error fetching prediction early", e); }

        // Global arrays (acumulados para "anidar" datos)
        const allBatches = [];
        const allLosses = [];
        let globalStepCounter = 0;

        // 2. Animate
        let currentEpochIdx = 0;

        async function playEpoch() {
            if (currentEpochIdx >= epochKeys.length) {
                statusEl.textContent = "Entrenamiento finalizado.";
                // Final render with full opacity (loss ~0 or explicit call without loss scaling?)
                // If we want to stay "scaled", we use last known loss. 
                // If we want to show 'true' prediction at end, call without loss arg.
                renderChart('chart-container', currentRealData, currentPredictionData, `Pred: ${featuresStr}`);
                return;
            }

            const epNum = epochKeys[currentEpochIdx]; // e.g. "0", "1"
            const epData = epochs[epNum];
            const duration = 5000; // 5s total per epoch
            const steps = epData.batch.length;
            const stepTime = duration / steps;

            let currentStep = 0;

            // Clear previous interval if any
            if (animationInterval) clearInterval(animationInterval);

            animationInterval = setInterval(() => {
                // If stopped mid-animation
                if (!animationInterval) return;

                if (currentStep >= steps) {
                    clearInterval(animationInterval);
                    currentEpochIdx++;
                    playEpoch(); // Next epoch
                    return;
                }

                // Add new point
                const currentBatchLoss = epData.loss[currentStep];
                allBatches.push(globalStepCounter++);
                allLosses.push(currentBatchLoss);

                // Update Training Chart
                renderTrainingChart('training-chart', [...allBatches], [...allLosses], epNum, currentBatchLoss);

                // Update Main Chart (Dynamic Lines!)
                if (currentRealData && currentPredictionData) {
                    // Pass epNum for Chaos Phase Logic check
                    renderChart(
                        'chart-container',
                        currentRealData,
                        currentPredictionData,
                        `Pred: ${featuresStr}`,
                        currentBatchLoss,
                        epNum
                    );
                }

                currentStep++;

            }, stepTime);
        }

        playEpoch();

    } catch (e) {
        console.error(e);
        statusEl.textContent = "Error iniciando entrenamiento/logs: " + e.message;
        if (currentPredictionData) {
            renderChart('chart-container', currentRealData, currentPredictionData, `Pred: ${featuresStr}`);
        }
    }
}

function handleStop() {
    // Stop animation
    if (animationInterval) {
        clearInterval(animationInterval);
        animationInterval = null;
    }
    document.getElementById('training-chart').style.display = 'none';

    // Reset charts (clean view)
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
