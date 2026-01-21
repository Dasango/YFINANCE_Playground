import React from 'react';
import { CURRENT_TICKER } from '../constants';

const TickerBar: React.FC = () => {
  const isPositive = CURRENT_TICKER.change24h >= 0;
  const colorClass = isPositive ? 'text-[#0ECB81]' : 'text-[#F6465D]';

  return (
    <div className="flex flex-wrap items-center gap-6 px-4 py-3 bg-[#161A1E] border-b border-[#2B3139]">
      <div className="flex flex-col">
        <h2 className="text-xl font-bold text-[#EAECEF]">{CURRENT_TICKER.symbol}</h2>
        <span className="text-xs text-[#848E9C] underline cursor-pointer">Bitcoin Price</span>
      </div>

      <div className="flex flex-col">
        <span className={`text-lg font-medium ${colorClass}`}>
            {CURRENT_TICKER.price.toLocaleString('en-US', { minimumFractionDigits: 2 })}
        </span>
        <span className="text-xs text-[#EAECEF]">${CURRENT_TICKER.price.toLocaleString()}</span>
      </div>

      <div className="flex flex-col">
        <span className="text-xs text-[#848E9C]">24h Change</span>
        <span className={`text-xs font-medium ${colorClass}`}>
          {CURRENT_TICKER.change24h}%
        </span>
      </div>

      <div className="flex flex-col">
        <span className="text-xs text-[#848E9C]">24h High</span>
        <span className="text-xs text-[#EAECEF]">{CURRENT_TICKER.high24h.toLocaleString()}</span>
      </div>

      <div className="flex flex-col">
        <span className="text-xs text-[#848E9C]">24h Low</span>
        <span className="text-xs text-[#EAECEF]">{CURRENT_TICKER.low24h.toLocaleString()}</span>
      </div>

      <div className="flex flex-col">
        <span className="text-xs text-[#848E9C]">24h Volume(BTC)</span>
        <span className="text-xs text-[#EAECEF]">{CURRENT_TICKER.volume24h.toLocaleString()}</span>
      </div>
       <div className="flex flex-col">
        <span className="text-xs text-[#848E9C]">24h Volume(USDT)</span>
        <span className="text-xs text-[#EAECEF]">{(CURRENT_TICKER.volume24h * CURRENT_TICKER.price / 1000000).toFixed(2)}M</span>
      </div>
    </div>
  );
};

export default TickerBar;