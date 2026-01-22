import React, { useState, useEffect } from 'react';
import { usePlayground } from '../context/PlaygroundContext';
import { CURRENT_TICKER as DEFAULT_TICKER } from '../constants';

// Simulación de los tickers futuros
const AVAILABLE_TICKERS = ['TSLA', 'ETH', 'GOOGL', 'BTC'];
const API_URL = import.meta.env.VITE_FASTAPI_URL;

interface TickerData {
  symbol: string;
  price: number;
  change24h: number;
  high24h: number;
  low24h: number;
  volume24h: number;
  volume24hUsd: number;
}

const TickerBar: React.FC = () => {
  // Estado para controlar si el menú se muestra o no
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { tickerData } = usePlayground();

  const isPositive = tickerData.change24h >= 0;
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
            {tickerData.symbol}
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
          {tickerData.price.toLocaleString('en-US', { minimumFractionDigits: 2 })}
        </span>
        <span className="text-xs text-[#EAECEF]">${tickerData.price.toLocaleString()}</span>
      </div>

      <div className="flex flex-col">
        <span className="text-xs text-[#848E9C]">24h Change</span>
        <span className={`text-xs font-medium ${colorClass}`}>
          {tickerData.change24h > 0 ? '+' : ''}{tickerData.change24h.toFixed(2)}%
        </span>
      </div>

      <div className="flex flex-col">
        <span className="text-xs text-[#848E9C]">24h High</span>
        <span className="text-xs text-[#EAECEF]">{tickerData.high24h.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
      </div>

      <div className="flex flex-col">
        <span className="text-xs text-[#848E9C]">24h Low</span>
        <span className="text-xs text-[#EAECEF]">{tickerData.low24h.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
      </div>

      <div className="flex flex-col">
        <span className="text-xs text-[#848E9C]">24h Volume(BTC)</span>
        <span className="text-xs text-[#EAECEF]">{tickerData.volume24h.toLocaleString('en-US', { maximumFractionDigits: 2 })}</span>
      </div>

      <div className="flex flex-col">
        <span className="text-xs text-[#848E9C]">24h Volume(USDT)</span>
        <span className="text-xs text-[#EAECEF]">{(tickerData.volume24hUsd / 1000000).toFixed(2)}M</span>
      </div>
    </div>
  );
};

export default TickerBar;