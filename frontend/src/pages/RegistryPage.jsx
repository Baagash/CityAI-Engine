import React, { useState, useEffect } from 'react';
import { 
  Database, 
  Plus, 
  Search, 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle,
  User,
  Car,
  FileBadge
} from 'lucide-react';
import { api } from '../services/api';

export default function RegistryPage() {
  const [vehicles, setVehicles] = useState([]);
  const [searchPlate, setSearchPlate] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [loading, setLoading] = useState(true);

  // Add Form State
  const [newPlate, setNewPlate] = useState('');
  const [newType, setNewType] = useState('sedan');
  const [newMake, setNewMake] = useState('');
  const [newColor, setNewColor] = useState('WHITE');
  const [newOwner, setNewOwner] = useState('');
  const [newNotes, setNewNotes] = useState('');

  const loadRegistry = async () => {
    setLoading(true);
    try {
      const data = await api.getRegistry({
        plate: searchPlate,
        status: statusFilter
      });
      setVehicles(data);
    } catch (err) {
      console.error('Registry error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRegistry();
  }, [searchPlate, statusFilter]);

  const handleAddVehicle = async (e) => {
    e.preventDefault();
    try {
      await api.addRegistryVehicle({
        registration_number: newPlate.toUpperCase().trim(),
        vehicle_type: newType,
        make_model: newMake,
        registered_color: newColor.toUpperCase(),
        owner_name: newOwner,
        notes: newNotes
      });
      setShowAddModal(false);
      setNewPlate('');
      setNewMake('');
      setNewOwner('');
      setNewNotes('');
      loadRegistry();
    } catch (err) {
      console.error('Add vehicle error:', err);
      alert('Failed to add vehicle: ' + err.message);
    }
  };

  const handleToggleFlag = async (regNumber, currentStatus) => {
    const newStatus = currentStatus === 'STOLEN' ? 'ACTIVE' : 'STOLEN';
    try {
      await api.flagRegistryVehicle(regNumber, newStatus);
      loadRegistry();
    } catch (err) {
      console.error('Flag error:', err);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Database className="w-4 h-4 text-purple-400" />
            <span className="text-[10px] uppercase font-bold text-purple-400 tracking-wider">
              OFFICIAL DMV/RTO MOCK DATABASE
            </span>
          </div>
          <h1 className="text-xl font-black text-slate-100 mt-0.5">Demo Vehicle Registry</h1>
          <p className="text-xs text-slate-400">
            Compare real-time AI computer vision observations against authorized DMV registration profiles to catch stolen plates and attribute mismatches.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold rounded-xl flex items-center space-x-1.5 transition shadow-lg shadow-purple-900/30 self-start md:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Enroll New Vehicle</span>
        </button>
      </div>

      {/* Search Toolbar */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="sm:col-span-2">
          <label className="block text-[11px] text-slate-400 mb-1">Search Registration Number</label>
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="e.g. TN38AB1234 or DL01CA1024..."
              value={searchPlate}
              onChange={(e) => setSearchPlate(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-400"
            />
          </div>
        </div>

        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Filter DMV Status</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-purple-400"
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="STOLEN">Stolen / Hotlist</option>
            <option value="SUSPENDED">Suspended</option>
          </select>
        </div>
      </div>

      {/* Registry Table */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900 overflow-hidden shadow-xl">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950 text-slate-400 font-semibold uppercase text-[10px] border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">Registration No.</th>
              <th className="py-3 px-4">Make & Model</th>
              <th className="py-3 px-4">Vehicle Type / Color</th>
              <th className="py-3 px-4">Registered Owner</th>
              <th className="py-3 px-4">DMV Status</th>
              <th className="py-3 px-4 text-right">Flag Test Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-sans">
            {vehicles.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-slate-500 text-xs">
                  No vehicles found in demo DMV registry.
                </td>
              </tr>
            ) : (
              vehicles.map((v) => (
                <tr key={v.id} className="hover:bg-slate-850/60 transition">
                  <td className="py-3 px-4 font-mono font-bold text-cyan-300">
                    <span className="px-2 py-0.5 bg-slate-950 border border-slate-700 rounded text-xs">
                      {v.registration_number}
                    </span>
                  </td>

                  <td className="py-3 px-4 text-slate-200 font-semibold">
                    {v.make_model}
                  </td>

                  <td className="py-3 px-4 text-slate-300">
                    {v.registered_color} {v.vehicle_type?.toUpperCase()}
                  </td>

                  <td className="py-3 px-4 text-slate-300">
                    {v.owner_name}
                  </td>

                  <td className="py-3 px-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      v.status === 'ACTIVE'
                        ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                        : 'bg-red-950 text-red-300 border border-red-800 animate-pulse'
                    }`}>
                      {v.status}
                    </span>
                  </td>

                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => handleToggleFlag(v.registration_number, v.status)}
                      className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                        v.status === 'STOLEN'
                          ? 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                          : 'bg-red-950 hover:bg-red-900/80 text-red-300 border border-red-800'
                      }`}
                    >
                      {v.status === 'STOLEN' ? 'Clear Stolen Flag' : 'Flag as STOLEN'}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Add Vehicle Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-700 rounded-2xl p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-slate-100">Enroll Vehicle in Demo DMV Registry</h3>
            <form onSubmit={handleAddVehicle} className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Registration Plate</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. TN38AB1234"
                    value={newPlate}
                    onChange={(e) => setNewPlate(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 uppercase font-mono"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Vehicle Type</label>
                  <select
                    value={newType}
                    onChange={(e) => setNewType(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                  >
                    <option value="sedan">Sedan</option>
                    <option value="suv">SUV</option>
                    <option value="truck">Truck</option>
                    <option value="bus">Bus</option>
                    <option value="motorcycle">Motorcycle</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Make & Model</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Honda City 1.5"
                    value={newMake}
                    onChange={(e) => setNewMake(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Registered Color</label>
                  <select
                    value={newColor}
                    onChange={(e) => setNewColor(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                  >
                    <option value="WHITE">White</option>
                    <option value="BLACK">Black</option>
                    <option value="SILVER">Silver / Grey</option>
                    <option value="BLUE">Blue</option>
                    <option value="RED">Red</option>
                    <option value="YELLOW">Yellow</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Registered Owner Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Anand R. (Downtown Residency)"
                  value={newOwner}
                  onChange={(e) => setNewOwner(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Notes</label>
                <textarea
                  rows={2}
                  placeholder="Optional notes or permit records..."
                  value={newNotes}
                  onChange={(e) => setNewNotes(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3.5 py-2 rounded-lg bg-slate-800 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-semibold"
                >
                  Enroll Vehicle
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
