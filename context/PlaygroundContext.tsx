import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Order, OrderType, OrderSide, OrderStatus } from '../types';

interface UserBalance {
    usd: number;
    btc: number;
}

interface PlaygroundContextType {
    userBalance: UserBalance;
    orders: Order[];
    marketPrice: number;
    placeOrder: (type: OrderType, side: OrderSide, amount: number, price?: number) => void;
    cancelOrder: (orderId: string) => void;
    updateMarketPrice: (price: number) => void;
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

    // Update market price and check for limit order executions
    const executeLimitOrders = (currentPrice: number) => {
        setOrders(prevOrders => {
            let balanceChanges = { usd: 0, btc: 0 };

            const newOrders = prevOrders.map(order => {
                if (order.status !== 'Open' || order.type !== 'Limit') return order;

                let shouldExecute = false;
                if (order.side === 'Buy' && currentPrice <= order.price) {
                    shouldExecute = true;
                } else if (order.side === 'Sell' && currentPrice >= order.price) {
                    shouldExecute = true;
                }

                if (shouldExecute) {
                    if (order.side === 'Buy') {
                        balanceChanges.btc += order.amount;
                    } else {
                        balanceChanges.usd += order.total;
                    }

                    return { ...order, status: 'Filled', filled: '100.00%' } as Order;
                }
                return order;
            });

            if (balanceChanges.usd !== 0 || balanceChanges.btc !== 0) {
                setUserBalance(prev => ({
                    usd: prev.usd + balanceChanges.usd,
                    btc: prev.btc + balanceChanges.btc
                }));
            }

            return newOrders;
        });
    };

    const updateMarketPrice = (price: number) => {
        setMarketPrice(price);
        executeLimitOrders(price);
    };

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
        setOrders(prev => {
            const target = prev.find(o => o.id === orderId);
            if (!target || target.status !== 'Open') return prev;

            // Refund held funds
            setUserBalance(balance => {
                if (target.side === 'Buy') {
                    return { ...balance, usd: balance.usd + target.total };
                } else {
                    return { ...balance, btc: balance.btc + target.amount };
                }
            });

            return prev.map(o => o.id === orderId ? { ...o, status: 'Canceled' } as Order : o);
        });
    };

    return (
        <PlaygroundContext.Provider value={{ userBalance, orders, marketPrice, placeOrder, cancelOrder, updateMarketPrice }}>
            {children}
        </PlaygroundContext.Provider>
    );
};
