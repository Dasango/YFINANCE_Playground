// controls_component.js

export function initControls(containerId, possibleFeatures, onTrainClick, onStopClick) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // 1. Feature Buttons
    const featuresDiv = document.getElementById('feature-buttons');
    featuresDiv.innerHTML = ''; // Clear

    const selectedFeatures = new Set();

    possibleFeatures.forEach(feat => {
        const btn = document.createElement('button');
        btn.textContent = feat;
        btn.className = 'feature-btn';
        btn.onclick = () => {
            if (selectedFeatures.has(feat)) {
                selectedFeatures.delete(feat);
                btn.classList.remove('active');
            } else {
                selectedFeatures.add(feat);
                btn.classList.add('active');
            }
        };
        featuresDiv.appendChild(btn);
    });

    // 2. Train Button Logic
    const trainBtn = document.getElementById('train-btn');
    let isTraining = false; // State to track mode

    trainBtn.onclick = () => {
        if (!isTraining) {
            // "Entrenar" mode
            if (selectedFeatures.size === 0) {
                alert("Por favor selecciona al menos una feature.");
                return;
            }
            // Sort features to match file naming convention (alphabetical usually? or by fixed order)
            // Script python usa: Close, High, Low, Open, Volume alphabetical order?
            // itertools.combinations preserves order of input list inputs.
            // input list was: ["Close", "High", "Low", "Open", "Volume"]
            // So we must sort based on that order.

            const featureOrder = ["Close", "High", "Low", "Open", "Volume"];
            const sorted = Array.from(selectedFeatures).sort((a, b) => {
                return featureOrder.indexOf(a) - featureOrder.indexOf(b);
            });

            // Callback to App
            onTrainClick(sorted.join("_"));

            // Visual update
            trainBtn.textContent = "Detener";
            trainBtn.classList.remove('btn-primary');
            trainBtn.classList.add('btn-danger');
            isTraining = true;
        } else {
            // "Detener" mode
            onStopClick();

            // Visual update
            trainBtn.textContent = "Entrenar (Ver Predicción)";
            trainBtn.classList.remove('btn-danger');
            trainBtn.classList.add('btn-primary');
            isTraining = false;
        }
    };
}
