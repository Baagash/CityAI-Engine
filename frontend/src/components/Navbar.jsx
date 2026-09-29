import React, { useState, useEffect } from 'react';
import { 
  Radio, 
  RefreshCw, 
  Cpu, 
  ShieldCheck, 
  Menu, 
  X, 
  Activity,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

export default function Navbar({ 
  systemStatus = 'ONLINE', 
  isRefreshing = false, 
  onRefresh = () => {},
  isMobileMenuOpen = false,
  setIsMobileMenuOpen = () => {}
}) {
  const [timeStr, setTimeStr] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit' 
      }) + ' UTC+' + (-(now.getTimezoneOffset() / 60) >= 0 ? '+' : '') + (-now.getTimezoneOffset() / 60));
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const isOnline = systemStatus === 'ONLINE';

  return (
    <header className="bg-slate-950/90 border-b border-slate-800/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Title */}
          <div className="flex items-center space-x-3">
            <button 
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="lg:hidden p-2 text-slate-400 hover:text-white rounded-md focus:outline-none"
              aria-label="Toggle menu"
            >
              {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>

            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/20 via-blue-600/20 to-indigo-600/20 border border-cyan-500/40 flex items-center justify-center shadow-[0_0_15px_rgba(6,182,212,0.25)]">
                <Radio className="w-5 h-5 text-cyan-400 animate-pulse" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h1 className="text-base sm:text-lg font-black tracking-wider text-white uppercase bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text">
                    CITY AI TRAFFIC COMMAND CENTER
                  </h1>
                </div>
                <div className="flex items-center space-x-2 text-[11px] text-slate-400 font-mono">
                  <span className="text-cyan-400 font-semibold">PHASE 1: FOUNDATION</span>
                  <span className="text-slate-600">•</span>
                  <span>SYSTEM TELEMETRY</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Status & Controls */}
          <div className="flex items-center space-x-4">
            {/* Clock */}
            <div className="hidden md:flex flex-col items-end px-3 py-1 rounded-lg bg-slate-900/60 border border-slate-800 text-right">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">COMMAND CLOCK</span>
              <span className="text-xs font-mono text-cyan-300 font-semibold tracking-wider">
                {timeStr || '00:00:00'}
              </span>
            </div>

            {/* Subsystem Health Pill */}
            <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-full border text-xs font-semibold tracking-wide ${
              isOnline 
                ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300 shadow-[0_0_12px_rgba(16,185,129,0.2)]'
                : 'bg-rose-950/40 border-rose-500/40 text-rose-300 shadow-[0_0_12px_rgba(244,63,94,0.2)]'
            }`}>
              {isOnline ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                  <span className="hidden sm:inline">CORE SYSTEM:</span>
                  <span>ONLINE</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
                  <span className="hidden sm:inline">CORE SYSTEM:</span>
                  <span>OFFLINE</span>
                </>
              )}
            </div>

            {/* Refresh Button */}
            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              title="Refresh telemetry"
              className="p-2 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-700/60 text-slate-300 hover:text-white transition disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`} />
            </button>
          </div>

        </div>
      </div>
    </header>
  );
}
