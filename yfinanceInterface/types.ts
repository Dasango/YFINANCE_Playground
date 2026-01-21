export interface CandleData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface Order {
  id: string;
  pair: string;
  type: 'Limit' | 'Market';
  side: 'Buy' | 'Sell';
  price: number;
  amount: number;
  total: number;
  filled: string;
  status: 'Open' | 'Filled' | 'Canceled';
  date: string;
}

export enum TradeTab {
  OPEN_ORDERS = 'Órdenes abiertas(1)',
  ORDER_HISTORY = 'Historial de órdenes',
  TRADE_HISTORY = 'Historial de operaciones',
  HOLDINGS = 'Holdings'
}