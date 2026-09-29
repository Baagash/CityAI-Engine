import React from 'react';
import { 
  Radio, 
  Layers, 
  Cpu, 
  Lock, 
  Terminal, 
  CheckCircle2, 
  Clock, 
  ArrowRight,
  Database,
  Eye,
  Search,
  Route,
  BarChart2,
  AlertTriangle,
  FolderLock,
  Camera,
  Settings
} from 'lucide-react';

const ICON_MAP = {
  'Live Cameras': Camera,
  'Vehicle Search': Search,
  'Trajectories': Route,
  'Traffic Analytics': BarChart2,
  'Alerts': AlertTriangle,
  'Investigations': FolderLock,
  'Camera Management': Camera,
  'Settings': Settings
};

export default function PlaceholderPage({ 
  title = "Module", 
  phase = "Phase 2", 
  description = "This operational module is scheduled for activation in upcoming development phases.",
  details = []
}) {
  const IconComponent = ICON_MAP[title] || Layers;

  return (
    <div className="space-y-6">
      {/* Module Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-[0_0_20px_rgba(6,182,212,0.15)]">
            <IconComponent className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-black tracking-wide text-white uppercase">{title}</h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                {phase} DEFERRED
              </span>
            </div>
            <p className="text-sm text-slate-400 mt-1">{description}</p>
          </div>
        </div>

        <div className="flex items-center space-x-2 px-3 py-2 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-400 font-mono">
          <Clock className="w-4 h-4 text-amber-400" />
          <span>INITIALIZATION SCHEDULED</span>
        </div>
      </div>

      {/* Main Content Showcase */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Module Scope & Specification */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-slate-900/40 border border-slate-800/80 backdrop-blur-sm space-y-5">
          <div className="flex items-center space-x-2 text-xs font-mono text-cyan-400 font-bold uppercase tracking-wider">
            <Terminal className="w-4 h-4" />
            <span>Planned Module Architecture</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {details.length > 0 ? (
              details.map((item, index) => (
                <div key={index} className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5">
                  <div className="text-xs font-bold text-slate-200">{item.title}</div>
                  <div className="text-xs text-slate-400 leading-relaxed">{item.desc}</div>
                </div>
              ))
            ) : (
              <>
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5">
                  <div className="text-xs font-bold text-slate-200">High-Precision Computer Vision</div>
                  <div className="text-xs text-slate-400">Deep neural vehicle recognition, plate OCR segmentation, and Re-ID embeddings.</div>
                </div>
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5">
                  <div className="text-xs font-bold text-slate-200">Real-Time City Pipeline</div>
                  <div className="text-xs text-slate-400">Multi-stream RTSP feed orchestration and anomaly event triggering.</div>
                </div>
              </>
            )}
          </div>

          {/* Tactical Status Notice */}
          <div className="p-4 rounded-xl bg-cyan-950/20 border border-cyan-500/20 flex items-start space-x-3 text-xs text-cyan-200/90">
            <Radio className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-cyan-300">Phase 1 Foundation Rule: </span>
              In accordance with project guidelines, AI detectors, CCTV inferencing pipelines, and advanced analytics models will be initialized sequentially after foundation verification.
            </div>
          </div>
        </div>

        {/* System Readiness Panel */}
        <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800/80 backdrop-blur-sm flex flex-col justify-between space-y-6">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center space-x-2">
              <Cpu className="w-4 h-4 text-cyan-400" />
              <span>Foundation Prerequisites</span>
            </h3>

            <div className="space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80">
                <span className="text-slate-300">FastAPI Core</span>
                <span className="text-emerald-400 font-bold flex items-center space-x-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>ONLINE</span>
                </span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80">
                <span className="text-slate-300">SQLite Database</span>
                <span className="text-emerald-400 font-bold flex items-center space-x-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>INITIALIZED</span>
                </span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80">
                <span className="text-slate-300">React Command UI</span>
                <span className="text-emerald-400 font-bold flex items-center space-x-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>ACTIVE</span>
                </span>
              </div>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-400">
            <span className="text-slate-200 font-medium">Ready for next phase execution.</span>
          </div>
        </div>

      </div>
    </div>
  );
}
