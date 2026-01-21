import React from 'react';
import { LayoutGrid, Globe, Settings, Bell, User } from 'lucide-react';

const Header: React.FC = () => {
  return (
    <header className="flex items-center justify-between px-4 py-3 bg-[#1E2026] border-b border-[#2B3139] text-[#EAECEF]">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
           <div className="w-8 h-8 bg-[#FCD535] rounded-full flex items-center justify-center">
             <LayoutGrid className="text-black w-5 h-5" />
           </div>
           <h1 className="text-xl font-bold tracking-tight text-[#FCD535]">BINANCE</h1>
        </div>
        <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
          <a href="#" className="hover:text-[#FCD535] transition-colors">Markets</a>
          <a href="#" className="text-[#FCD535]">Trade</a>
          <a href="#" className="hover:text-[#FCD535] transition-colors">Derivatives</a>
          <a href="#" className="hover:text-[#FCD535] transition-colors">Earn</a>
          <a href="#" className="hover:text-[#FCD535] transition-colors">Finance</a>
        </nav>
      </div>
      
      <div className="flex items-center gap-4 text-[#848E9C]">
        <Globe className="w-5 h-5 cursor-pointer hover:text-[#EAECEF]" />
        <Settings className="w-5 h-5 cursor-pointer hover:text-[#EAECEF]" />
        <Bell className="w-5 h-5 cursor-pointer hover:text-[#EAECEF]" />
        <User className="w-5 h-5 cursor-pointer hover:text-[#EAECEF]" />
      </div>
    </header>
  );
};

export default Header;