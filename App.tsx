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

      {/* Main Content Area */}
      <div className="flex flex-1 min-h-0 overflow-y-auto lg:overflow-hidden flex-col lg:flex-row">

        {/* Left Column: Chart + Tabs */}
        {/* Mobile: h-auto (scrolls with parent), Desktop: h-full (constrained) */}
        <div className="flex flex-col flex-1 lg:h-full lg:min-h-0 border-r border-[#2B3139]">

          {/* Chart Container */}
          {/* Mobile: Fixed height, Desktop: Flexible 3/5 */}
          <div className="h-[450px] shrink-0 border-b border-[#2B3139] relative lg:h-auto lg:flex-[3] lg:min-h-0">
            <Chart />
          </div>

          {/* Tabs Container */}
          {/* Mobile: Fixed min-height, Desktop: Flexible 2/5 */}
          <div className="min-h-[400px] bg-[#161A1E] lg:h-auto lg:flex-[2] lg:min-h-0 lg:overflow-y-auto">
            <UserTabs />
          </div>
        </div>

        {/* Right Column: Order Form (Desktop Only) */}
        <div className="hidden lg:block w-[320px] h-full overflow-y-auto border-l border-[#2B3139]">
          <OrderForm />
        </div>

        {/* Mobile Order Form Spacer (optional, if needed to prevent overlap with sticky bottom) */}
        <div className="lg:hidden h-[100px] w-full"></div>
      </div>

      {/* Mobile Sticky Order Form */}
      <div className="lg:hidden block p-4 bg-[#1e2329] border-t border-[#2B3139] sticky bottom-0 z-10">
        <OrderForm />
      </div>
    </div>
  );
};

export default App;