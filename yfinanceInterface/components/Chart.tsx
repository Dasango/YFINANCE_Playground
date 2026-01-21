import React from 'react';
import {
  ComposedChart,
  Bar, // Only Bar is needed for candlesticks, Line is removed
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { MOCK_DATA } from '../constants';

// Custom shape for the candlestick
// Recharts passes standard props (x, y, width, height) plus payload (our data)
const CustomCandle = (props: any) => {
  const { x, y, width, height, payload } = props;
  const { open, close, high, low } = payload;
  
  // Determine color based on open/close
  const isGreen = close >= open;
  const color = isGreen ? '#0ECB81' : '#F6465D';
  
  const { xAxis, yAxis } = props;
  if (!xAxis || !yAxis) return null;

  // Scale open, close, high, low values to pixel coordinates
  const yOpen = yAxis.scale(open);
  const yClose = yAxis.scale(close);
  const yHigh = yAxis.scale(high);
  const yLow = yAxis.scale(low);
  
  // Increased barWidth significantly for better visibility, 90% of available width
  const barWidth = width * 0.9;
  const xCentered = x + width / 2;

  // Calculate body dimensions, ensuring a minimum height for very small price changes
  const bodyHeight = Math.max(2, Math.abs(yOpen - yClose)); // Ensure minimum height of 2px
  const bodyY = Math.min(yOpen, yClose);

  return (
    <g>
      {/* Wick - increased strokeWidth for visibility */}
      <line
        x1={xCentered}
        y1={yHigh}
        x2={xCentered}
        y2={yLow}
        stroke={color}
        strokeWidth={3} // Increased to 3 for better visibility
      />
      {/* Body */}
      <rect
        x={x + (width - barWidth) / 2}
        y={bodyY}
        width={barWidth}
        height={bodyHeight}
        fill={color}
        stroke={color}
      />
    </g>
  );
};

const Chart: React.FC = () => {
  // Calculate min/max price for Y-axis domain, adding a small buffer
  const minPrice = Math.min(...MOCK_DATA.map(d => d.low)) * 0.999;
  const maxPrice = Math.max(...MOCK_DATA.map(d => d.high)) * 1.001;

  return (
    <div className="flex flex-col h-full bg-[#161A1E] border-r border-[#2B3139]">
      <div className="flex items-center justify-between px-4 py-2 border-b border-[#2B3139]">
        <div className="flex gap-4 text-xs font-medium text-[#848E9C]">
          <span className="hover:text-[#FCD535] cursor-pointer">Time</span>
          <span className="text-[#FCD535] cursor-pointer">15m</span>
          <span className="hover:text-[#FCD535] cursor-pointer">1H</span>
          <span className="hover:text-[#FCD535] cursor-pointer">4H</span>
          <span className="hover:text-[#FCD535] cursor-pointer">1D</span>
          <span className="hover:text-[#FCD535] cursor-pointer">1W</span>
        </div>
        <div className="text-xs text-[#848E9C]">Original | TradingView | Depth</div>
      </div>
      
      <div className="flex-1 w-full min-h-[400px] py-4 relative">
         <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={MOCK_DATA} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#2B3139" strokeDasharray="3 3" vertical={false} />
            <XAxis 
              dataKey="time" 
              tick={{ fontSize: 10, fill: '#848E9C' }} 
              axisLine={false}
              tickLine={false}
              minTickGap={30}
            />
            <YAxis 
              domain={[minPrice, maxPrice]} 
              orientation="right" 
              tick={{ fontSize: 10, fill: '#848E9C' }} 
              axisLine={false}
              tickLine={false}
              tickFormatter={(val) => val.toFixed(2)}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1E2026', borderColor: '#2B3139', color: '#EAECEF' }}
              itemStyle={{ fontSize: 12 }}
              labelStyle={{ color: '#848E9C', marginBottom: 5 }}
            />
            
            {/* 
              Using Bar with CustomCandle to render candlesticks.
              dataKey can be anything as CustomCandle uses the whole payload.
            */}
            <Bar 
              dataKey="close" // Dummy dataKey, actual rendering is done by CustomCandle
              shape={<CustomCandle />} 
              isAnimationActive={false}
            />
            
            {/* The Line overlay is removed as per user request */}

          </ComposedChart>
        </ResponsiveContainer>
        
        {/* Floating current price label simulation */}
        <div className="absolute top-4 left-4 bg-[#1E2026] p-2 rounded border border-[#2B3139] shadow-lg pointer-events-none opacity-80">
            <div className="flex gap-4 text-xs">
                <span className="text-[#848E9C]">O: <span className={MOCK_DATA[MOCK_DATA.length-1].open < MOCK_DATA[MOCK_DATA.length-1].close ? "text-[#0ECB81]" : "text-[#F6465D]"}>{MOCK_DATA[MOCK_DATA.length-1].open}</span></span>
                <span className="text-[#848E9C]">H: <span className={MOCK_DATA[MOCK_DATA.length-1].open < MOCK_DATA[MOCK_DATA.length-1].close ? "text-[#0ECB81]" : "text-[#F6465D]"}>{MOCK_DATA[MOCK_DATA.length-1].high}</span></span>
                <span className="text-[#848E9C]">L: <span className={MOCK_DATA[MOCK_DATA.length-1].open < MOCK_DATA[MOCK_DATA.length-1].close ? "text-[#0ECB81]" : "text-[#F6465D]"}>{MOCK_DATA[MOCK_DATA.length-1].low}</span></span>
                <span className="text-[#848E9C]">C: <span className={MOCK_DATA[MOCK_DATA.length-1].open < MOCK_DATA[MOCK_DATA.length-1].close ? "text-[#0ECB81]" : "text-[#F6465D]"}>{MOCK_DATA[MOCK_DATA.length-1].close}</span></span>
            </div>
        </div>
      </div>
    </div>
  );
};

export default Chart;