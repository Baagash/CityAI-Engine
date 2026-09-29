import React, { useState } from 'react';
import { 
  Sliders, 
  Play, 
  CopyCheck, 
  Zap, 
  AlertTriangle, 
  ShieldAlert, 
  CloudSun, 
  CloudRain, 
  Moon, 
  CloudFog, 
  RefreshCcw,
  CheckCircle2,
  Terminal
} from 'lucide-react';
import { api } from '../services/api';

export default function SimulationControl() {
  const [activeScenario, setActiveScenario] = useState('NORMAL_TRAFFIC');
  const [weather, setWeather] = useState('CLEAR');
  const [logs, setLogs] = useState([
    `[${new Date().toLocaleTimeString()}] Simulation Engine initialized. Normal city baseline flow active.`
  ]);
  const [triggering, setTriggering] = useState(false);

  const handleTriggerScenario = async (type) => {
    setTriggering(true);
    try {
      const res = await api.triggerScenario(type, weather);
      setActiveScenario(type);
      setLogs(prev => [
        `[${new Date().toLocaleTimeString()}] SCENARIO TRIGGERED: ${res.message}`,
        ...prev
      ]);
    } catch (err) {
      setLogs(prev => [
        `[${new Date().toLocaleTimeString()}] ERROR: ${err.message}`,
        ...prev
      ]);
    } finally {
      setTriggering(false);
    }
  };

  const handleChangeWeather = async (w) => {
    setWeather(w);
    try {
      await api.setWeather(w);
      setLogs(prev => [
        `[${new Date().toLocaleTimeString()}] ENVIRONMENT UPDATED: Weather condition set to ${w}`,
        ...prev
      ]);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-cyan-950/30 to-purple-950/40 border border-slate-800 shadow-xl">
        <div className="flex items-center space-x-2">
          <Sliders className="w-4 h-4 text-cyan-400" />
          <span className="text-[10px] uppercase font-bold text-cyan-400 tracking-wider">
            EVALUATION & DEMO CONTROL DECK
          </span>
        </div>
        <h1 className="text-xl font-black text-slate-100 mt-0.5">Real-Time Scenario Simulator</h1>
        <p className="text-xs text-slate-400 max-w-3xl">
          Instantly inject multi-camera edge cases, duplicate cloned plates, impossible velocity violations, and weather degradations to test AI correlation accuracy.
        </p>
      </div>

      {/* Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Scenario 1: Cloned Plate */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-red-900/40 space-y-3 hover:border-red-500/60 transition shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 rounded-lg bg-red-500/10 text-red-400 border border-red-500/30">
                <CopyCheck className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-100">Scenario 1: Cloned Plate Conflict</h3>
                <span className="text-[10px] font-mono text-red-400 font-bold">CORE INNOVATION TEST</span>
              </div>
            </div>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Spawns plate <strong className="text-emerald-400 font-mono">TN38AB1234</strong> simultaneously as a <strong>White Sedan</strong> on CAM01 and a <strong>Black SUV</strong> on CAM04. Tests attribute mismatch & cross-camera correlation.
          </p>

          <button
            disabled={triggering}
            onClick={() => handleTriggerScenario('CLONED_PLATE')}
            className="w-full py-2.5 bg-red-600 hover:bg-red-500 text-white text-xs font-bold rounded-xl flex items-center justify-center space-x-2 transition shadow-lg shadow-red-900/30"
          >
            <Play className="w-4 h-4 fill-white" />
            <span>Inject Cloned Plate Conflict</span>
          </button>
        </div>

        {/* Scenario 2: Impossible Speed */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-orange-900/40 space-y-3 hover:border-orange-500/60 transition shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 rounded-lg bg-orange-500/10 text-orange-400 border border-orange-500/30">
                <Zap className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-100">Scenario 2: Impossible Speed Anomaly</h3>
                <span className="text-[10px] font-mono text-orange-400 font-bold">TOPOLOGICAL TRANSIT VIOLATION</span>
              </div>
            </div>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Spawns vehicle <strong className="text-emerald-400 font-mono">KA05MB9912</strong> at CAM01 and then CAM04 (18 km distance) in 10 seconds. Tests topological physics velocity limit detection.
          </p>

          <button
            disabled={triggering}
            onClick={() => handleTriggerScenario('IMPOSSIBLE_SPEED')}
            className="w-full py-2.5 bg-orange-600 hover:bg-orange-500 text-white text-xs font-bold rounded-xl flex items-center justify-center space-x-2 transition shadow-lg shadow-orange-900/30"
          >
            <Play className="w-4 h-4 fill-white" />
            <span>Inject Impossible Speed Anomaly</span>
          </button>
        </div>

        {/* Scenario 3: Stolen Car Sighting */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-purple-900/40 space-y-3 hover:border-purple-500/60 transition shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/30">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-100">Scenario 3: Stolen Hotlist Sighting</h3>
                <span className="text-[10px] font-mono text-purple-400 font-bold">DMV REGISTRY CORRELATION</span>
              </div>
            </div>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Spawns stolen registered vehicle <strong className="text-emerald-400 font-mono">DL01CA1024</strong> at CAM02 (Downtown). Tests automatic DMV hotlist matching and instant intercept alert.
          </p>

          <button
            disabled={triggering}
            onClick={() => handleTriggerScenario('STOLEN_VEHICLE')}
            className="w-full py-2.5 bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold rounded-xl flex items-center justify-center space-x-2 transition shadow-lg shadow-purple-900/30"
          >
            <Play className="w-4 h-4 fill-white" />
            <span>Spawn Stolen Vehicle Track</span>
          </button>
        </div>

        {/* Scenario 4: Highway Congestion & Reset */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3 hover:border-cyan-500/50 transition shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-100">Scenario 4 & 5: Congestion & Reset</h3>
                <span className="text-[10px] font-mono text-cyan-400 font-bold">TRAFFIC FLOW SIMULATION</span>
              </div>
            </div>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Trigger a traffic bottleneck on CAM03 (Expressway) or reset the entire simulator to clean standard baseline traffic.
          </p>

          <div className="grid grid-cols-2 gap-2">
            <button
              disabled={triggering}
              onClick={() => handleTriggerScenario('CONGESTION')}
              className="py-2.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold rounded-xl flex items-center justify-center space-x-1.5 transition"
            >
              <AlertTriangle className="w-4 h-4" />
              <span>Trigger Congestion</span>
            </button>
            <button
              disabled={triggering}
              onClick={() => handleTriggerScenario('NORMAL_TRAFFIC')}
              className="py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold rounded-xl flex items-center justify-center space-x-1.5 transition"
            >
              <RefreshCcw className="w-4 h-4" />
              <span>Reset Baseline</span>
            </button>
          </div>
        </div>
      </div>

      {/* Environmental Weather Switcher */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3 shadow-xl">
        <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
          Environmental Weather & Visibility Matrix
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { id: 'CLEAR', label: 'Clear Daylight', penalty: '0% OCR penalty', icon: CloudSun, color: 'border-amber-500/40 text-amber-300' },
            { id: 'RAIN', label: 'Heavy Rain', penalty: '15% OCR penalty', icon: CloudRain, color: 'border-blue-500/40 text-blue-300' },
            { id: 'NIGHT', label: 'Night Low-Light', penalty: '20% OCR penalty', icon: Moon, color: 'border-purple-500/40 text-purple-300' },
            { id: 'FOG', label: 'Dense Fog', penalty: '30% OCR penalty', icon: CloudFog, color: 'border-gray-500/40 text-gray-300' }
          ].map(({ id, label, penalty, icon: Icon, color }) => (
            <button
              key={id}
              onClick={() => handleChangeWeather(id)}
              className={`p-3.5 rounded-xl border text-left transition ${
                weather === id
                  ? `bg-slate-950 ${color} shadow-[0_0_15px_rgba(0,242,254,0.15)] ring-1 ring-cyan-400`
                  : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center space-x-2">
                <Icon className="w-4 h-4" />
                <span className="text-xs font-bold text-slate-200">{label}</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1 font-mono">{penalty}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Live Terminal Console */}
      <div className="rounded-2xl bg-slate-950 border border-slate-800 overflow-hidden shadow-2xl p-4 space-y-2">
        <div className="flex items-center justify-between text-xs pb-2 border-b border-slate-800">
          <span className="font-mono text-cyan-400 flex items-center space-x-1.5">
            <Terminal className="w-4 h-4" />
            <span>Simulation Event Log & Console</span>
          </span>
          <span className="text-[10px] text-slate-500 font-mono">Live Ingestion Active</span>
        </div>

        <div className="font-mono text-xs text-slate-300 space-y-1 max-h-40 overflow-y-auto">
          {logs.map((log, idx) => (
            <div key={idx} className="leading-snug text-slate-300">
              {log}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
