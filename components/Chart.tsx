import React, { useEffect, useState, useMemo } from 'react';
import { usePlayground } from '../context/PlaygroundContext';
const API_URL = import.meta.env.VITE_FASTAPI_URL;
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

const Chart: React.FC = () => {
  const { candleData } = usePlayground();
  const [predictions, setPredictions] = useState<any[]>([]);

  // Fetch predictions independently but aligned with updates
  useEffect(() => {
    const fetchPredictions = async () => {
      try {
        const res = await fetch(API_URL + '/api/predictions');
        if (res.ok) {
          const json = await res.json();
          setPredictions(json);
        }
      } catch (e) {
        console.error("Error fetching predictions", e);
      }
    };

    fetchPredictions();
    const interval = setInterval(fetchPredictions, 5000);
    return () => clearInterval(interval);
  }, []);

  const combinedData = useMemo(() => {
    if (!candleData.length) return [];

    const predsMap = new Map();
    if (Array.isArray(predictions)) {
      predictions.forEach((p: any) => {
        predsMap.set(p.datetime, p.predicted_close);
      });
    }

    return candleData.map((d: any) => ({
      ...d,
      predicted_close: predsMap.has(d.datetime) ? parseFloat(predsMap.get(d.datetime)) : null
    }));
  }, [candleData, predictions]);

  if (combinedData.length === 0) return <div className="p-4 text-white">Cargando datos...</div>;

  return (
    <div className="flex flex-col h-full bg-[#161A1E] border-r border-[#2B3139]">
      <div className="flex items-center justify-between px-4 py-2 border-b border-[#2B3139]">
        <div className="flex gap-4 text-xs font-medium text-[#848E9C]">
          <span className="text-[#FCD535]">BTC-USD</span>
          {/* Indicador visual opcional de "En vivo" */}
          <span className="flex items-center gap-1 text-green-500">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
            LIVE
          </span>
        </div>
      </div>

      <div className="flex-1 w-full min-h-[400px] py-4 relative">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={combinedData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#2B3139" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 10, fill: '#848E9C' }}
              axisLine={false}
              tickLine={false}
              minTickGap={30}
            />
            <YAxis
              domain={['auto', 'auto']}
              orientation="right"
              tick={{ fontSize: 10, fill: '#848E9C' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(val) => val.toLocaleString()}
              width={60}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#1E2026', borderColor: '#2B3139', color: '#fff' }}
              itemStyle={{ fontSize: 12, color: '#FCD535' }}
              formatter={(value: number, name: string) => [value.toFixed(2), name]}
              labelStyle={{ color: '#848E9C' }}
            />
            <Line
              name="Predicción"
              type="monotone"
              dataKey="predicted_close"
              stroke="#0ea5e9" // Azul cielo para diferenciar
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
              strokeDasharray="5 5" // Punteada para indicar que es predicción/evaluación
            />
            <Line
              name="Precio"
              type="monotone"
              dataKey="close"
              stroke="#FCD535"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: '#fff' }}
              isAnimationActive={false} // Desactivar animación para que las actualizaciones se sientan fluidas
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default Chart;