import React, { useState } from 'react';
import { Info } from 'lucide-react';
import { CURRENT_TICKER } from '../constants';

const OrderForm: React.FC = () => {
  const [orderType, setOrderType] = useState<'Limit' | 'Market'>('Limit');
  const [buyPrice, setBuyPrice] = useState<string>(CURRENT_TICKER.price.toString());
  const [buyAmount, setBuyAmount] = useState<string>('');
  const [sellPrice, setSellPrice] = useState<string>(CURRENT_TICKER.price.toString());
  const [sellAmount, setSellAmount] = useState<string>('');

  const InputField = ({ label, suffix, value, onChange }: any) => (
    <div className="mb-3">
      <div className="flex justify-between mb-1">
        <label className="text-xs text-[#848E9C]">{label}</label>
      </div>
      <div className="relative flex items-center bg-[#2B3139] rounded hover:border-[#FCD535] border border-transparent transition-colors">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full bg-transparent text-sm text-[#EAECEF] p-2 outline-none text-right font-medium"
        />
        <span className="text-xs text-[#848E9C] pr-2 absolute left-2 pointer-events-none">{label === 'Price' ? '' : ''}</span>
        <span className="text-xs text-[#848E9C] pr-2 uppercase">{suffix}</span>
      </div>
    </div>
  );

  return (
    <div className="bg-[#161A1E] h-full flex flex-col border-l border-[#2B3139] min-w-[320px]">
      {/* Tabs */}
      <div className="flex items-center gap-4 px-4 pt-3 pb-2">
        <button
          // Fix: Change 'Spot' to 'Limit' to correctly highlight the button when orderType is 'Limit'
          className={`text-sm font-medium transition-colors ${orderType === 'Limit' ? 'text-[#FCD535]' : 'text-[#EAECEF] hover:text-[#FCD535]'}`}
          onClick={() => setOrderType('Limit')} // Dummy for visual
        >
          Spot
        </button>
      </div>

      <div className="flex items-center gap-2 px-4 mb-4">
        <button
          onClick={() => setOrderType('Limit')}
          className={`text-xs px-3 py-1 rounded-full transition-colors ${orderType === 'Limit' ? 'bg-[#2B3139] text-[#FCD535]' : 'text-[#848E9C] hover:text-[#EAECEF]'}`}
        >
          Limit
        </button>
        <button
          onClick={() => setOrderType('Market')}
          className={`text-xs px-3 py-1 rounded-full transition-colors ${orderType === 'Market' ? 'bg-[#2B3139] text-[#FCD535]' : 'text-[#848E9C] hover:text-[#EAECEF]'}`}
        >
          Market
        </button>
        <Info className="w-3 h-3 text-[#848E9C] ml-auto" />
      </div>

      {/* Forms Grid */}
      <div className="grid grid-cols-2 gap-4 px-4 flex-1 overflow-y-auto">
        {/* Buy Side */}
        <div className="flex flex-col">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs text-[#848E9C]">Avbl</span>
            <span className="text-xs text-[#EAECEF] font-medium">1,240.50 USDT</span>
          </div>

          {orderType === 'Limit' && (
            <InputField label="Price" suffix="USDT" value={buyPrice} onChange={setBuyPrice} />
          )}
          {orderType === 'Market' && (
            <div className="mb-3 bg-[#2B3139] rounded p-2 text-xs text-[#848E9C] text-center italic">
              Market Price
            </div>
          )}

          <InputField label="Amount" suffix="BTC" value={buyAmount} onChange={setBuyAmount} />

          <div className="mb-4">
            <input type="range" className="w-full h-1 bg-[#2B3139] rounded-lg appearance-none cursor-pointer accent-[#EAECEF]" />
          </div>

          {orderType === 'Limit' && (
            <InputField label="Total" suffix="USDT" value={buyAmount && buyPrice ? (parseFloat(buyAmount) * parseFloat(buyPrice)).toFixed(2) : ''} onChange={() => { }} />
          )}

          <button className="w-full py-2.5 mt-auto bg-[#0ECB81] hover:bg-[#0ECB81]/90 text-white text-sm font-bold rounded transition-colors">
            Buy BTC
          </button>
        </div>

        {/* Sell Side */}
        <div className="flex flex-col">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs text-[#848E9C]">Avbl</span>
            <span className="text-xs text-[#EAECEF] font-medium">0.024 BTC</span>
          </div>

          {orderType === 'Limit' && (
            <InputField label="Price" suffix="USDT" value={sellPrice} onChange={setSellPrice} />
          )}
          {orderType === 'Market' && (
            <div className="mb-3 bg-[#2B3139] rounded p-2 text-xs text-[#848E9C] text-center italic">
              Market Price
            </div>
          )}

          <InputField label="Amount" suffix="BTC" value={sellAmount} onChange={setSellAmount} />

          <div className="mb-4">
            <input type="range" className="w-full h-1 bg-[#2B3139] rounded-lg appearance-none cursor-pointer accent-[#EAECEF]" />
          </div>

          {orderType === 'Limit' && (
            <InputField label="Total" suffix="USDT" value={sellAmount && sellPrice ? (parseFloat(sellAmount) * parseFloat(sellPrice)).toFixed(2) : ''} onChange={() => { }} />
          )}

          <button className="w-full py-2.5 mt-auto bg-[#F6465D] hover:bg-[#F6465D]/90 text-white text-sm font-bold rounded transition-colors">
            Sell BTC
          </button>
        </div>
      </div>

      <div className="p-4 mt-2 border-t border-[#2B3139]">
        <div className="flex justify-between text-xs text-[#848E9C] mb-1">
          <span>Open Orders (0)</span>
          <span>Funds</span>
        </div>
      </div>
    </div>
  );
};

export default OrderForm;