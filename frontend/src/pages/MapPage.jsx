import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Camera, Car, Radio, Navigation, Gauge, RefreshCw, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

// Custom Tactical Camera Icon
const createCameraIcon = (cameraId, status) => {
  const isOnline = status === 'ACTIVE';
  return L.divIcon({
    className: 'custom-camera-marker',
    html: `
      <div style="
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background: ${isOnline ? '#0f172a' : '#450a0a'};
        border: 2px solid ${isOnline ? '#00f2fe' : '#ef4444'};
        box-shadow: 0 0 15px ${isOnline ? 'rgba(0,242,254,0.6)' : 'rgba(239,68,68,0.6)'};
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-family: monospace;
        font-size: 10px;
        font-weight: 800;
      ">
        ${cameraId}
      </div>
    `,
    iconSize: [38, 38],
    iconAnchor: [19, 19]
  });
};

export default function MapPage() {
  const [cameras, setCameras] = useState([]);
  const [topology, setTopology] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState('TN38AB1234');
  const [vehicleTrajectory, setVehicleTrajectory] = useState([]);
  const [searchPlateInput, setSearchPlateInput] = useState('');
  const [loading, setLoading] = useState(true);

  const cityCenter = [13.0150, 80.2520]; // City center coordinate

  const loadMapData = async () => {
    try {
      const [cams, top] = await Promise.all([
        api.getCameras(),
        api.getTopology()
      ]);
      setCameras(cams);
      setTopology(top);
    } catch (err) {
      console.error('Error loading map data:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadVehiclePath = async (plate) => {
    if (!plate) return;
    try {
      const traj = await api.getTrajectory(plate);
      setVehicleTrajectory(traj);
    } catch (err) {
      console.error('Trajectory error:', err);
      setVehicleTrajectory([]);
    }
  };

  useEffect(() => {
    loadMapData();
    loadVehiclePath(selectedVehicle);
    const interval = setInterval(loadMapData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleTrajectorySearch = (e) => {
    e.preventDefault();
    if (searchPlateInput.trim()) {
      const p = searchPlateInput.trim().toUpperCase();
      setSelectedVehicle(p);
      loadVehiclePath(p);
    }
  };

  // Build coordinate lookup for topology polylines
  const camCoords = {};
  cameras.forEach(c => {
    camCoords[c.camera_id] = [c.latitude, c.longitude];
  });

  // Build trajectory polyline
  const trajectoryPositions = vehicleTrajectory.map(t => [t.latitude, t.longitude]);

  return (
    <div className="space-y-4 pb-10">
      {/* Top Map Control Bar */}
      <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Radio className="w-4 h-4 text-cyan-400 animate-pulse" />
            <span className="text-[10px] uppercase font-bold text-cyan-400 tracking-wider">
              GEOSPATIAL TOPOLOGY & CAMERA GRID
            </span>
          </div>
          <h1 className="text-lg font-black text-slate-100 mt-0.5">Interactive City Surveillance Map</h1>
          <p className="text-xs text-slate-400">
            Real-time multi-camera graph topology with breadcrumb trajectory tracking & speed inference.
          </p>
        </div>

        {/* Trajectory Tracker Form */}
        <form onSubmit={handleTrajectorySearch} className="flex items-center space-x-2">
          <input
            type="text"
            placeholder="Plot vehicle (e.g. TN38AB1234)..."
            value={searchPlateInput}
            onChange={(e) => setSearchPlateInput(e.target.value)}
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
          />
          <button
            type="submit"
            className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-lg flex items-center space-x-1 transition"
          >
            <Navigation className="w-3.5 h-3.5" />
            <span>Plot Route</span>
          </button>
        </form>
      </div>

      {/* Map Container */}
      <div className="relative h-[680px] w-full rounded-2xl overflow-hidden border border-slate-800 shadow-2xl bg-slate-950">
        <MapContainer
          center={cityCenter}
          zoom={12}
          scrollWheelZoom={true}
          className="h-full w-full"
        >
          {/* Tile Layer (OSM with dark filter applied in index.css) */}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Topology Network Edges */}
          {topology.map((edge, idx) => {
            const p1 = camCoords[edge.source_camera];
            const p2 = camCoords[edge.destination_camera];
            if (!p1 || !p2) return null;

            return (
              <Polyline
                key={`topo-${idx}`}
                positions={[p1, p2]}
                pathOptions={{
                  color: '#00f2fe',
                  weight: 3,
                  opacity: 0.4,
                  dashArray: '6, 8'
                }}
              >
                <Tooltip sticky>
                  <div className="text-xs font-mono">
                    <span className="font-bold">{edge.source_camera} → {edge.destination_camera}</span>
                    <br />
                    Distance: {edge.distance_km} km | Min Time: {edge.expected_min_travel_time_sec}s
                  </div>
                </Tooltip>
              </Polyline>
            );
          })}

          {/* Vehicle Reconstructed Trajectory Path */}
          {trajectoryPositions.length > 1 && (
            <Polyline
              positions={trajectoryPositions}
              pathOptions={{
                color: '#ec4899',
                weight: 5,
                opacity: 0.9,
                lineCap: 'round'
              }}
            >
              <Tooltip sticky>
                <div className="text-xs font-mono font-bold text-pink-400">
                  RECONSTRUCTED JOURNEY: {selectedVehicle}
                </div>
              </Tooltip>
            </Polyline>
          )}

          {/* Camera Markers */}
          {cameras.map((cam) => (
            <Marker
              key={cam.camera_id}
              position={[cam.latitude, cam.longitude]}
              icon={createCameraIcon(cam.camera_id, cam.status)}
            >
              <Popup className="custom-leaflet-popup">
                <div className="p-1 space-y-2 text-xs w-64">
                  <div className="flex items-center justify-between border-b border-slate-700 pb-1.5">
                    <span className="font-bold text-cyan-400 font-mono">{cam.camera_id}</span>
                    <span className="text-[10px] text-emerald-400 font-semibold uppercase">{cam.status}</span>
                  </div>

                  <p className="font-semibold text-slate-100">{cam.camera_name}</p>
                  <p className="text-[11px] text-slate-400">{cam.location_name}</p>

                  {/* Mini Stream Preview in Popup */}
                  <div className="relative aspect-video rounded bg-black overflow-hidden border border-slate-700">
                    <img
                      src={api.getLiveStreamUrl(cam.camera_id)}
                      alt={cam.camera_id}
                      className="w-full h-full object-cover"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-1.5 text-[11px] pt-1">
                    <div className="bg-slate-800 p-1.5 rounded">
                      <span className="text-slate-400">Flow:</span> <span className="text-slate-200 font-bold">{cam.active_vehicles_count || 3} v</span>
                    </div>
                    <div className="bg-slate-800 p-1.5 rounded">
                      <span className="text-slate-400">Avg Spd:</span> <span className="text-emerald-400 font-bold">{cam.average_speed_kmh || 48} km/h</span>
                    </div>
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>

        {/* Legend Floating Card */}
        <div className="absolute top-4 right-4 z-[1000] p-3 rounded-xl bg-slate-950/90 backdrop-blur-md border border-slate-800 text-xs space-y-2 shadow-xl">
          <span className="font-bold text-slate-300 text-[11px] uppercase tracking-wider block">
            Map Legend & Layers
          </span>
          <div className="space-y-1 text-[11px] text-slate-400">
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 rounded-full bg-cyan-400 shadow-[0_0_8px_#00f2fe]" />
              <span>Surveillance Camera Node</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-4 h-0.5 bg-cyan-400 border border-dashed border-cyan-300" />
              <span>Camera Topology Highway Route</span>
            </div>
            {vehicleTrajectory.length > 0 && (
              <div className="flex items-center space-x-2 text-pink-400 font-bold">
                <span className="w-4 h-1 bg-pink-500 rounded" />
                <span>Tracked Vehicle: {selectedVehicle}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
