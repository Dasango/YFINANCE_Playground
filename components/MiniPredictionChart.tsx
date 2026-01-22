import React, { useEffect, useState } from 'react';
import { LineChart, Line, ResponsiveContainer, YAxis, XAxis, CartesianGrid, Tooltip } from 'recharts';
import { usePlayground } from '../context/PlaygroundContext';

const API_URL = import.meta.env.VITE_FASTAPI_URL;

interface ChartPoint {
    index: number;
    history: number | null;
    prediction: number | null;
    velocity?: number | null;
}

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        const historyData = payload.find((p: any) => p.dataKey === 'history');
        const predictionData = payload.find((p: any) => p.dataKey === 'prediction');

        if (historyData && historyData.value !== null) {
            return (
                <div className="bg-[#1E2026] border border-[#2B3139] p-2 rounded shadow text-xs">
                    <p className="text-[#FCD535]">Precio real: {historyData.value.toFixed(2)}</p>
                </div>
            );
        }

        if (predictionData && predictionData.value !== null) {
            const velocity = predictionData.payload.velocity;
            return (
                <div className="bg-[#1E2026] border border-[#2B3139] p-2 rounded shadow text-xs">
                    <p className="text-[#38bdf8]">Predicción: {predictionData.value.toFixed(2)}</p>
                    {velocity !== undefined && velocity !== null && (
                        <p className={`text-[10px] mt-1 ${velocity >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            Velocidad: {velocity.toFixed(2)}
                        </p>
                    )}
                </div>
            );
        }
    }
    return null;
};

const MiniPredictionChart: React.FC = () => {
    const { candleData } = usePlayground();
    const [chartData, setChartData] = useState<ChartPoint[]>([]);
    const [trendType, setTrendType] = useState<'positive' | 'negative'>('positive');
    const [predictionSpeed, setPredictionSpeed] = useState<number>(0);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchPrediction = async () => {
            try {
                const res = await fetch(`${API_URL}/api/predict`);
                const data = await res.json();

                // We use global candleData for history to ensure sync with main chart/ticker
                // We take the last 15 points to match the visual style or whatever amount 'history' usually returned
                const historyLength = 15;
                const relevantHistory = candleData.slice(-historyLength);

                if (relevantHistory.length > 0 && data.predictions) {
                    const lastHistoryVal = relevantHistory[relevantHistory.length - 1].close;

                    // 1. Prepare History Points from Context
                    const historyPoints: ChartPoint[] = relevantHistory.map((d: any, i: number) => ({
                        index: i,
                        history: d.close,
                        prediction: null
                    }));

                    // 2. Prepare Prediction Points
                    const predictionPoints: ChartPoint[] = [];

                    // Bridge point
                    predictionPoints.push({
                        index: relevantHistory.length - 1,
                        history: lastHistoryVal,
                        prediction: lastHistoryVal
                    });

                    // Predictions
                    let previousVal = lastHistoryVal;
                    data.predictions.forEach((val: number, i: number) => {
                        const velocity = val - previousVal;
                        predictionPoints.push({
                            index: relevantHistory.length + i,
                            history: null,
                            prediction: val,
                            velocity: velocity
                        });
                        previousVal = val;
                    });

                    // Merge
                    // Fix the bridge: update the last history point to include the prediction start
                    historyPoints[historyPoints.length - 1] = predictionPoints[0];

                    const fullData = [...historyPoints, ...predictionPoints.slice(1)];
                    setChartData(fullData);

                    // 3. Trend Logic
                    const predSum = data.predictions.reduce((a: number, b: number) => a + b, 0);
                    const predMean = predSum / data.predictions.length;
                    const diff = predMean - lastHistoryVal;

                    if (diff < 0) {
                        setTrendType('negative');
                    } else {
                        setTrendType('positive');
                    }
                    setPredictionSpeed(diff);
                }
            } catch (error) {
                console.error("Error loading mini prediction:", error);
            } finally {
                setIsLoading(false);
            }
        };

        // Only fetch if we have history
        if (candleData.length > 0) {
            fetchPrediction();
        }

        const interval = setInterval(() => {
            if (candleData.length > 0) fetchPrediction();
        }, 5000);

        return () => clearInterval(interval);
    }, [candleData]); // Re-run when candleData updates to keep in sync

    // Lógica de estilos basada en Tailwind CSS
    // 'negative' (baja) -> Verde
    // 'positive' (alza) -> Rojo
    const glowClasses = trendType === 'negative'
        ? 'shadow-[inset_0_0_12px_rgba(34,197,94,0.4)] border-green-500/50 text-green-400' // Verde esmeralda
        : 'shadow-[inset_0_0_12px_rgba(239,68,68,0.4)] border-red-500/50 text-red-400';    // Rojo

    if (isLoading && chartData.length === 0) {
        // Un placeholder simple mientras carga la primera vez
        return <div className="w-44 h-12 bg-[#1E2026] rounded border border-gray-700 mx-4 animate-pulse"></div>;
    }

    return (
        // Contenedor principal:
        // - w-44 h-12: Tamaño fijo pequeño (ajusta según necesites)
        // - bg-[#1E2026]: Fondo oscuro que coincide con tu interfaz
        // - border y transition: Para el cambio suave de color
        <div className={`relative w-full h-32 bg-[#1E2026] rounded-none overflow-hidden border-y ${glowClasses} transition-all duration-700 ease-in-out flex items-center`}>

            {/* Pequeño indicador de texto con la velocidad/pendiente */}
            <div className={`absolute top-1 left-2 text-[10px] font-bold ${glowClasses.split(' ').pop()}`}>
                {trendType === 'negative' ? '▼' : '▲'} PRED {predictionSpeed.toFixed(2)}
            </div>

            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
                    <CartesianGrid stroke="#2B3139" strokeDasharray="3 3" />
                    {/* Ejes ocultos necesarios para el escalado automático */}
                    <YAxis domain={['auto', 'auto']} hide padding={{ top: 10, bottom: 10 }} />
                    <XAxis dataKey="index" hide />

                    {/* Línea Histórica (Amarilla) */}
                    <Line
                        type="monotone"
                        dataKey="history"
                        stroke="#FCD535"
                        strokeWidth={1.5}
                        dot={false}
                        isAnimationActive={false}
                        connectNulls={true} // Importante para que no se corte
                    />
                    {/* Línea Predicción (Celeste) */}
                    <Line
                        type="monotone"
                        dataKey="prediction"
                        stroke="#38bdf8" // Un celeste brillante (sky-400 de tailwind)
                        strokeWidth={1.5}
                        dot={false}
                        strokeDasharray="3 3" // Opcional: línea punteada para indicar que es predicción
                        isAnimationActive={false}
                        connectNulls={true}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#2B3139', strokeWidth: 1 }} />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};

export default MiniPredictionChart;