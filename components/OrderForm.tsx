import React, { useState, useEffect } from 'react';
import { Info } from 'lucide-react';
import { usePlayground } from '../context/PlaygroundContext';
import { OrderType } from '../types';

const InputField = ({ label, suffix, value, onChange }: any) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    // Allow digits, one dot, or one comma. 
    // Simple regex for "starts with digits/dots/commas" to avoid letters.
    // We won't be too strict on multiple dots/commas while typing to avoid annoyance, 
    // but cleaning it up on blur would be better. For now, just block letters.
    if (/^[0-9.,]*$/.test(val)) {
      onChange(val);
    }
  };

  return (
    <div className="mb-3">
      <div className="flex justify-between mb-1">
        <label className="text-xs text-[#848E9C]">{label}</label>
      </div>
      <div className="relative flex items-center bg-[#2B3139] rounded hover:border-[#FCD535] border border-transparent transition-colors">
        <input
          type="text"
          value={value}
          onChange={handleChange}
          className="w-full bg-transparent text-sm text-[#EAECEF] p-2 outline-none text-right font-medium"
        />
        <span className="text-xs text-[#848E9C] pr-2 absolute left-2 pointer-events-none">{label === 'Price' ? '' : ''}</span>
        <span className="text-xs text-[#848E9C] pr-2 uppercase">{suffix}</span>
      </div>
    </div>
  );
};

const OrderForm: React.FC = () => {
  const { userBalance, marketPrice, placeOrder } = usePlayground();
  const [orderType, setOrderType] = useState<OrderType>('Limit');

  // Buy Form State
  const [buyPrice, setBuyPrice] = useState<string>('');
  const [buyAmount, setBuyAmount] = useState<string>('');

  // Sell Form State
  const [sellPrice, setSellPrice] = useState<string>('');
  const [sellAmount, setSellAmount] = useState<string>('');

  // Update price inputs when market price changes if they are empty (optional, good UX)
  useEffect(() => {
    if (marketPrice > 0) {
      if (!buyPrice) setBuyPrice(marketPrice.toFixed(2));
      if (!sellPrice) setSellPrice(marketPrice.toFixed(2));
    }
  }, [marketPrice]);

  const handleBuy = () => {
    const amount = parseFloat(buyAmount.replace(',', '.'));
    const price = orderType === 'Limit' ? parseFloat(buyPrice.replace(',', '.')) : marketPrice;

    if (!amount || (orderType === 'Limit' && !price)) return;

    placeOrder(orderType, 'Buy', amount, price);
    // Reset amount only?
    setBuyAmount('');
  };

  const handleSell = () => {
    const amount = parseFloat(sellAmount.replace(',', '.'));
    const price = orderType === 'Limit' ? parseFloat(sellPrice.replace(',', '.')) : marketPrice;

    if (!amount || (orderType === 'Limit' && !price)) return;

    placeOrder(orderType, 'Sell', amount, price);
    setSellAmount('');
  };



  return (
    <div className="bg-[#161A1E] flex flex-col min-w-[320px]">
      {/* Tabs */}
      <div className="flex items-center gap-4 px-4 pt-3 pb-2">
        <button
          className={`text-sm font-medium transition-colors ${orderType === 'Limit' ? 'text-[#FCD535]' : 'text-[#EAECEF] hover:text-[#FCD535]'}`}
          onClick={() => setOrderType('Limit')}
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
      <div className="grid grid-cols-2 gap-4 px-4 pb-4">
        {/* Buy Side */}
        <div className="flex flex-col">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs text-[#848E9C]">Avbl</span>
            <span className="text-xs text-[#EAECEF] font-medium">{userBalance.usd.toLocaleString('en-US', { minimumFractionDigits: 2 })} USDT</span>
          </div>

          {orderType === 'Limit' && (
            <InputField label="Price" suffix="USDT" value={buyPrice} onChange={setBuyPrice} />
          )}
          {orderType === 'Market' && (
            <div className="mb-3 bg-[#2B3139] rounded p-2 text-xs text-[#EAECEF] text-center font-medium">
              Market Price: ≈ {marketPrice.toLocaleString('en-US', { minimumFractionDigits: 2 })} USDT
            </div>
          )}

          <InputField label="Amount" suffix="BTC" value={buyAmount} onChange={setBuyAmount} />

          <div className="mb-4">
            <input type="range" className="w-full h-1 bg-[#2B3139] rounded-lg appearance-none cursor-pointer accent-[#EAECEF]" />
          </div>

          {orderType === 'Limit' && (
            <InputField label="Total" suffix="USDT" value={buyAmount && buyPrice ? (parseFloat(buyAmount.replace(',', '.')) * parseFloat(buyPrice.replace(',', '.'))).toFixed(2) : ''} onChange={() => { }} />
          )}

          <button
            onClick={handleBuy}
            className="w-full py-2.5 mt-4 bg-[#0ECB81] hover:bg-[#0ECB81]/90 text-white text-sm font-bold rounded transition-colors">
            Buy BTC
          </button>
        </div>

        {/* Sell Side */}
        <div className="flex flex-col">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs text-[#848E9C]">Avbl</span>
            <span className="text-xs text-[#EAECEF] font-medium">{userBalance.btc.toFixed(6)} BTC</span>
          </div>

          {orderType === 'Limit' && (
            <InputField label="Price" suffix="USDT" value={sellPrice} onChange={setSellPrice} />
          )}
          {orderType === 'Market' && (
            <div className="mb-3 bg-[#2B3139] rounded p-2 text-xs text-[#EAECEF] text-center font-medium">
              Market Price: ≈ {marketPrice.toLocaleString('en-US', { minimumFractionDigits: 2 })} USDT
            </div>
          )}

          <InputField label="Amount" suffix="BTC" value={sellAmount} onChange={setSellAmount} />

          <div className="mb-4">
            <input type="range" className="w-full h-1 bg-[#2B3139] rounded-lg appearance-none cursor-pointer accent-[#EAECEF]" />
          </div>

          {orderType === 'Limit' && (
            <InputField label="Total" suffix="USDT" value={sellAmount && sellPrice ? (parseFloat(sellAmount.replace(',', '.')) * parseFloat(sellPrice.replace(',', '.'))).toFixed(2) : ''} onChange={() => { }} />
          )}

          <button
            onClick={handleSell}
            className="w-full py-2.5 mt-4 bg-[#F6465D] hover:bg-[#F6465D]/90 text-white text-sm font-bold rounded transition-colors">
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