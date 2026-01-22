import React, { useEffect, useState, useCallback } from 'react';
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
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // 1. Extraemos la lógica de obtención de datos a una función reutilizable
  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(API_URL + '/api/data');
      const json = await res.json();

      if (Array.isArray(json)) {
        const formattedData = json.map((item: any) => {
          // TRUCO: Cortamos el string "2026-01-21 19:25:00" por el espacio
          // y nos quedamos con la segunda parte (la hora).
          const horaCompleta = item.datetime.split(' ')[1]; // "19:25:00"

          return {
            // Tomamos solo los primeros 5 caracteres: "19:25"
            time: horaCompleta ? horaCompleta.substring(0, 5) : item.datetime,

            // Usamos las minúsculas correctas
            open: parseFloat(item.open) || 0,
            close: parseFloat(item.close) || 0,
            high: parseFloat(item.high) || 0,
            low: parseFloat(item.low) || 0,
          };
        });

        const cleanData = formattedData.filter((d: any) => d.close > 0);
        setData(cleanData);
      }
    } catch (err) {
      console.error("Error fetching data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // 2. Llamada inicial inmediata
    fetchData();

    // 3. Configurar el intervalo (Polling) cada 5 segundos
    // Tu backend actualiza cada ~20s, así que 5s asegura que verás el cambio rápido
    const interval = setInterval(() => {
      fetchData();
    }, 5000);

    // 4. Limpieza: Importante para detener el reloj si el usuario cierra la pestaña/componente
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading) return <div className="p-4 text-white">Cargando datos iniciales...</div>;
  if (data.length === 0) return <div className="p-4 text-white">No hay datos disponibles</div>;

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
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
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
              formatter={(value: number) => [value.toFixed(2), "Precio"]}
              labelStyle={{ color: '#848E9C' }}
            />
            <Line
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