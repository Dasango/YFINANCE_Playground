export type OrderType = 'Limit' | 'Market';
export type OrderSide = 'Buy' | 'Sell';
export type OrderStatus = 'Open' | 'Filled' | 'Canceled';

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
  type: OrderType;
  side: OrderSide;
  price: number;
  amount: number;
  total: number;
  filled: string;
  status: OrderStatus;
  date: string;
}

export enum TradeTab {
  OPEN_ORDERS = 'Órdenes abiertas',
  ORDER_HISTORY = 'Historial de órdenes',
  TRADE_HISTORY = 'Historial de operaciones',
  HOLDINGS = 'Holdings'
}