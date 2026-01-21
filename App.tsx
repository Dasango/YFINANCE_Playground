import React from 'react';
import Header from './components/Header';
import TickerBar from './components/TickerBar';
import Chart from './components/Chart';
import OrderForm from './components/OrderForm';
import UserTabs from './components/UserTabs';

const App: React.FC = () => {
  return (
    <div className="flex flex-col h-screen w-full bg-[#161A1E] text-[#EAECEF] overflow-hidden font-sans">
      <Header />
      <TickerBar />

      {/* 1. Main Content: Quitamos el scroll de aquí para que el flex funcione */}
      <div className="flex flex-1 min-h-0 overflow-hidden">

        {/* 2. Left Column: Cambiamos a h-full y min-h-0 */}
        <div className="flex flex-col flex-1 h-full min-h-0 border-r border-[#2B3139]">

          {/* Chart: Flex 3, pero permitimos que se achique con min-h-0 */}
          <div className="flex-[3] min-h-0 border-b border-[#2B3139] relative">
            <Chart />
          </div>

          {/* Tabs: Flex 2, con su propio scroll interno si es necesario */}
          <div className="flex-[2] min-h-0 overflow-y-auto">
            <UserTabs />
          </div>
        </div>

        {/* 3. Right Column: Order Form Desktop */}
        <div className="w-[320px] hidden lg:block h-full overflow-y-auto border-l border-[#2B3139]">
          <OrderForm />
        </div>
      </div>

      {/* 4. Mobile Only: Fuera del área de scroll principal o como un sticky bottom */}
      <div className="lg:hidden block p-4 bg-[#1e2329] border-t border-[#2B3139]">
        <OrderForm />
      </div>
    </div>
  );
};

export default App;