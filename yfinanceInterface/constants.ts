import { CandleData, Order } from './types';

// Hardcoded API data generator to simulate "Real" market movements
const generateData = (): CandleData[] => {
  const data: CandleData[] = [];
  let price = 42000;
  const now = new Date();
  
  for (let i = 0; i < 100; i++) {
    const time = new Date(now.getTime() - (100 - i) * 15 * 60000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const volatility = Math.random() * 200;
    const change = (Math.random() - 0.5) * volatility;
    
    const open = price;
    const close = price + change;
    const high = Math.max(open, close) + Math.random() * 50;
    const low = Math.min(open, close) - Math.random() * 50;
    const volume = Math.floor(Math.random() * 1000) + 100;

    data.push({
      time,
      open: Number(open.toFixed(2)),
      high: Number(high.toFixed(2)),
      low: Number(low.toFixed(2)),
      close: Number(close.toFixed(2)),
      volume
    });
    price = close;
  }
  return data;
};

export const MOCK_DATA = generateData();

export const CURRENT_TICKER = {
  symbol: 'BTC/USDT',
  price: MOCK_DATA[MOCK_DATA.length - 1].close,
  change24h: 2.45,
  high24h: 43500.00,
  low24h: 41200.00,
  volume24h: 4520.12
};

export const MOCK_ORDERS: Order[] = [
  {
    id: '1',
    pair: 'BTC/USDT',
    type: 'Limit',
    side: 'Buy',
    price: 41500,
    amount: 0.5,
    total: 20750,
    filled: '0.00%',
    status: 'Open',
    date: '2023-10-27 14:30'
  },
  {
    id: '2',
    pair: 'BTC/USDT',
    type: 'Market',
    side: 'Sell',
    price: 42100,
    amount: 0.1,
    total: 4210,
    filled: '100.00%',
    status: 'Filled',
    date: '2023-10-26 09:15'
  }
];