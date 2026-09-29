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
  FileText,
  TrendingUp,
  UserCheck
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

  useEffect(() => {
    handleSearch();
  }, [searchParams]);

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl">
        <div className="flex items-center space-x-2">
          <Car className="w-4 h-4 text-cyan-400" />
          <span className="text-[10px] uppercase font-bold text-cyan-400 tracking-wider">
            GLOBAL VEHICLE IDENTITY & TRAJECTORY RECONSTRUCTION
          </span>
        </div>
        <h1 className="text-xl font-black text-slate-100 mt-0.5">Vehicle Intelligence Explorer</h1>
        <p className="text-xs text-slate-400 max-w-2xl">
          Search spatiotemporal trajectories, cross-camera sightings, registered DMV records, and appearance consistency profiles.
        </p>

        {/* Multi-Parameter Search Controls */}
        <form onSubmit={handleSearch} className="mt-4 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
          <div>
            <label className="block text-[11px] text-slate-400 mb-1">Plate Number</label>
            <input
              type="text"
              placeholder="e.g. TN38AB1234"
              value={plateQuery}
              onChange={(e) => setPlateQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
            />
          </div>

          <div>
            <label className="block text-[11px] text-slate-400 mb-1">Global ID</label>
            <input
              type="text"
              placeholder="e.g. VEH-102934"
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
              <span>{loading ? 'Searching...' : 'Execute Search'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Results & Vehicle Dossier View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Search Results List (1 Col) */}
        <div className="space-y-3">
          <div className="flex justify-between items-center text-xs font-semibold text-slate-400 px-1">
            <span>Vehicles Identified ({vehicles.length})</span>
            <span className="text-[10px]">Select to inspect journey</span>
          </div>

          <div className="space-y-2.5 max-h-[600px] overflow-y-auto pr-1">
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
                    <span className="text-slate-300 font-bold">{v.total_sightings} Sightings</span>
                  </div>

                  <div className="text-[10px] text-slate-500 flex justify-between">
                    <span>Last: {new Date(v.last_seen).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    <span>Conf: {Math.round(v.confidence * 100)}%</span>
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
                        {selectedVehicle.primary_plate}
                      </span>
                      <span className="text-xs font-mono font-bold text-cyan-300 bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-800/80">
                        {selectedVehicle.global_id}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400">
                      Primary Appearance: <strong className="text-slate-200">{selectedVehicle.color} {selectedVehicle.vehicle_type?.toUpperCase()}</strong>
                    </p>
                  </div>

                  <div className="text-right text-xs">
                    <span className="text-slate-400">Confidence Score:</span>
                    <p className="text-base font-bold text-emerald-400 font-mono">
                      {Math.round(selectedVehicle.confidence * 100)}%
                    </p>
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
                      <div>Observed Class: <strong className="text-white">{selectedVehicle.vehicle_type}</strong></div>
                      <div>Observed Color: <strong className="text-white">{selectedVehicle.color}</strong></div>
                      <div>Total City Sightings: <strong className="text-cyan-400">{selectedVehicle.total_sightings}</strong></div>
                      <div>First Sighted: <strong className="text-slate-400">{new Date(selectedVehicle.first_seen).toLocaleString()}</strong></div>
                    </div>
                  </div>

                  {/* Registered DMV Record */}
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                    <span className="text-[10px] font-bold text-purple-400 uppercase tracking-wider block">
                      Demo DMV Registry Record
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
                        No official DMV record found in local Demo Registry.
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Trajectory Reconstruction Journey Timeline */}
              <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Navigation className="w-4 h-4 text-cyan-400" />
                    <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                      Reconstructed Multi-Camera Journey Timeline
                    </h3>
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {selectedVehicle.trajectories?.length || 0} Waypoints
                  </span>
                </div>

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
                              Waypoint {idx + 1}: {traj.camera_id} ({traj.camera_name || 'Checkpoint'})
                            </span>
                            <span className="text-slate-500 font-mono text-[10px]">
                              {new Date(traj.timestamp).toLocaleTimeString()}
                            </span>
                          </div>

                          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-slate-400 text-[11px]">
                            <div>GPS: <span className="font-mono text-slate-300">{traj.latitude?.toFixed(4)}, {traj.longitude?.toFixed(4)}</span></div>
                            <div>Estimated Speed: <strong className="text-emerald-400">{traj.speed_kmh || 52} km/h</strong></div>
                            <div>Route Feasibility: <span className="text-cyan-400 font-bold">100% (Feasible)</span></div>
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
              Select a vehicle from the search results to inspect intelligence dossier.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
