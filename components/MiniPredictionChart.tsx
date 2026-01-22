import React, { useEffect, useState } from 'react';
import { LineChart, Line, ResponsiveContainer, YAxis, XAxis } from 'recharts';

// Asegúrate de que esta variable de entorno esté definida en tu proyecto (ej. .env.local)
const API_URL = import.meta.env.VITE_FASTAPI_URL;

// Definimos una interfaz simple para los datos del gráfico
interface ChartPoint {
    index: number;
    history: number | null;
    prediction: number | null;
}

const MiniPredictionChart: React.FC = () => {
    const [chartData, setChartData] = useState<ChartPoint[]>([]);
    // 'positive' = media de predicción > último histórico (Rojo)
    // 'negative' = media de predicción < último histórico (Verde)
    const [trendType, setTrendType] = useState<'positive' | 'negative'>('positive');
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchPrediction = async () => {
            try {
                // Opcional: si quieres un estado de carga visual, descomenta esto
                // setIsLoading(true);
                const res = await fetch(`${API_URL}/api/predict`);
                const data = await res.json();

                if (data.history && data.predictions && data.history.length > 0) {
                    const lastHistoryVal = data.history[data.history.length - 1];

                    // 1. Preparar datos históricos
                    const historyPoints: ChartPoint[] = data.history.map((val: number, i: number) => ({
                        index: i,
                        history: val,
                        prediction: null
                    }));

                    // 2. Preparar datos de predicción
                    // El primer punto de predicción debe coincidir con el último histórico
                    // para que las líneas se conecten visualmente sin huecos.
                    const predictionPoints: ChartPoint[] = [];

                    // Punto puente (el último histórico es el inicio de la predicción)
                    predictionPoints.push({
                        index: data.history.length - 1,
                        history: lastHistoryVal, // Necesario para que Recharts lo dibuje
                        prediction: lastHistoryVal
                    });

                    // Resto de predicciones
                    data.predictions.forEach((val: number, i: number) => {
                        predictionPoints.push({
                            index: data.history.length + i,
                            history: null,
                            prediction: val
                        });
                    });

                    // Combinar y eliminar duplicados en el punto puente si es necesario
                    // Una forma simple es reemplazar el último de historia con el puente
                    historyPoints[historyPoints.length - 1] = predictionPoints[0];
                    // Y unir el resto de predicciones (desde el índice 1)
                    const fullData = [...historyPoints, ...predictionPoints.slice(1)];

                    setChartData(fullData);

                    // 3. Lógica de Tendencia (Media vs Último Histórico)
                    const predSum = data.predictions.reduce((a: number, b: number) => a + b, 0);
                    const predMean = predSum / data.predictions.length;

                    const diff = predMean - lastHistoryVal;

                    // Si la diferencia es negativa (la media futura es menor al precio actual),
                    // ponemos 'negative' que se traducirá al color VERDE según tu petición.
                    if (diff < 0) {
                        setTrendType('negative'); // Tendencia a la baja -> Verde
                    } else {
                        setTrendType('positive'); // Tendencia al alza -> Rojo
                    }
                }
            } catch (error) {
                console.error("Error loading mini prediction:", error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchPrediction();
        // Actualizar cada 5 segundos
        const interval = setInterval(fetchPrediction, 5000);
        return () => clearInterval(interval);
    }, []);

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
        <div className={`relative w-44 h-12 bg-[#1E2026] rounded-md overflow-hidden border ${glowClasses} transition-all duration-700 ease-in-out mx-4 flex items-center`}>

            {/* Pequeño indicador de texto opcional (puedes quitarlo si quieres solo gráfica) */}
            <div className={`absolute top-1 left-2 text-[10px] font-bold ${glowClasses.split(' ').pop()}`}>
                {trendType === 'negative' ? '▼ PRED' : '▲ PRED'}
            </div>

            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
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
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};

export default MiniPredictionChart;