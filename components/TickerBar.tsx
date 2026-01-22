import React, { useState } from 'react';
import { CURRENT_TICKER } from '../constants';
import MiniPredictionChart from './MiniPredictionChart';

// Simulación de los tickers futuros
const AVAILABLE_TICKERS = ['TSLA', 'ETH', 'GOOGL', 'BTC'];

const TickerBar: React.FC = () => {
  // Estado para controlar si el menú se muestra o no
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const isPositive = CURRENT_TICKER.change24h >= 0;
  const colorClass = isPositive ? 'text-[#0ECB81]' : 'text-[#F6465D]';

  // Función para manejar el clic en una opción (aquí pondrías la lógica futura de cambio)
  const handleSelectTicker = (ticker: string) => {
    console.log(`Cambiando a: ${ticker}`);
    setIsMenuOpen(false); // Cerrar menú al seleccionar
    // Aquí llamarías a una función para actualizar el CURRENT_TICKER globalmente
  };

  return (
    <div className="flex flex-wrap items-center gap-6 px-4 py-3 bg-[#161A1E] border-b border-[#2B3139]">

      {/* SECCIÓN DEL TICKER CON DROPDOWN */}
      <div className="flex flex-col relative"> {/* 'relative' es clave para el menú */}
        <div
          className="flex items-center gap-2 cursor-pointer group"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
        >
          <h2 className="text-xl font-bold text-[#EAECEF] group-hover:text-[#FCD535] transition-colors">
            {CURRENT_TICKER.symbol}
          </h2>
          {/* Triangulito indicador (opcional pero recomendado) */}
          <span className={`text-[10px] text-[#848E9C] transition-transform ${isMenuOpen ? 'rotate-180' : ''}`}>▼</span>
        </div>

        {/* MENÚ DESPLEGABLE */}
        {isMenuOpen && (
          <div className="absolute top-full left-0 mt-2 w-32 bg-[#2B3139] rounded shadow-lg z-50 overflow-hidden border border-[#474D57]">
            {AVAILABLE_TICKERS.map((ticker) => (
              <div
                key={ticker}
                className="px-4 py-2 text-sm text-[#EAECEF] hover:bg-[#161A1E] cursor-pointer transition-colors"
                onClick={() => handleSelectTicker(ticker)}
              >
                {ticker}
              </div>
            ))}
          </div>
        )}

        <span className="text-xs text-[#848E9C] underline cursor-pointer">Bitcoin Price</span>
      </div>

      {/* RESTO DE LOS DATOS (Sin cambios) */}
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

      {/* Mini Chart al fondo */}
      <div className="ml-auto">
        <MiniPredictionChart />
      </div>
    </div>
  );
};

export default TickerBar;