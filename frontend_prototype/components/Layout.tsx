import React, { useState } from 'react';
import { LayoutDashboard, LineChart, FileText, Settings, Car, Bell, Search, User, MapPin, ChevronDown, ChevronUp, Sliders } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { useAppContext, USER_ROLES, MultiplierSettings } from '../context/AppContext';

const Layout = ({ children }: { children?: React.ReactNode }) => {
  const location = useLocation();
  const { 
    branches, 
    selectedBranch, 
    setSelectedBranch, 
    userRole, 
    setUserRole,
    multipliers,
    setMultipliers,
    branchesLoading 
  } = useAppContext();
  
  const [showMultipliers, setShowMultipliers] = useState(false);

  const isActive = (path: string) => location.pathname === path ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800';
  
  const currentBranch = branches.find(b => b.id === selectedBranch);

  const handleMultiplierChange = (key: keyof MultiplierSettings, value: number) => {
    setMultipliers({ ...multipliers, [key]: value });
  };

  return (
    <div className="flex h-screen bg-slate-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-72 bg-slate-900 text-white flex-shrink-0 hidden md:flex flex-col transition-all duration-300">
        {/* Logo */}
        <div className="p-6 flex items-center space-x-3 border-b border-slate-700">
          <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
            <Car className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold tracking-tight">RENTY <span className="text-blue-400 text-sm font-normal">v2.0</span></span>
        </div>

        {/* Role & Branch Selection */}
        <div className="px-4 py-4 border-b border-slate-700/50 space-y-3">
          {/* User Role */}
          <div>
            <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5 block">User Role</label>
            <select
              value={userRole}
              onChange={(e) => setUserRole(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {USER_ROLES.map(role => (
                <option key={role} value={role}>{role}</option>
              ))}
            </select>
          </div>
          
          {/* Branch Selector */}
          <div>
            <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5 block">Branch</label>
            <div className="relative">
              <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <select
                value={selectedBranch}
                onChange={(e) => setSelectedBranch(Number(e.target.value))}
                disabled={branchesLoading}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-sm text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none"
              >
                {branches.map(branch => (
                  <option key={branch.id} value={branch.id}>
                    {branch.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
          <Link to="/" className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${isActive('/')}`}>
            <LayoutDashboard className="w-5 h-5" />
            <span className="font-medium">Manager Dashboard</span>
          </Link>
          <Link to="/analytics" className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${isActive('/analytics')}`}>
            <LineChart className="w-5 h-5" />
            <span className="font-medium">EDA Analysis</span>
          </Link>
          <Link to="/docs" className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${isActive('/docs')}`}>
            <FileText className="w-5 h-5" />
            <span className="font-medium">Documentation</span>
          </Link>
          
          {/* Multiplier Settings Section */}
          <div className="pt-6">
            <button 
              onClick={() => setShowMultipliers(!showMultipliers)}
              className="flex items-center justify-between w-full px-4 py-3 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <div className="flex items-center space-x-3">
                <Sliders className="w-5 h-5" />
                <span className="font-medium">Multiplier Settings</span>
              </div>
              {showMultipliers ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
            
            {showMultipliers && (
              <div className="mt-2 mx-2 p-4 bg-slate-800/50 rounded-xl space-y-4">
                {/* Min/Max Overall Multiplier */}
                <div className="space-y-3">
                  <h4 className="text-xs font-semibold text-amber-400 uppercase tracking-wider">Price Bounds</h4>
                  
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Min Multiplier</span>
                      <span className="text-white font-medium">{multipliers.min_multiplier.toFixed(2)}x</span>
                    </div>
                    <input
                      type="range"
                      min="0.5"
                      max="1.0"
                      step="0.05"
                      value={multipliers.min_multiplier}
                      onChange={(e) => handleMultiplierChange('min_multiplier', parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-amber-500"
                    />
                    <div className="flex justify-between text-xs text-slate-500 mt-1">
                      <span>-50%</span>
                      <span>0%</span>
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Max Multiplier</span>
                      <span className="text-white font-medium">{multipliers.max_multiplier.toFixed(2)}x</span>
                    </div>
                    <input
                      type="range"
                      min="1.5"
                      max="3.0"
                      step="0.1"
                      value={multipliers.max_multiplier}
                      onChange={(e) => handleMultiplierChange('max_multiplier', parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-amber-500"
                    />
                    <div className="flex justify-between text-xs text-slate-500 mt-1">
                      <span>+50%</span>
                      <span>+200%</span>
                    </div>
                  </div>
                </div>

                {/* Demand Multipliers */}
                <div className="space-y-3 pt-3 border-t border-slate-700/50">
                  <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Demand Impact</h4>
                  
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">High Demand</span>
                      <span className="text-emerald-400 font-medium">+{((multipliers.demand_high - 1) * 100).toFixed(0)}%</span>
                    </div>
                    <input
                      type="range"
                      min="1.05"
                      max="1.50"
                      step="0.05"
                      value={multipliers.demand_high}
                      onChange={(e) => handleMultiplierChange('demand_high', parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                    />
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Low Demand</span>
                      <span className="text-rose-400 font-medium">{((multipliers.demand_low - 1) * 100).toFixed(0)}%</span>
                    </div>
                    <input
                      type="range"
                      min="0.70"
                      max="0.95"
                      step="0.05"
                      value={multipliers.demand_low}
                      onChange={(e) => handleMultiplierChange('demand_low', parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-rose-500"
                    />
                  </div>
                </div>

                {/* Supply Multipliers */}
                <div className="space-y-3 pt-3 border-t border-slate-700/50">
                  <h4 className="text-xs font-semibold text-blue-400 uppercase tracking-wider">Supply Impact</h4>
                  
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Low Stock</span>
                      <span className="text-blue-400 font-medium">+{((multipliers.supply_high - 1) * 100).toFixed(0)}%</span>
                    </div>
                    <input
                      type="range"
                      min="1.05"
                      max="1.30"
                      step="0.05"
                      value={multipliers.supply_high}
                      onChange={(e) => handleMultiplierChange('supply_high', parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                    />
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">High Stock</span>
                      <span className="text-cyan-400 font-medium">{((multipliers.supply_low - 1) * 100).toFixed(0)}%</span>
                    </div>
                    <input
                      type="range"
                      min="0.80"
                      max="0.95"
                      step="0.05"
                      value={multipliers.supply_low}
                      onChange={(e) => handleMultiplierChange('supply_low', parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                    />
                  </div>
                </div>

                {/* Event Multiplier */}
                <div className="space-y-3 pt-3 border-t border-slate-700/50">
                  <h4 className="text-xs font-semibold text-purple-400 uppercase tracking-wider">Event Impact</h4>
                  
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Max Event Premium</span>
                      <span className="text-purple-400 font-medium">+{((multipliers.event_max - 1) * 100).toFixed(0)}%</span>
                    </div>
                    <input
                      type="range"
                      min="1.20"
                      max="2.00"
                      step="0.10"
                      value={multipliers.event_max}
                      onChange={(e) => handleMultiplierChange('event_max', parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
                    />
                    <div className="flex justify-between text-xs text-slate-500 mt-1">
                      <span>+20%</span>
                      <span>+100%</span>
                    </div>
                  </div>
                </div>

                {/* Reset Button */}
                <button
                  onClick={() => setMultipliers({
                    min_multiplier: 0.80,
                    max_multiplier: 2.50,
                    demand_high: 1.20,
                    demand_low: 0.85,
                    supply_high: 1.15,
                    supply_low: 0.90,
                    event_max: 1.60,
                  })}
                  className="w-full mt-2 py-2 text-xs font-medium text-slate-400 hover:text-white bg-slate-700/50 hover:bg-slate-700 rounded-lg transition-colors"
                >
                  Reset to Defaults
                </button>
              </div>
            )}
          </div>
          
          <div className="pt-4">
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 px-4">System</div>
            <a href="#" className="flex items-center space-x-3 px-4 py-3 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors">
              <Settings className="w-5 h-5" />
              <span className="font-medium">Pricing Rules</span>
            </a>
          </div>
        </nav>

        {/* User Info */}
        <div className="p-4 border-t border-slate-700">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center text-sm font-bold">
              {userRole.split(' ').map(w => w[0]).join('')}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{userRole}</p>
              <p className="text-xs text-slate-400 truncate">{currentBranch?.name || 'Loading...'}</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 shadow-sm">
          <div className="flex items-center text-slate-500">
            <Search className="w-5 h-5 mr-3" />
            <input 
              type="text" 
              placeholder="Search contracts, vehicles, or dates..." 
              className="bg-transparent border-none focus:ring-0 text-sm w-64 outline-none"
            />
          </div>
          <div className="flex items-center space-x-4">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              System Active
            </span>
            <button className="relative p-2 text-slate-400 hover:text-slate-600">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>
            <button className="p-1 rounded-full bg-slate-100">
              <User className="w-5 h-5 text-slate-600" />
            </button>
          </div>
        </header>

        {/* Scrollable Body */}
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;
