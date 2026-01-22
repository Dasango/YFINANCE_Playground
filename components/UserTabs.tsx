import React, { useState } from 'react';
import { TradeTab } from '../types';
import { usePlayground } from '../context/PlaygroundContext';

const UserTabs: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TradeTab>(TradeTab.OPEN_ORDERS);
  const { orders, userBalance, cancelOrder } = usePlayground();

  const getFilteredOrders = () => {
    switch (activeTab) {
      case TradeTab.OPEN_ORDERS:
        return orders.filter(o => o.status === 'Open');
      case TradeTab.ORDER_HISTORY:
        return orders.filter(o => o.status === 'Filled');
      case TradeTab.TRADE_HISTORY:
        return orders; // All operations
      default:
        return [];
    }
  };

  const filteredOrders = getFilteredOrders();

  const renderTable = (showAction = false) => (
    <div className="w-full text-left">
      <div className="grid grid-cols-9 text-xs text-[#848E9C] mb-3 px-2">
        <span>Date</span>
        <span>Pair</span>
        <span>Type</span>
        <span>Side</span>
        <span>Price</span>
        <span>Amount</span>
        <span>Filled</span>
        <span>Total</span>
        {showAction && <span>Action</span>}
      </div>
      {filteredOrders.map((order) => (
        <div key={order.id} className="grid grid-cols-9 text-xs text-[#EAECEF] py-2 hover:bg-[#2B3139] rounded px-2 items-center">
          <span className="text-[#848E9C] whitespace-nowrap overflow-hidden text-ellipsis">{order.date}</span>
          <span className="font-medium">{order.pair}</span>
          <span>{order.type}</span>
          <span className={order.side === 'Buy' ? 'text-[#0ECB81]' : 'text-[#F6465D]'}>{order.side}</span>
          <span>{order.price.toLocaleString()}</span>
          <span>{order.amount}</span>
          <span>{order.filled}</span>
          <span>{order.total.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
          {showAction && (
            <span>
              <button
                onClick={() => cancelOrder(order.id)}
                className="text-[#F6465D] hover:underline"
              >
                Cancel
              </button>
            </span>
          )}
        </div>
      ))}
      {filteredOrders.length === 0 && (
        <div className="flex items-center justify-center h-20 text-xs text-[#848E9C]">
          No data
        </div>
      )}
    </div>
  );

  return (
    <div className="bg-[#161A1E] w-full flex flex-col border-t border-[#2B3139] h-full min-h-[250px]">
      <div className="flex items-center gap-6 px-4 border-b border-[#2B3139] overflow-x-auto">
        {Object.values(TradeTab).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`text-sm font-medium py-3 border-b-2 transition-colors whitespace-nowrap ${activeTab === tab
                ? 'text-[#FCD535] border-[#FCD535]'
                : 'text-[#848E9C] border-transparent hover:text-[#EAECEF]'
              }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto p-4 max-h-[400px]">
        {activeTab === TradeTab.HOLDINGS ? (
          <div className="flex flex-col gap-4">
            <div className="flex justify-between items-center p-3 bg-[#2B3139] rounded">
              <span className="text-[#848E9C] text-sm">USDT Balance</span>
              <span className="text-[#EAECEF] font-bold text-lg">{userBalance.usd.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-[#2B3139] rounded">
              <span className="text-[#848E9C] text-sm">BTC Balance</span>
              <span className="text-[#EAECEF] font-bold text-lg">{userBalance.btc.toFixed(6)}</span>
            </div>
          </div>
        ) : (
          renderTable(activeTab === TradeTab.OPEN_ORDERS)
        )}
      </div>
    </div>
  );
};

export default UserTabs;