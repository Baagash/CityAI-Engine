import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Video, 
  Crosshair, 
  Route, 
  BarChart3, 
  AlertTriangle, 
  FolderLock, 
  Camera, 
  Settings,
  Cpu
} from 'lucide-react';

export const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard, exact: true, status: 'READY' },
  { path: '/live-cameras', label: 'Live Cameras', icon: Video, status: 'READY' },
  { path: '/camera-management', label: 'Camera Management', icon: Camera, status: 'READY' },
  { path: '/vehicle-search', label: 'Vehicle Detection', icon: Crosshair, status: 'READY' },
  { path: '/trajectories', label: 'Trajectories', icon: Route, status: 'PHASE 4' },
  { path: '/analytics', label: 'Traffic Analytics', icon: BarChart3, status: 'PHASE 4' },
  { path: '/alerts', label: 'Alerts', icon: AlertTriangle, status: 'PHASE 4' },
  { path: '/investigations', label: 'Investigations', icon: FolderLock, status: 'PHASE 4' },
  { path: '/settings', label: 'Settings', icon: Settings, status: 'READY' }
];

export default function Sidebar({ isOpen, onClose }) {
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div 
          onClick={onClose}
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-40 lg:hidden"
        />
      )}

      <aside className={`
        fixed lg:static top-16 bottom-0 left-0 z-40
        w-64 bg-slate-950/95 lg:bg-slate-950/60 border-r border-slate-800/80
        flex flex-col justify-between p-3.5 shrink-0 h-[calc(100vh-4rem)]
        transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {/* Navigation Sections */}
        <div className="space-y-4">
          <div>
            <div className="px-3 py-1.5 text-[10px] font-bold text-slate-500 uppercase tracking-widest font-mono">
              Command Modules
            </div>
            <nav className="space-y-1 mt-1">
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    end={item.exact}
                    onClick={onClose}
                    className={({ isActive }) =>
                      `flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition group ${
                        isActive
                          ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/40 shadow-[0_0_15px_rgba(6,182,212,0.15)] font-semibold'
                          : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900/80 border border-transparent'
                      }`
                    }
                  >
                    <div className="flex items-center space-x-3 truncate">
                      <Icon className="w-4 h-4 shrink-0 transition-transform group-hover:scale-110" />
                      <span className="truncate">{item.label}</span>
                    </div>

                    {item.status === 'READY' ? (
                      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                        LIVE
                      </span>
                    ) : (
                      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-900 text-slate-500 border border-slate-800">
                        {item.status}
                      </span>
                    )}
                  </NavLink>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Phase 3 AI Inference & MOT Banner */}
        <div className="p-3 rounded-xl bg-gradient-to-b from-slate-900/90 to-slate-950 border border-slate-800/80 text-[11px] space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1.5 text-cyan-400 font-semibold">
              <Cpu className="w-3.5 h-3.5" />
              <span>YOLOV8 TRACKING ENGINE</span>
            </div>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          </div>
          <p className="text-slate-400 leading-tight text-[11px]">
            Real vehicle detection (car, truck, bus, bike) & per-camera MOT active.
          </p>
          <div className="pt-1 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-500 font-mono">
            <span>MODEL: YOLOv8n</span>
            <span>MOT: BYTETRACK</span>
          </div>
        </div>
      </aside>
    </>
  );
}
