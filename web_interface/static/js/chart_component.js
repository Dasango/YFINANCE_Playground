// chart_component.js
// Encapsulates Plotly logic

let plotInstance = null;

export function renderChart(containerId, realData, predictionData = null, predictionName = "Predicción") {
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

    // Trace 2: Prediction (if exists)
    if (predictionData) {
        const trace2 = {
            x: predictionData.dates,
            y: predictionData.values,
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

    const config = { responsive: true };

    Plotly.newPlot(containerId, data, layout, config);
}
