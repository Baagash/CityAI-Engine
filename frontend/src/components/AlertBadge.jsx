import React from 'react';

export function AlertTypeBadge({ type }) {
  let color = 'bg-slate-800 text-slate-300 border-slate-700';
  let label = type;

  if (type === 'POSSIBLE_DUPLICATE_PLATE') {
    color = 'bg-red-950/80 text-red-300 border-red-800/80 font-bold';
    label = 'POSSIBLE DUPLICATE PLATE';
  } else if (type === 'IMPOSSIBLE_TRAVEL') {
    color = 'bg-orange-950/80 text-orange-300 border-orange-800/80 font-bold';
    label = 'IMPOSSIBLE TRAVEL';
  } else if (type === 'REGISTRY_MISMATCH') {
    color = 'bg-amber-950/80 text-amber-300 border-amber-800/80 font-bold';
    label = 'REGISTRY MISMATCH';
  } else if (type === 'TRAFFIC_CONGESTION') {
    color = 'bg-yellow-950/80 text-yellow-300 border-yellow-800/80';
    label = 'TRAFFIC CONGESTION';
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] uppercase tracking-wider border ${color}`}>
      {label}
    </span>
  );
}

export function SeverityBadge({ severity }) {
  let color = 'bg-slate-800 text-slate-300 border-slate-700';
  if (severity === 'CRITICAL') {
    color = 'bg-red-900/60 text-red-200 border-red-600 animate-pulse';
  } else if (severity === 'WARNING') {
    color = 'bg-amber-900/60 text-amber-200 border-amber-600';
  } else if (severity === 'INFO') {
    color = 'bg-blue-900/60 text-blue-200 border-blue-600';
  }

  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold uppercase border ${color}`}>
      {severity}
    </span>
  );
}

export function StatusBadge({ status }) {
  let color = 'bg-slate-800 text-slate-300 border-slate-700';
  let label = status?.replace(/_/g, ' ') || 'UNKNOWN';

  if (status === 'REQUIRES_VERIFICATION') {
    color = 'bg-amber-950/90 text-amber-300 border-amber-700 font-semibold';
  } else if (status === 'UNDER_INVESTIGATION') {
    color = 'bg-purple-950/90 text-purple-300 border-purple-700 font-semibold';
  } else if (status === 'VERIFIED_ANOMALY') {
    color = 'bg-emerald-950/90 text-emerald-300 border-emerald-700 font-semibold';
  } else if (status === 'DISMISSED_FALSE_POSITIVE') {
    color = 'bg-slate-800 text-slate-400 border-slate-700 line-through';
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] uppercase tracking-wide border ${color}`}>
      {label}
    </span>
  );
}
