import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Order, OrderType, OrderSide, OrderStatus, TickerData, CandleData } from '../types';
import { CURRENT_TICKER as DEFAULT_TICKER } from '../constants';

const API_URL = import.meta.env.VITE_FASTAPI_URL;

interface UserBalance {
    usd: number;
    btc: number;
}

interface PlaygroundContextType {
    userBalance: UserBalance;
    orders: Order[];
    marketPrice: number;
    tickerData: TickerData;
    candleData: any[]; // Using any for the Chart formatted data for now, or proper interface
    placeOrder: (type: OrderType, side: OrderSide, amount: number, price?: number) => void;
    cancelOrder: (orderId: string) => void;
}

const PlaygroundContext = createContext<PlaygroundContextType | undefined>(undefined);

export const usePlayground = () => {
    const context = useContext(PlaygroundContext);
    if (!context) {
        throw new Error('usePlayground must be used within a PlaygroundProvider');
    }
    return context;
};

interface PlaygroundProviderProps {
    children: ReactNode;
}

export const PlaygroundProvider: React.FC<PlaygroundProviderProps> = ({ children }) => {
    // Initial state: 10,000 USD, 0 BTC
    const [userBalance, setUserBalance] = useState<UserBalance>({ usd: 10000, btc: 0 });
    const [orders, setOrders] = useState<Order[]>([]);
    const [marketPrice, setMarketPrice] = useState<number>(0);
    const [candleData, setCandleData] = useState<any[]>([]);
    const [tickerData, setTickerData] = useState<TickerData>({
        symbol: 'BTC/USDT',
        price: DEFAULT_TICKER.price,
        change24h: DEFAULT_TICKER.change24h,
        high24h: DEFAULT_TICKER.high24h,
        low24h: DEFAULT_TICKER.low24h,
        volume24h: DEFAULT_TICKER.volume24h,
        volume24hUsd: DEFAULT_TICKER.volume24h * DEFAULT_TICKER.price,
    });

    // Limit Order Execution Effect
    useEffect(() => {
        if (orders.length === 0 || marketPrice === 0) return;

        let balanceChanges = { usd: 0, btc: 0 };
        let hasChanges = false;

        const newOrders = orders.map(order => {
            if (order.status !== 'Open' || order.type !== 'Limit') return order;

            let shouldExecute = false;
            // Check condition
            if (order.side === 'Buy' && marketPrice <= order.price) {
                shouldExecute = true;
            } else if (order.side === 'Sell' && marketPrice >= order.price) {
                shouldExecute = true;
            }

            if (shouldExecute) {
                hasChanges = true;
                if (order.side === 'Buy') {
                    balanceChanges.btc += order.amount;
                } else {
                    balanceChanges.usd += order.total;
                }
                return { ...order, status: 'Filled', filled: '100.00%' } as Order;
            }
            return order;
        });

        if (hasChanges) {
            setOrders(newOrders);
            setUserBalance(prev => ({
                usd: prev.usd + balanceChanges.usd,
                btc: prev.btc + balanceChanges.btc
            }));
        }
    }, [marketPrice, orders]); // Runs whenever price updates or orders change

    // Centralized Data Fetching
    useEffect(() => {
        const fetchData = async () => {
            try {
                // Fetch Main Data
                const res = await fetch(`${API_URL}/api/data`);
                if (!res.ok) return;
                const data = await res.json();

                if (data && data.length > 0) {
                    // 1. Process Ticker Data (24h stats)
                    const last24hData = data.slice(-1440);
                    const lastCandle = last24hData[last24hData.length - 1];
                    const currentPrice = lastCandle.close;
                    const firstCandle = last24hData[0];
                    const prevPrice = firstCandle.open;
                    const change24h = ((currentPrice - prevPrice) / prevPrice) * 100;

                    let high24h = -Infinity;
                    let low24h = Infinity;
                    let volume24h = 0;
                    let volume24hUsd = 0;

                    last24hData.forEach((d: any) => {
                        if (d.high > high24h) high24h = d.high;
                        if (d.low < low24h) low24h = d.low;
                        volume24h += d.volume;
                        volume24hUsd += d.volume * d.close;
                    });

                    setTickerData({
                        symbol: 'BTC/USDT',
                        price: currentPrice,
                        change24h,
                        high24h,
                        low24h,
                        volume24h,
                        volume24hUsd
                    });

                    // Update global market price
                    setMarketPrice(currentPrice);
                    // executeLimitOrders removed; handled by Effect

                    // 2. Process Candle Data for Chart
                    const formattedData = data.map((item: any) => {
                        const horaCompleta = item.datetime.split(' ')[1];
                        return {
                            datetime: item.datetime,
                            time: horaCompleta ? horaCompleta.substring(0, 5) : item.datetime,
                            open: parseFloat(item.open) || 0,
                            close: parseFloat(item.close) || 0,
                            high: parseFloat(item.high) || 0,
                            low: parseFloat(item.low) || 0,
                        };
                    });

                    setCandleData(formattedData.filter((d: any) => d.close > 0));
                }

            } catch (error) {
                console.error("Error fetching data:", error);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []); // Only dependency is mount, essentially.

    const placeOrder = (type: OrderType, side: OrderSide, amount: number, price?: number) => {
        const executionPrice = price || marketPrice;
        const total = amount * executionPrice;

        // Validation
        if (side === 'Buy') {
            if (userBalance.usd < total) {
                alert('Insufficient USD Balance');
                return;
            }
        } else {
            if (userBalance.btc < amount) {
                alert('Insufficient BTC Balance');
                return;
            }
        }

        const newOrder: Order = {
            id: Math.random().toString(36).substr(2, 9),
            pair: 'BTC/USDT',
            type,
            side,
            price: executionPrice,
            amount,
            total,
            filled: '0.00%',
            status: 'Open',
            date: new Date().toLocaleString(),
        };

        if (type === 'Market') {
            // Find immediate execution
            newOrder.status = 'Filled';
            newOrder.filled = '100.00%';

            // Update balance immediately
            setUserBalance(prev => {
                if (side === 'Buy') {
                    return { usd: prev.usd - total, btc: prev.btc + amount };
                } else {
                    return { usd: prev.usd + total, btc: prev.btc - amount };
                }
            });
        } else {
            // Limit Order
            // Hold funds
            setUserBalance(prev => {
                if (side === 'Buy') {
                    return { ...prev, usd: prev.usd - total };
                } else {
                    return { ...prev, btc: prev.btc - amount };
                }
            });
        }

        setOrders(prev => [newOrder, ...prev]);
    };

    const cancelOrder = (orderId: string) => {
        const target = orders.find(o => o.id === orderId);
        if (!target || target.status !== 'Open') return;

        // Refund held funds
        setUserBalance(balance => {
            if (target.side === 'Buy') {
                return { ...balance, usd: balance.usd + target.total };
            } else {
                return { ...balance, btc: balance.btc + target.amount };
            }
        });

        setOrders(prev => prev.map(o => o.id === orderId ? { ...o, status: 'Canceled' } as Order : o));
    };

    return (
        <PlaygroundContext.Provider value={{ userBalance, orders, marketPrice, tickerData, candleData, placeOrder, cancelOrder }}>
            {children}
        </PlaygroundContext.Provider>
    );
};
