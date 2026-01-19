// chart_component.js
// Encapsulates Plotly logic

let plotInstance = null;

export function renderChart(containerId, realData, predictionData = null, predictionName = "Predicción", currentLoss = null) {
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

    // Scale factor based on loss (if training)
    // If loss is e.g. 0.05, factor is 0.95. The line is 95% of height.
    const scaleFactor = currentLoss !== null ? (1 - parseFloat(currentLoss)) : 1;

    // Trace 3: Historical Sim (Red line below Real Data)
    if (currentLoss !== null) {
        // Same x as real data, y scaled
        const historySimValues = values.map(v => v * scaleFactor);
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
            showlegend: false // Optional, maybe clutter
        };
        data.push(traceHistory);
    }

    // Trace 2: Prediction (if exists)
    if (predictionData) {
        // Apply scaling to prediction as well
        const predValues = currentLoss !== null
            ? predictionData.values.map(v => v * scaleFactor)
            : predictionData.values;

        const trace2 = {
            x: predictionData.dates,
            y: predValues, // Use scaled values
            mode: 'lines',
            name: predictionName,
            line: {
                color: '#ef4444', // red-500
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

    // Use react for efficient updates
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
            shape: 'spline' // smooth curve
        },
        fill: 'tozeroy', // Optional: fill under line for cool effect
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
            fixedrange: false // Allow zoom/pan/autoscale
        },
        yaxis: {
            showgrid: false,
            zeroline: false,
            showticklabels: false,
            fixedrange: false
        }
    };

    // Removed staticPlot: true to avoid rendering issues with updates
    const config = { responsive: true, displayModeBar: false };

    Plotly.react(containerId, [trace], layout, config);
}
