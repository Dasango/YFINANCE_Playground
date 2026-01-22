import React, { useEffect, useState } from 'react';
import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts';

const API_URL = import.meta.env.VITE_FASTAPI_URL;

const MiniPredictionChart: React.FC = () => {
    const [chartData, setChartData] = useState<any[]>([]);
    const [trendType, setTrendType] = useState<'positive' | 'negative'>('positive');

    useEffect(() => {
        const fetchPrediction = async () => {
            try {
                const res = await fetch(`${API_URL}/api/predict`);
                const data = await res.json();

                if (data.history && data.predictions) {
                    const history = data.history.map((val: number, i: number) => ({
                        index: i,
                        history: val,
                        prediction: null
                    }));

                    // Connect the last history point to the first prediction point
                    // to make the line continuous, or just start predictions
                    // We'll just plot them.

                    // To connect lines visually, the first point of "prediction" line 
                    // should often match the last point of "history" line, 
                    // or we accept a gap. 
                    // Let's create a combined dataset.

                    const lastHistoryVal = data.history[data.history.length - 1];
                    const predictions = data.predictions.map((val: number, i: number) => ({
                        index: data.history.length + i,
                        history: null,
                        prediction: val
                    }));

                    // Add a bridge point? 
                    // Let's modify the first prediction point to start at the last history?
                    // Or add a point that has both?
                    const bridgePoint = {
                        index: data.history.length - 1,
                        history: lastHistoryVal,
                        prediction: lastHistoryVal
                    };

                    // Replace last history point with bridge point 
                    // so prediction line starts there.
                    history[history.length - 1] = bridgePoint;

                    const fullData = [...history, ...predictions];
                    setChartData(fullData);

                    // Calculate mean of predictions
                    const predSum = data.predictions.reduce((a: number, b: number) => a + b, 0);
                    const predMean = predSum / data.predictions.length;

                    // "Si al sacar la media de predicionts es negativo..." 
                    // Interpreted as: Mean < Last History Value (Trend is down) -> Green
                    // Otherwise -> Red
                    const diff = predMean - lastHistoryVal;

                    if (diff < 0) {
                        setTrendType('negative'); // "negativo" -> Green glow requested
                    } else {
                        setTrendType('positive'); // Red glow
                    }
                }
            } catch (error) {
                console.error("Error loading mini prediction:", error);
            }
        };

        fetchPrediction();
        const interval = setInterval(fetchPrediction, 5000);
        return () => clearInterval(interval);
    }, []);

    // Glow color logic: 
    // "negativo que los alrededores ... respolandor interior verde"
    // "de lo contrario uno rojo"
    const glowClass = trendType === 'negative'
        ? 'shadow-[inset_0_0_10px_rgba(34,197,94,0.5)] border-green-500/30'
        : 'shadow-[inset_0_0_10px_rgba(239,68,68,0.5)] border-red-500/30';

    return (
        <div className={`relative w-40 h-10 bg-[#1E2026] rounded overflow-hidden border ${glowClass} transition-shadow duration-500 mx-4`}>
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                    <Line
                        type="monotone"
                        dataKey="history"
                        stroke="#FCD535" // Yellow
                        strokeWidth={2}
                        dot={false}
                        isAnimationActive={false}
                    />
                    <Line
                        type="monotone"
                        dataKey="prediction"
                        stroke="#0ea5e9" // Light Blue (Celeste)
                        strokeWidth={2}
                        dot={false}
                        isAnimationActive={false}
                    />
                    <YAxis domain={['auto', 'auto']} hide />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};

export default MiniPredictionChart;
