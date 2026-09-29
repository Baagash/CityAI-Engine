import React from 'react';

export default function MetricCard({ title, value, subtitle, icon: Icon, color = 'cyan', change = null }) {
  const colorStyles = {
    cyan: {
      border: 'border-cyan-500/30',
      iconBg: 'bg-cyan-500/10 text-cyan-400',
      glow: 'shadow-[0_0_15px_rgba(0,242,254,0.1)]'
    },
    red: {
      border: 'border-red-500/40',
      iconBg: 'bg-red-500/10 text-red-400',
      glow: 'shadow-[0_0_15px_rgba(239,68,68,0.15)]'
    },
    amber: {
      border: 'border-amber-500/30',
      iconBg: 'bg-amber-500/10 text-amber-400',
      glow: 'shadow-[0_0_15px_rgba(245,158,11,0.1)]'
    },
    emerald: {
      border: 'border-emerald-500/30',
      iconBg: 'bg-emerald-500/10 text-emerald-400',
      glow: 'shadow-[0_0_15px_rgba(16,185,129,0.1)]'
    },
    purple: {
      border: 'border-purple-500/30',
      iconBg: 'bg-purple-500/10 text-purple-400',
      glow: 'shadow-[0_0_15px_rgba(168,85,247,0.1)]'
    }
  }[color] || {
    border: 'border-slate-700',
    iconBg: 'bg-slate-800 text-slate-300',
    glow: ''
  };

  return (
    <div className={`p-4 rounded-xl bg-slate-900/80 border ${colorStyles.border} ${colorStyles.glow} transition duration-200 hover:scale-[1.01]`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</span>
        {Icon && (
          <div className={`p-2 rounded-lg ${colorStyles.iconBg}`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="mt-2 flex items-baseline justify-between">
        <span className="text-2xl font-black text-slate-100 font-mono tracking-tight">{value}</span>
        {change && (
          <span className={`text-[11px] font-bold ${change.startsWith('+') ? 'text-emerald-400' : 'text-slate-400'}`}>
            {change}
          </span>
        )}
      </div>

      {subtitle && <p className="mt-1 text-[11px] text-slate-500">{subtitle}</p>}
    </div>
  );
}
