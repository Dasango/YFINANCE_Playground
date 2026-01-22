import React from 'react';
import Header from './components/Header';
import TickerBar from './components/TickerBar';
import Chart from './components/Chart';
import OrderForm from './components/OrderForm';
import MiniPredictionChart from './components/MiniPredictionChart';
import UserTabs from './components/UserTabs';

const App: React.FC = () => {
  return (
    <div className="flex flex-col lg:h-screen w-full bg-[#161A1E] text-[#EAECEF] font-sans">
      <Header />
      <TickerBar />

      {/* Main Content Area */}
      {/* Mobile: default flow (no h-screen restriction), Desktop: flex row with hidden overflow */}
      <div className="flex flex-1 min-h-0 overflow-y-auto lg:overflow-hidden flex-col lg:flex-row">

        {/* Left Column: Chart + Tabs */}
        {/* Mobile: auto height, Desktop: full height constrained */}
        <div className="flex flex-col flex-1 lg:h-full lg:min-h-0 border-r border-[#2B3139]">

          {/* Chart Container */}
          {/* Mobile: Fixed height, Desktop: Flexible 3/5. Added z-0 and overflow-hidden */}
          <div className="h-[450px] shrink-0 border-b border-[#2B3139] relative lg:h-auto lg:flex-[3] lg:min-h-0 z-0 overflow-hidden">
            <Chart />
          </div>

          {/* Tabs Container */}
          {/* Mobile: Min height, Desktop: Flexible 2/5. Added z-10 for interactivity */}
          <div className="min-h-[400px] bg-[#161A1E] relative lg:h-auto lg:flex-[2] lg:min-h-0 lg:overflow-y-auto z-10">
            <UserTabs />
          </div>

          {/* Mobile Order Form: Flows naturally after tabs */}
          <div className="lg:hidden p-4 border-t border-[#2B3139]">
            <div className="flex justify-center mb-4">
              <MiniPredictionChart />
            </div>
            <OrderForm />
          </div>
        </div>

        {/* Right Column: Order Form (Desktop Only) */}
        <div className="hidden lg:block w-[320px] h-full overflow-y-auto border-l border-[#2B3139]">
          <div className="flex justify-center py-4 border-b border-[#2B3139]">
            <MiniPredictionChart />
          </div>
          <OrderForm />
        </div>
      </div>
    </div>
  );
};

export default App;