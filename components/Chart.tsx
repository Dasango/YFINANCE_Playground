import React, { useEffect, useState } from 'react';
import {
  ComposedChart,
  Line, // <--- CAMBIO IMPORTANTE
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

const Chart: React.FC = () => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/data')
      .then((res) => res.json())
      .then((json) => {
        if (Array.isArray(json)) {
          const formattedData = json.map((item: any) => ({
            time: item.datetime || item.Date,
            // Aseguramos que sea número. Si falla, devuelve 0 para que no rompa la gráfica.
            open: parseFloat(item.Open) || 0,
            close: parseFloat(item.Close) || 0,
            high: parseFloat(item.High) || 0,
            low: parseFloat(item.Low) || 0,
          }));

          // Filtramos basura para evitar que un NaN rompa toda la línea
          const cleanData = formattedData.filter((d: any) => d.close > 0);

          setData(cleanData);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching data:", err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="p-4 text-white">Cargando datos...</div>;
  if (data.length === 0) return <div className="p-4 text-white">No hay datos disponibles</div>;

  // Cálculos de mínimo y máximo para que la línea no se vea plana
  const minPrice = Math.min(...data.map(d => d.low));
  const maxPrice = Math.max(...data.map(d => d.high));
  const lastBar = data[data.length - 1];

  return (
    <div className="flex flex-col h-full bg-[#161A1E] border-r border-[#2B3139]">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-[#2B3139]">
        <div className="flex gap-4 text-xs font-medium text-[#848E9C]">
          <span className="text-[#FCD535]">BTC-USD (Línea)</span>
          <span>15m</span>
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
              domain={[minPrice, maxPrice]} // Escala automática ajustada
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

            {/* AQUÍ ESTÁ EL CAMBIO: Usamos LINE en vez de BAR con CustomShape */}
            <Line
              type="monotone"
              dataKey="close"
              stroke="#FCD535"
              strokeWidth={2}
              dot={false} // Sin puntos en cada dato, solo la línea limpia
              activeDot={{ r: 4, fill: '#fff' }}
            />

          </ComposedChart>
        </ResponsiveContainer>

        {/* Panel de información simple */}
        <div className="absolute top-4 left-4 bg-[#1E2026]/90 p-2 rounded border border-[#2B3139]">
          <div className="text-xs text-[#848E9C]">
            Precio Actual: <span className="text-[#FCD535] text-sm font-bold">{lastBar.close.toFixed(2)}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chart;