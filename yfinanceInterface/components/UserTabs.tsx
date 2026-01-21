import React, { useState } from 'react';
import { TradeTab, Order } from '../types';
import { MOCK_ORDERS } from '../constants';

const UserTabs: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TradeTab>(TradeTab.OPEN_ORDERS);

  return (
    <div className="bg-[#161A1E] w-full flex flex-col border-t border-[#2B3139] h-full min-h-[250px]">
      <div className="flex items-center gap-6 px-4 border-b border-[#2B3139]">
        {Object.values(TradeTab).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`text-sm font-medium py-3 border-b-2 transition-colors ${
              activeTab === tab
                ? 'text-[#FCD535] border-[#FCD535]'
                : 'text-[#848E9C] border-transparent hover:text-[#EAECEF]'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto p-4">
        {activeTab === TradeTab.OPEN_ORDERS && (
          <div className="w-full text-left">
            <div className="grid grid-cols-8 text-xs text-[#848E9C] mb-3 px-2">
              <span>Date</span>
              <span>Pair</span>
              <span>Type</span>
              <span>Side</span>
              <span>Price</span>
              <span>Amount</span>
              <span>Filled</span>
              <span>Total</span>
            </div>
            {MOCK_ORDERS.filter(o => o.status === 'Open').map((order) => (
              <div key={order.id} className="grid grid-cols-8 text-xs text-[#EAECEF] py-2 hover:bg-[#2B3139] rounded px-2">
                <span className="text-[#848E9C]">{order.date}</span>
                <span className="font-medium">{order.pair}</span>
                <span>{order.type}</span>
                <span className={order.side === 'Buy' ? 'text-[#0ECB81]' : 'text-[#F6465D]'}>{order.side}</span>
                <span>{order.price.toLocaleString()}</span>
                <span>{order.amount}</span>
                <span>{order.filled}</span>
                <span>{order.total.toLocaleString()}</span>
              </div>
            ))}
             {MOCK_ORDERS.filter(o => o.status === 'Open').length === 0 && (
                <div className="flex items-center justify-center h-20 text-xs text-[#848E9C]">
                    No open orders
                </div>
             )}
          </div>
        )}

        {activeTab !== TradeTab.OPEN_ORDERS && (
          <div className="flex items-center justify-center h-full text-[#848E9C] text-sm">
             <div className="flex flex-col items-center gap-2">
                 <span className="opacity-50">No Data Available</span>
             </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserTabs;