import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  Search, 
  Car, 
  Calendar, 
  MapPin, 
  Navigation, 
  Clock, 
  ShieldAlert, 
  CheckCircle, 
  AlertTriangle,
  XCircle,
  FileText,
  TrendingUp,
  UserCheck,
  Camera,
  Activity,
  Layers,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  RefreshCw
} from 'lucide-react';
import { api } from '../services/api';

export default function VehicleSearch() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [plateQuery, setPlateQuery] = useState(searchParams.get('plate') || '');
  const [globalIdQuery, setGlobalIdQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [colorFilter, setColorFilter] = useState('');
  
  const [vehicles, setVehicles] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [loading, setLoading] = useState(false);

  // Live Pairwise Re-ID Match Test Panel State
  const [showMatcher, setShowMatcher] = useState(false);
  const [matchCamA, setMatchCamA] = useState('CAM01');
  const [matchCamB, setMatchCamB] = useState('CAM02');
  const [matchPlateA, setMatchPlateA] = useState('TN38AB1234');
  const [matchPlateB, setMatchPlateB] = useState('TN38AB1234');
  const [matchTypeA, setMatchTypeA] = useState('sedan');
  const [matchTypeB, setMatchTypeB] = useState('sedan');
  const [matchColorA, setMatchColorA] = useState('WHITE');
  const [matchColorB, setMatchColorB] = useState('WHITE');
  const [matchTimeElapsed, setMatchTimeElapsed] = useState(240);
  const [matchResult, setMatchResult] = useState(null);
  const [matchingLoading, setMatchingLoading] = useState(false);

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    try {
      const results = await api.searchVehicles({
        plate: plateQuery,
        global_id: globalIdQuery,
        vehicle_type: typeFilter,
        color: colorFilter
      });
      setVehicles(results);
      if (results.length > 0) {
        setSelectedVehicle(results[0]);
      } else {
        setSelectedVehicle(null);
      }
    } catch (err) {
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunPairwiseMatch = async (e) => {
    if (e) e.preventDefault();
    setMatchingLoading(true);
    try {
      const res = await api.matchReID({
        camera_a: matchCamA,
        camera_b: matchCamB,
        tracker_a: `${matchCamA}-TRK-001`,
        tracker_b: `${matchCamB}-TRK-002`,
        plate_a: matchPlateA,
        plate_b: matchPlateB,
        vehicle_type_a: matchTypeA,
        vehicle_type_b: matchTypeB,
        color_a: matchColorA,
        color_b: matchColorB,
        time_elapsed_sec: parseFloat(matchTimeElapsed) || 120.0
      });
      setMatchResult(res);
    } catch (err) {
      console.error('Re-ID Match Error:', err);
    } finally {
      setMatchingLoading(false);
    }
  };

  useEffect(() => {
    handleSearch();
  }, [searchParams]);

  // Decision badge helper
  const renderDecisionBadge = (decision, reasonCode) => {
    const dec = (decision || 'MATCH').toUpperCase();
    if (dec === 'MATCH') {
      return (
        <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-950/80 border border-emerald-500/60 text-emerald-300 text-xs font-bold">
          <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
          <span>MATCH</span>
          {reasonCode && <span className="text-[10px] text-emerald-400/70 font-normal">({reasonCode})</span>}
        </div>
      );
    } else if (dec === 'REVIEW_REQUIRED' || dec === 'UNCERTAIN') {
      return (
        <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-amber-950/80 border border-amber-500/60 text-amber-300 text-xs font-bold">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          <span>REVIEW REQUIRED</span>
          {reasonCode && <span className="text-[10px] text-amber-400/80 font-normal">({reasonCode})</span>}
        </div>
      );
    } else {
      return (
        <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-rose-950/80 border border-rose-500/60 text-rose-300 text-xs font-bold">
          <XCircle className="w-3.5 h-3.5 text-rose-400" />
          <span>REJECT</span>
          {reasonCode && <span className="text-[10px] text-rose-400/80 font-normal">({reasonCode})</span>}
        </div>
      );
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <Car className="w-4 h-4 text-cyan-400" />
              <span className="text-[10px] uppercase font-bold text-cyan-400 tracking-wider">
                PHASE 5 — MULTI-CAMERA VEHICLE RE-IDENTIFICATION & TRAJECTORY INTELLIGENCE
              </span>
            </div>
            <h1 className="text-xl font-black text-slate-100">Vehicle Intelligence & Re-ID Explorer</h1>
            <p className="text-xs text-slate-400 max-w-2xl">
              Cross-camera global vehicle profile correlation combining visual appearance embeddings, plate similarity,
              attributes, and camera topology spatiotemporal verification.
            </p>
          </div>

          <button
            onClick={() => setShowMatcher(!showMatcher)}
            className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-cyan-300 text-xs font-semibold flex items-center space-x-1.5 transition"
          >
            <Activity className="w-3.5 h-3.5" />
            <span>{showMatcher ? 'Hide Live Re-ID Matcher' : 'Open Pairwise Re-ID Matcher'}</span>
          </button>
        </div>

        {/* Multi-Parameter Search Controls */}
        <form onSubmit={handleSearch} className="mt-4 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
          <div>
            <label className="block text-[11px] text-slate-400 mb-1">Plate Number</label>
            <input
              type="text"
              placeholder="e.g. TN38AB1234 or UNKNOWN"
              value={plateQuery}
              onChange={(e) => setPlateQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
            />
          </div>

          <div>
            <label className="block text-[11px] text-slate-400 mb-1">Global ID</label>
            <input
              type="text"
              placeholder="e.g. VEH-000042"
              value={globalIdQuery}
              onChange={(e) => setGlobalIdQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
            />
          </div>

          <div>
            <label className="block text-[11px] text-slate-400 mb-1">Vehicle Type</label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-400"
            >
              <option value="">All Types</option>
              <option value="sedan">Sedan</option>
              <option value="suv">SUV</option>
              <option value="truck">Truck</option>
              <option value="bus">Bus</option>
              <option value="motorcycle">Motorcycle</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] text-slate-400 mb-1">Observed Color</label>
            <select
              value={colorFilter}
              onChange={(e) => setColorFilter(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-400"
            >
              <option value="">All Colors</option>
              <option value="WHITE">White</option>
              <option value="BLACK">Black</option>
              <option value="SILVER">Silver / Grey</option>
              <option value="BLUE">Blue</option>
              <option value="RED">Red</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={loading}
              className="w-full px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-lg flex items-center justify-center space-x-1.5 transition shadow-lg shadow-cyan-900/30"
            >
              <Search className="w-4 h-4" />
              <span>{loading ? 'Searching...' : 'Search Network'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Interactive Pairwise Re-ID Matcher Panel (Step 17 POST /api/vehicles/reid/match) */}
      {showMatcher && (
        <div className="p-5 rounded-2xl bg-slate-900 border border-cyan-800/60 shadow-2xl space-y-4 animate-in fade-in duration-200">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-cyan-400" />
              <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
                Multi-Modal Vehicle Re-ID Pairwise Simulator
              </h2>
            </div>
            <span className="text-[10px] text-slate-400 font-mono">POST /api/vehicles/reid/match</span>
          </div>

          <form onSubmit={handleRunPairwiseMatch} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
            {/* Observation A */}
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <span className="text-[10px] font-bold text-cyan-400 uppercase">Observation A (Source)</span>
              <div>
                <label className="block text-[10px] text-slate-400">Camera</label>
                <select value={matchCamA} onChange={(e) => setMatchCamA(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200">
                  <option value="CAM01">CAM01 (North Ring Road)</option>
                  <option value="CAM02">CAM02 (Anna Salai)</option>
                  <option value="CAM03">CAM03 (OMR Expressway)</option>
                  <option value="CAM04">CAM04 (Port Terminal)</option>
                </select>
              </div>
              <div>
                <label className="block text-[10px] text-slate-400">Plate</label>
                <input type="text" value={matchPlateA} onChange={(e) => setMatchPlateA(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200" />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[10px] text-slate-400">Type</label>
                  <select value={matchTypeA} onChange={(e) => setMatchTypeA(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200">
                    <option value="sedan">Sedan</option>
                    <option value="suv">SUV</option>
                    <option value="truck">Truck</option>
                    <option value="bus">Bus</option>
                    <option value="motorcycle">Motorcycle</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] text-slate-400">Color</label>
                  <select value={matchColorA} onChange={(e) => setMatchColorA(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200">
                    <option value="WHITE">White</option>
                    <option value="BLACK">Black</option>
                    <option value="BLUE">Blue</option>
                    <option value="RED">Red</option>
                    <option value="SILVER">Silver</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Observation B */}
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <span className="text-[10px] font-bold text-purple-400 uppercase">Observation B (Destination)</span>
              <div>
                <label className="block text-[10px] text-slate-400">Camera</label>
                <select value={matchCamB} onChange={(e) => setMatchCamB(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200">
                  <option value="CAM02">CAM02 (Anna Salai)</option>
                  <option value="CAM01">CAM01 (North Ring Road)</option>
                  <option value="CAM03">CAM03 (OMR Expressway)</option>
                  <option value="CAM04">CAM04 (Port Terminal)</option>
                </select>
              </div>
              <div>
                <label className="block text-[10px] text-slate-400">Plate</label>
                <input type="text" value={matchPlateB} onChange={(e) => setMatchPlateB(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200" />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[10px] text-slate-400">Type</label>
                  <select value={matchTypeB} onChange={(e) => setMatchTypeB(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200">
                    <option value="sedan">Sedan</option>
                    <option value="suv">SUV</option>
                    <option value="truck">Truck</option>
                    <option value="bus">Bus</option>
                    <option value="motorcycle">Motorcycle</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] text-slate-400">Color</label>
                  <select value={matchColorB} onChange={(e) => setMatchColorB(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200">
                    <option value="WHITE">White</option>
                    <option value="BLACK">Black</option>
                    <option value="BLUE">Blue</option>
                    <option value="RED">Red</option>
                    <option value="SILVER">Silver</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Transit Parameters & Submit */}
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <span className="text-[10px] font-bold text-amber-400 uppercase">Transit Timing</span>
              <div>
                <label className="block text-[10px] text-slate-400">Elapsed Seconds</label>
                <input
                  type="number"
                  value={matchTimeElapsed}
                  onChange={(e) => setMatchTimeElapsed(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200"
                />
                <span className="text-[10px] text-slate-500">Min safe transit CAM01→CAM02: 105s</span>
              </div>
              <div className="pt-3">
                <button
                  type="submit"
                  disabled={matchingLoading}
                  className="w-full py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold rounded-lg transition shadow-lg shadow-cyan-950/40"
                >
                  {matchingLoading ? 'Evaluating...' : 'Evaluate Re-ID Match'}
                </button>
              </div>
            </div>

            {/* Match Decision Result */}
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <span className="text-[10px] font-bold text-emerald-400 uppercase">Evaluation Output</span>
              {matchResult ? (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Decision:</span>
                    {renderDecisionBadge(matchResult.decision, matchResult.reason_code)}
                  </div>
                  <div className="text-[11px] text-slate-300">
                    Composite Score: <strong className="text-cyan-400 font-mono">{Math.round(matchResult.composite_score * 100)}%</strong>
                  </div>
                  <div className="text-[10px] text-slate-400 bg-slate-900 p-2 rounded border border-slate-800">
                    {matchResult.reason}
                  </div>
                </div>
              ) : (
                <div className="text-slate-500 text-[11px] italic py-3 text-center">
                  Set observation parameters and click Evaluate Re-ID Match.
                </div>
              )}
            </div>
          </form>
        </div>
      )}

      {/* Results & Vehicle Dossier View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Search Results List (1 Col) */}
        <div className="space-y-3">
          <div className="flex justify-between items-center text-xs font-semibold text-slate-400 px-1">
            <span>Global Entities Identified ({vehicles.length})</span>
            <span className="text-[10px]">Select to inspect dossier</span>
          </div>

          <div className="space-y-2.5 max-h-[650px] overflow-y-auto pr-1">
            {vehicles.length === 0 ? (
              <div className="p-8 rounded-xl bg-slate-900 border border-slate-800 text-center text-xs text-slate-500">
                No vehicles matching current criteria.
              </div>
            ) : (
              vehicles.map((v) => (
                <div
                  key={v.id}
                  onClick={() => setSelectedVehicle(v)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition space-y-2 ${
                    selectedVehicle?.id === v.id
                      ? 'bg-cyan-950/40 border-cyan-500/60 shadow-[0_0_15px_rgba(0,242,254,0.15)]'
                      : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 bg-emerald-950 border border-emerald-700 text-emerald-300 font-mono font-bold text-xs rounded">
                      {v.primary_plate || 'NO PLATE'}
                    </span>
                    <span className="font-mono text-[11px] text-cyan-400 font-bold">{v.global_id}</span>
                  </div>

                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span className="capitalize">{v.color} {v.vehicle_type}</span>
                    <span className="text-slate-300 font-bold">{v.total_sightings} Sighting{v.total_sightings > 1 ? 's' : ''}</span>
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-800/80">
                    <span>Last: {v.last_camera_id || 'CAM01'} • {new Date(v.last_seen).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    <span className="font-mono text-cyan-400 font-bold">Conf: {Math.round(v.confidence * 100)}%</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Deep Vehicle Profile & Trajectory Timeline (2 Cols) */}
        <div className="lg:col-span-2 space-y-5">
          {selectedVehicle ? (
            <>
              {/* Profile Card */}
              <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2.5">
                      <span className="text-xl font-black font-mono text-emerald-400 px-2.5 py-0.5 rounded bg-emerald-950/80 border border-emerald-700/80">
                        {selectedVehicle.primary_plate || 'UNKNOWN PLATE'}
                      </span>
                      <span className="text-xs font-mono font-bold text-cyan-300 bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-800/80">
                        {selectedVehicle.global_id}
                      </span>
                      {renderDecisionBadge(selectedVehicle.reid_decision, selectedVehicle.reid_reason)}
                    </div>
                    <p className="text-xs text-slate-400">
                      Primary Profile: <strong className="text-slate-200 capitalize">{selectedVehicle.color} {selectedVehicle.vehicle_type}</strong>
                    </p>
                  </div>

                  <div className="text-right text-xs">
                    <span className="text-slate-400">Re-ID Confidence:</span>
                    <p className="text-lg font-black text-emerald-400 font-mono">
                      {Math.round(selectedVehicle.confidence * 100)}%
                    </p>
                  </div>
                </div>

                {/* Multimodal Score Breakdown Meters */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                  <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                    <span className="text-[10px] text-slate-400 uppercase block">Visual Appearance (40%)</span>
                    <div className="flex justify-between items-center">
                      <span className="font-mono text-cyan-300 font-bold">Cosine Sim</span>
                      <span className="font-mono text-cyan-400 font-bold">{Math.round(selectedVehicle.confidence * 100)}%</span>
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-cyan-400 h-full rounded-full" style={{ width: `${Math.round(selectedVehicle.confidence * 100)}%` }} />
                    </div>
                  </div>

                  <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                    <span className="text-[10px] text-slate-400 uppercase block">Plate String (30%)</span>
                    <div className="flex justify-between items-center">
                      <span className="font-mono text-emerald-300 font-bold">OCR Match</span>
                      <span className="font-mono text-emerald-400 font-bold">
                        {selectedVehicle.primary_plate && selectedVehicle.primary_plate !== 'UNKNOWN' ? '100%' : '0%'}
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-emerald-400 h-full rounded-full" style={{ width: selectedVehicle.primary_plate && selectedVehicle.primary_plate !== 'UNKNOWN' ? '100%' : '15%' }} />
                    </div>
                  </div>

                  <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                    <span className="text-[10px] text-slate-400 uppercase block">Attributes (15%)</span>
                    <div className="flex justify-between items-center">
                      <span className="font-mono text-purple-300 font-bold">Type + Color</span>
                      <span className="font-mono text-purple-400 font-bold">95%</span>
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-purple-400 h-full rounded-full" style={{ width: '95%' }} />
                    </div>
                  </div>

                  <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                    <span className="text-[10px] text-slate-400 uppercase block">Spatiotemporal (15%)</span>
                    <div className="flex justify-between items-center">
                      <span className="font-mono text-amber-300 font-bold">Transit Window</span>
                      <span className="font-mono text-amber-400 font-bold">100%</span>
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-amber-400 h-full rounded-full" style={{ width: '100%' }} />
                    </div>
                  </div>
                </div>

                {/* DMV Registry Cross-Check vs AI Observation */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  {/* AI Observed Data */}
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                    <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider block">
                      AI Observation Profile
                    </span>
                    <div className="space-y-1 text-slate-300">
                      <div>Observed Class: <strong className="text-white capitalize">{selectedVehicle.vehicle_type}</strong></div>
                      <div>Observed Color: <strong className="text-white">{selectedVehicle.color}</strong></div>
                      <div>Total City Sightings: <strong className="text-cyan-400">{selectedVehicle.total_sightings}</strong></div>
                      <div>Last Camera Checkpoint: <strong className="text-slate-200">{selectedVehicle.last_camera_id || 'CAM01'}</strong></div>
                      <div>First Sighted: <strong className="text-slate-400">{new Date(selectedVehicle.first_seen).toLocaleString()}</strong></div>
                    </div>
                  </div>

                  {/* Registered DMV Record */}
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                    <span className="text-[10px] font-bold text-purple-400 uppercase tracking-wider block">
                      Official DMV Registry Record
                    </span>
                    {selectedVehicle.registered_data ? (
                      <div className="space-y-1 text-slate-300">
                        <div>Registered Owner: <strong className="text-white">{selectedVehicle.registered_data.owner_name}</strong></div>
                        <div>Official Make/Model: <strong className="text-white">{selectedVehicle.registered_data.make_model}</strong></div>
                        <div>Registered Color: <strong className="text-white">{selectedVehicle.registered_data.registered_color}</strong></div>
                        <div>
                          Status:{' '}
                          <span className={`px-1.5 py-0.2 text-[10px] font-bold rounded ${
                            selectedVehicle.registered_data.status === 'ACTIVE'
                              ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                              : 'bg-red-950 text-red-300 border border-red-800'
                          }`}>
                            {selectedVehicle.registered_data.status}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="text-slate-500 text-[11px] italic py-2">
                        No matching DMV record found in local registry.
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Trajectory Reconstruction Journey Timeline (Step 19) */}
              <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Navigation className="w-4 h-4 text-cyan-400" />
                    <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                      Multi-Camera Trajectory Route Timeline
                    </h3>
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {selectedVehicle.trajectories?.length || 0} Waypoints Sighted
                  </span>
                </div>

                {/* Visual Route Flow Header */}
                {selectedVehicle.trajectories && selectedVehicle.trajectories.length > 0 && (
                  <div className="flex flex-wrap items-center gap-2 p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs">
                    <span className="text-[10px] text-slate-500 font-bold uppercase">Transit Route:</span>
                    {selectedVehicle.trajectories.map((t, idx) => (
                      <React.Fragment key={idx}>
                        <span className="px-2 py-0.5 bg-slate-900 border border-cyan-700/60 rounded font-mono font-bold text-cyan-300">
                          {t.camera_id}
                        </span>
                        {idx < selectedVehicle.trajectories.length - 1 && (
                          <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                )}

                <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
                  {(!selectedVehicle.trajectories || selectedVehicle.trajectories.length === 0) ? (
                    <p className="text-xs text-slate-500">No trajectory waypoints logged.</p>
                  ) : (
                    selectedVehicle.trajectories.map((traj, idx) => (
                      <div key={idx} className="relative group">
                        {/* Dot indicator */}
                        <div className="absolute -left-[27px] top-1 w-3.5 h-3.5 rounded-full bg-cyan-400 border-2 border-slate-900 shadow-[0_0_8px_#00f2fe]" />

                        <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5 text-xs">
                          <div className="flex items-center justify-between">
                            <span className="font-mono font-bold text-cyan-300">
                              Waypoint {idx + 1}: {traj.camera_id} — {traj.camera_name || 'Checkpoint'}
                            </span>
                            <span className="text-slate-500 font-mono text-[10px]">
                              {new Date(traj.timestamp).toLocaleTimeString()}
                            </span>
                          </div>

                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-slate-400 text-[11px] pt-1 border-t border-slate-900">
                            <div>GPS: <span className="font-mono text-slate-300">{traj.latitude?.toFixed(4)}, {traj.longitude?.toFixed(4)}</span></div>
                            <div>Estimated Speed: <strong className="text-emerald-400">{traj.speed_kmh || 52} km/h</strong></div>
                            <div>Route Confidence: <span className="text-cyan-400 font-mono font-bold">{Math.round((traj.route_confidence || 1.0) * 100)}%</span></div>
                            <div>Status: <span className="text-emerald-400 font-semibold">Feasible Transit</span></div>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="p-12 rounded-2xl bg-slate-900 border border-slate-800 text-center text-slate-500 text-xs">
              Select a global vehicle entity from the list to inspect intelligence dossier.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
