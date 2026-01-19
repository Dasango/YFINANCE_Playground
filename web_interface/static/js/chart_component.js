// chart_component.js
// Encapsulates Plotly logic

let plotInstance = null;

export function renderChart(containerId, realData, predictionData = null, predictionName = "Predicción", currentLoss = null, currentEpoch = null) {
    const dates = realData.dates;
    const values = realData.values;
    const ticker = realData.ticker;

    // Trace 1: Real Data
    const trace1 = {
        x: dates,
        y: values,
        mode: 'lines',
        name: `Real Data (${ticker})`,
        line: {
            color: '#10b981', // emerald-500
            width: 2
        }
    };

    const data = [trace1];

    // Calculate History Sim (Continuity logic)
    let historySimValues = null;
    let connectPoint = null;

    if (currentLoss !== null) {
        const lossVal = parseFloat(currentLoss);

        // History Trace: User LIKES noise here.
        // Factor = 1 - loss - noise
        historySimValues = values.map(v => {
            // Noise proportional to loss
            const noise = Math.random() * lossVal;
            const factor = 1 - lossVal - noise;
            return v * factor;
        });

        // The last point of history sim determines where prediction starts
        connectPoint = historySimValues[historySimValues.length - 1];

        const traceHistory = {
            x: dates,
            y: historySimValues,
            mode: 'lines',
            name: 'Training Sim',
            line: {
                color: '#ef4444',
                width: 2,
                dash: 'dot'
            },
            showlegend: false
        };
        data.push(traceHistory);
    }

    // Trace 2: Prediction (Future)
    if (predictionData) {
        let predValues;
        const targetValues = predictionData.values;

        if (currentLoss !== null && connectPoint !== null) {
            const lossVal = parseFloat(currentLoss);

            // "Unfolding" Effect + Conditional Noise

            // 1. Unfolding Factor (0 = Flat, 1 = Full Shape)
            // Multiplier 150: Requires loss < 0.006 to be fully unfolded.
            // This makes it stay "low/flat" much longer and rise slowly.
            const shapeFactor = Math.max(0, Math.min(1, 1 - (lossVal * 150)));

            const targetStart = targetValues[0];

            predValues = targetValues.map(v => {
                // Base Shape (Unfolded)
                const delta = v - targetStart;
                let val = connectPoint + (delta * shapeFactor);

                // 2. Conditional Noise
                // "mete el ruido aleatorio por lo menos que el loss sea menor que 0.0002"
                if (lossVal >= 0.0002) {
                    // Noise magnitude proportional to loss
                    const noiseMag = lossVal * (values[values.length - 1] * 0.01);
                    // Increased noise factor to 25 for "more erratic"
                    const rnd = (Math.random() - 0.5) * noiseMag * 25;
                    val += rnd;
                }

                return val;
            });

        } else {
            // Standard/Final View
            predValues = targetValues;
        }

        const trace2 = {
            x: predictionData.dates,
            y: predValues,
            mode: 'lines',
            name: predictionName,
            line: {
                color: '#ef4444',
                width: 2,
                dash: 'dot'
            }
        };
        data.push(trace2);
    }

    const layout = {
        title: {
            text: 'Market Data & Predictions (Last 100)',
            font: { color: '#ffffff' }
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        xaxis: {
            gridcolor: 'rgba(255,255,255,0.1)',
            zerolinecolor: 'rgba(255,255,255,0.1)',
            tickfont: { color: '#9ca3af' }
        },
        yaxis: {
            gridcolor: 'rgba(255,255,255,0.1)',
            zerolinecolor: 'rgba(255,255,255,0.1)',
            tickfont: { color: '#9ca3af' }
        },
        legend: {
            font: { color: '#ffffff' }
        },
        margin: { t: 40, r: 20, l: 40, b: 40 }
    };

    const config = { responsive: true, displayModeBar: false };

    Plotly.react(containerId, data, layout, config);
}

export function renderTrainingChart(containerId, xValues, yValues, epochNum, currentLoss) {
    const trace = {
        x: xValues,
        y: yValues,
        mode: 'lines',
        line: {
            color: '#f59e0b', // amber-500
            width: 2,
            shape: 'spline'
        },
        fill: 'tozeroy',
        fillcolor: 'rgba(245, 158, 11, 0.1)'
    };

    const lossText = currentLoss !== undefined ? ` | Loss: ${Number(currentLoss).toFixed(5)}` : '';

    const layout = {
        title: {
            text: `Epoch ${epochNum}${lossText}`,
            font: { color: '#ffffff', size: 14 }
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        margin: { t: 30, r: 10, l: 30, b: 20 },
        xaxis: {
            showgrid: false,
            zeroline: false,
            showticklabels: false,
            fixedrange: false
        },
        yaxis: {
            showgrid: false,
            zeroline: false,
            showticklabels: false,
            fixedrange: false
        }
    };

    const config = { responsive: true, displayModeBar: false };

    Plotly.react(containerId, [trace], layout, config);
}
