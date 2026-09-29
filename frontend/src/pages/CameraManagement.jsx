import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Camera, 
  Plus, 
  Play, 
  Square, 
  Eye, 
  Edit2, 
  Trash2, 
  Search, 
  Filter, 
  RefreshCw, 
  AlertCircle, 
  CheckCircle2, 
  Video, 
  Radio,
  MapPin,
  Compass,
  X,
  Layers
} from 'lucide-react';
import { api } from '../services/api';

export default function CameraManagement() {
  const navigate = useNavigate();
  const [cameras, setCameras] = useState([]);
  const [stats, setStats] = useState({ total_cameras: 0, online_cameras: 0, offline_cameras: 0, active_streams: 0 });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState({});
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedZone, setSelectedZone] = useState('ALL');

  // Modals state
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedCamera, setSelectedCamera] = useState(null);
  const [cameraToDelete, setCameraToDelete] = useState(null);

  // Form states
  const initialForm = {
    camera_id: '',
    camera_name: '',
    location_name: '',
    latitude: 13.0827,
    longitude: 80.2707,
    zone: 'Zone A - Downtown',
    direction: 'NORTHBOUND',
    source_type: 'LOCAL_VIDEO',
    source_url: '',
    local_video_path: 'backend/videos/demo_traffic_cam01.mp4',
    description: '',
    is_demo: true
  };
  const [formData, setFormData] = useState(initialForm);
  const [formError, setFormError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchCameraData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [camList, statsData] = await Promise.all([
        api.getCameras(),
        api.getCameraStats()
      ]);
      setCameras(camList);
      setStats(statsData);
    } catch (err) {
      setError(err.message || 'Failed to load camera registry.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCameraData();
    const interval = setInterval(() => {
      // Background telemetry refresh
      api.getCameraStats().then(setStats).catch(() => {});
      api.getCameras().then(setCameras).catch(() => {});
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleStartStream = async (camId) => {
    setActionLoading(prev => ({ ...prev, [camId]: true }));
    try {
      await api.startCamera(camId);
      await fetchCameraData();
    } catch (err) {
      alert(`Error starting stream: ${err.message}`);
    } finally {
      setActionLoading(prev => ({ ...prev, [camId]: false }));
    }
  };

  const handleStopStream = async (camId) => {
    setActionLoading(prev => ({ ...prev, [camId]: true }));
    try {
      await api.stopCamera(camId);
      await fetchCameraData();
    } catch (err) {
      alert(`Error stopping stream: ${err.message}`);
    } finally {
      setActionLoading(prev => ({ ...prev, [camId]: false }));
    }
  };

  const handleOpenAddModal = () => {
    setFormData(initialForm);
    setFormError(null);
    setIsAddModalOpen(true);
  };

  const handleOpenEditModal = (cam) => {
    setSelectedCamera(cam);
    setFormData({
      camera_name: cam.camera_name,
      location_name: cam.location_name,
      latitude: cam.latitude,
      longitude: cam.longitude,
      zone: cam.zone,
      direction: cam.direction,
      source_type: cam.source_type,
      source_url: cam.source_url || '',
      local_video_path: cam.local_video_path || '',
      description: cam.description || '',
      is_demo: cam.is_demo
    });
    setFormError(null);
    setIsEditModalOpen(true);
  };

  const handleCreateCamera = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setFormError(null);
    try {
      await api.createCamera({
        ...formData,
        latitude: parseFloat(formData.latitude),
        longitude: parseFloat(formData.longitude)
      });
      setIsAddModalOpen(false);
      await fetchCameraData();
    } catch (err) {
      setFormError(err.message || 'Failed to create camera.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateCamera = async (e) => {
    e.preventDefault();
    if (!selectedCamera) return;
    setIsSubmitting(true);
    setFormError(null);
    try {
      await api.updateCamera(selectedCamera.camera_id, {
        ...formData,
        latitude: parseFloat(formData.latitude),
        longitude: parseFloat(formData.longitude)
      });
      setIsEditModalOpen(false);
      await fetchCameraData();
    } catch (err) {
      setFormError(err.message || 'Failed to update camera.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteCamera = async () => {
    if (!cameraToDelete) return;
    try {
      await api.deleteCamera(cameraToDelete.camera_id);
      setCameraToDelete(null);
      await fetchCameraData();
    } catch (err) {
      alert(`Error deleting camera: ${err.message}`);
    }
  };

  // Filtered cameras
  const filteredCameras = cameras.filter(cam => {
    const matchesSearch = 
      cam.camera_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      cam.camera_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      cam.location_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesZone = selectedZone === 'ALL' || cam.zone === selectedZone;
    return matchesSearch && matchesZone;
  });

  const availableZones = ['ALL', ...new Set(cameras.map(c => c.zone))];

  return (
    <div className="space-y-6 animate-fade-in">
      
      {/* Top Banner / Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-slate-900/90 via-slate-900/60 to-cyan-950/30 border border-slate-800 backdrop-blur-xl">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
              CCTV NODE REGISTRY
            </span>
            <span className="text-slate-500 font-mono text-xs">•</span>
            <span className="text-slate-400 font-mono text-xs">OPENCV VIDEO INGESTION</span>
          </div>
          <h2 className="text-2xl font-black tracking-tight text-white uppercase">
            CAMERA NODE MANAGEMENT
          </h2>
          <p className="text-sm text-slate-400">
            Configure CCTV node feeds, assign video sources, monitor capture states, and provision stream links.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchCameraData}
            disabled={isLoading}
            className="p-2.5 rounded-xl bg-slate-950/80 hover:bg-slate-800 border border-slate-800 text-slate-300 transition"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>

          <button
            onClick={handleOpenAddModal}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs transition shadow-[0_0_20px_rgba(6,182,212,0.3)]"
          >
            <Plus className="w-4 h-4" />
            <span>Add Camera Node</span>
          </button>
        </div>
      </div>

      {/* Real Statistics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-1">
          <div className="text-[10px] uppercase font-bold text-slate-500 font-mono">Total Cameras</div>
          <div className="text-2xl font-black text-white font-mono">{stats.total_cameras}</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-1">
          <div className="text-[10px] uppercase font-bold text-slate-500 font-mono">Online Nodes</div>
          <div className="text-2xl font-black text-emerald-400 font-mono">{stats.online_cameras}</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-1">
          <div className="text-[10px] uppercase font-bold text-slate-500 font-mono">Standby / Stopped</div>
          <div className="text-2xl font-black text-slate-400 font-mono">{stats.offline_cameras}</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-1">
          <div className="text-[10px] uppercase font-bold text-slate-500 font-mono">Active Streams</div>
          <div className="text-2xl font-black text-cyan-400 font-mono">{stats.active_streams}</div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
            <span className="text-xs font-mono">{error}</span>
          </div>
          <button onClick={fetchCameraData} className="text-xs font-bold text-rose-300 hover:underline">Retry</button>
        </div>
      )}

      {/* Filters Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/50 border border-slate-800">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by ID, name, or location..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto overflow-x-auto">
          <span className="text-[10px] font-mono text-slate-500 uppercase shrink-0">Zone Filter:</span>
          {availableZones.map(zone => (
            <button
              key={zone}
              onClick={() => setSelectedZone(zone)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition shrink-0 ${
                selectedZone === zone
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              {zone}
            </button>
          ))}
        </div>
      </div>

      {/* Cameras Table / Grid */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800 overflow-hidden backdrop-blur-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 uppercase font-mono text-[11px] border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4">Camera Node</th>
                <th className="py-3.5 px-4">Location & GIS</th>
                <th className="py-3.5 px-4">Zone</th>
                <th className="py-3.5 px-4">Direction</th>
                <th className="py-3.5 px-4">Source Type</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {isLoading && cameras.length === 0 ? (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-slate-500 font-mono">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-cyan-400" />
                    Loading Camera Nodes...
                  </td>
                </tr>
              ) : filteredCameras.length === 0 ? (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-slate-500 font-mono">
                    No camera nodes found matching criteria.
                  </td>
                </tr>
              ) : (
                filteredCameras.map((cam) => {
                  const isOnline = cam.status === 'ONLINE';
                  const isError = cam.status === 'ERROR';
                  const isProcessingAction = actionLoading[cam.camera_id];

                  return (
                    <tr key={cam.camera_id} className="hover:bg-slate-800/30 transition">
                      
                      {/* Camera Info */}
                      <td className="py-3.5 px-4">
                        <div className="flex items-center space-x-3">
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-mono font-bold text-xs ${
                            isOnline 
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' 
                              : 'bg-slate-800 text-slate-400 border border-slate-700'
                          }`}>
                            <Camera className="w-4 h-4" />
                          </div>
                          <div>
                            <div className="font-bold text-white flex items-center space-x-2">
                              <span>{cam.camera_id}</span>
                              {cam.is_demo && (
                                <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                                  DEMO CAMERA
                                </span>
                              )}
                            </div>
                            <div className="text-[11px] text-slate-400">{cam.camera_name}</div>
                          </div>
                        </div>
                      </td>

                      {/* Location & GIS */}
                      <td className="py-3.5 px-4 font-mono">
                        <div className="text-slate-200">{cam.location_name}</div>
                        <div className="text-[10px] text-slate-500 flex items-center space-x-1 mt-0.5">
                          <MapPin className="w-3 h-3 text-cyan-400/70" />
                          <span>{cam.latitude?.toFixed(4)}, {cam.longitude?.toFixed(4)}</span>
                        </div>
                      </td>

                      {/* Zone */}
                      <td className="py-3.5 px-4 font-mono text-slate-300">
                        {cam.zone}
                      </td>

                      {/* Direction */}
                      <td className="py-3.5 px-4 font-mono text-[11px]">
                        <span className="px-2 py-0.5 rounded bg-slate-950 text-cyan-300 border border-slate-800">
                          {cam.direction}
                        </span>
                      </td>

                      {/* Source */}
                      <td className="py-3.5 px-4 font-mono text-[11px]">
                        <div className="text-slate-300 font-semibold">{cam.source_type}</div>
                        <div className="text-[10px] text-slate-500 truncate max-w-[140px]" title={cam.local_video_path || cam.source_url}>
                          {cam.local_video_path ? cam.local_video_path.split('/').pop() : (cam.source_url || 'N/A')}
                        </div>
                      </td>

                      {/* Status */}
                      <td className="py-3.5 px-4">
                        <div className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[10px] font-mono font-bold border ${
                          isOnline
                            ? 'bg-emerald-950/50 text-emerald-300 border-emerald-500/40 shadow-[0_0_10px_rgba(16,185,129,0.2)]'
                            : isError
                            ? 'bg-rose-950/50 text-rose-300 border-rose-500/40'
                            : 'bg-slate-950 text-slate-400 border-slate-800'
                        }`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${
                            isOnline ? 'bg-emerald-400 animate-ping' : isError ? 'bg-rose-400' : 'bg-slate-500'
                          }`} />
                          <span>{cam.status}</span>
                        </div>
                      </td>

                      {/* Actions */}
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end space-x-1.5">
                          
                          {/* Start / Stop Stream */}
                          {isOnline ? (
                            <button
                              onClick={() => handleStopStream(cam.camera_id)}
                              disabled={isProcessingAction}
                              title="Stop Video Stream"
                              className="p-1.5 rounded-lg bg-amber-950/40 hover:bg-amber-900/60 text-amber-300 border border-amber-500/30 transition disabled:opacity-50"
                            >
                              <Square className="w-3.5 h-3.5" />
                            </button>
                          ) : (
                            <button
                              onClick={() => handleStartStream(cam.camera_id)}
                              disabled={isProcessingAction}
                              title="Start Video Ingestion"
                              className="p-1.5 rounded-lg bg-emerald-950/40 hover:bg-emerald-900/60 text-emerald-300 border border-emerald-500/30 transition disabled:opacity-50"
                            >
                              <Play className="w-3.5 h-3.5" />
                            </button>
                          )}

                          {/* View Live Stream Page */}
                          <button
                            onClick={() => navigate(`/live-cameras?camera=${cam.camera_id}`)}
                            title="Open Live Preview"
                            className="p-1.5 rounded-lg bg-cyan-950/40 hover:bg-cyan-900/60 text-cyan-300 border border-cyan-500/30 transition"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>

                          {/* Edit Camera */}
                          <button
                            onClick={() => handleOpenEditModal(cam)}
                            title="Edit Node Config"
                            className="p-1.5 rounded-lg bg-slate-950 hover:bg-slate-800 text-slate-300 border border-slate-800 transition"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>

                          {/* Delete Camera */}
                          <button
                            onClick={() => setCameraToDelete(cam)}
                            title="Delete Node"
                            className="p-1.5 rounded-lg bg-rose-950/30 hover:bg-rose-900/50 text-rose-400 border border-rose-800/40 transition"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>

                        </div>
                      </td>

                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ADD CAMERA MODAL */}
      {isAddModalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-xl bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2 text-white font-black uppercase text-sm tracking-wide">
                <Plus className="w-4 h-4 text-cyan-400" />
                <span>Add Traffic Camera Node</span>
              </div>
              <button onClick={() => setIsAddModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            {formError && (
              <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-500/40 text-rose-200 text-xs font-mono">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateCamera} className="space-y-4 text-xs font-mono">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-400 mb-1">Camera ID *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. CAM05"
                    value={formData.camera_id}
                    onChange={(e) => setFormData({ ...formData, camera_id: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500 uppercase"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Camera Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. South Bypass Cam"
                    value={formData.camera_name}
                    onChange={(e) => setFormData({ ...formData, camera_name: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Location Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. South Bypass Intersection"
                  value={formData.location_name}
                  onChange={(e) => setFormData({ ...formData, location_name: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-400 mb-1">Latitude *</label>
                  <input
                    type="number"
                    step="0.0001"
                    required
                    value={formData.latitude}
                    onChange={(e) => setFormData({ ...formData, latitude: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Longitude *</label>
                  <input
                    type="number"
                    step="0.0001"
                    required
                    value={formData.longitude}
                    onChange={(e) => setFormData({ ...formData, longitude: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-400 mb-1">Urban Zone</label>
                  <input
                    type="text"
                    value={formData.zone}
                    onChange={(e) => setFormData({ ...formData, zone: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Direction</label>
                  <select
                    value={formData.direction}
                    onChange={(e) => setFormData({ ...formData, direction: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="NORTHBOUND">NORTHBOUND</option>
                    <option value="SOUTHBOUND">SOUTHBOUND</option>
                    <option value="EASTBOUND">EASTBOUND</option>
                    <option value="WESTBOUND">WESTBOUND</option>
                    <option value="BIDIRECTIONAL">BIDIRECTIONAL</option>
                    <option value="INTERSECTION">INTERSECTION</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Source Type</label>
                <select
                  value={formData.source_type}
                  onChange={(e) => setFormData({ ...formData, source_type: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="LOCAL_VIDEO">LOCAL_VIDEO (OpenCV File Ingest)</option>
                  <option value="RTSP">RTSP (Network Stream)</option>
                  <option value="WEBCAM">WEBCAM (Direct Hardware Device)</option>
                </select>
              </div>

              {formData.source_type === 'LOCAL_VIDEO' && (
                <div>
                  <label className="block text-slate-400 mb-1">Local Video Path</label>
                  <input
                    type="text"
                    placeholder="e.g. backend/videos/demo_traffic_cam01.mp4"
                    value={formData.local_video_path}
                    onChange={(e) => setFormData({ ...formData, local_video_path: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              )}

              {formData.source_type === 'RTSP' && (
                <div>
                  <label className="block text-slate-400 mb-1">RTSP Stream URL *</label>
                  <input
                    type="text"
                    required
                    placeholder="rtsp://admin:pass@192.168.1.100:554/live"
                    value={formData.source_url}
                    onChange={(e) => setFormData({ ...formData, source_url: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              )}

              {formData.source_type === 'WEBCAM' && (
                <div>
                  <label className="block text-slate-400 mb-1">Webcam Device Index</label>
                  <input
                    type="text"
                    placeholder="0"
                    value={formData.local_video_path}
                    onChange={(e) => setFormData({ ...formData, local_video_path: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              )}

              <div>
                <label className="block text-slate-400 mb-1">Description / Notes</label>
                <textarea
                  rows="2"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500 font-sans"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-300 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-bold transition disabled:opacity-50"
                >
                  {isSubmitting ? 'Registering...' : 'Register Camera'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* EDIT CAMERA MODAL */}
      {isEditModalOpen && selectedCamera && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-xl bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2 text-white font-black uppercase text-sm tracking-wide">
                <Edit2 className="w-4 h-4 text-cyan-400" />
                <span>Edit Camera Node: {selectedCamera.camera_id}</span>
              </div>
              <button onClick={() => setIsEditModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            {formError && (
              <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-500/40 text-rose-200 text-xs font-mono">
                {formError}
              </div>
            )}

            <form onSubmit={handleUpdateCamera} className="space-y-4 text-xs font-mono">
              <div>
                <label className="block text-slate-400 mb-1">Camera Name</label>
                <input
                  type="text"
                  required
                  value={formData.camera_name}
                  onChange={(e) => setFormData({ ...formData, camera_name: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Location Name</label>
                <input
                  type="text"
                  required
                  value={formData.location_name}
                  onChange={(e) => setFormData({ ...formData, location_name: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-400 mb-1">Latitude</label>
                  <input
                    type="number"
                    step="0.0001"
                    required
                    value={formData.latitude}
                    onChange={(e) => setFormData({ ...formData, latitude: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Longitude</label>
                  <input
                    type="number"
                    step="0.0001"
                    required
                    value={formData.longitude}
                    onChange={(e) => setFormData({ ...formData, longitude: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-400 mb-1">Zone</label>
                  <input
                    type="text"
                    value={formData.zone}
                    onChange={(e) => setFormData({ ...formData, zone: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Direction</label>
                  <select
                    value={formData.direction}
                    onChange={(e) => setFormData({ ...formData, direction: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="NORTHBOUND">NORTHBOUND</option>
                    <option value="SOUTHBOUND">SOUTHBOUND</option>
                    <option value="EASTBOUND">EASTBOUND</option>
                    <option value="WESTBOUND">WESTBOUND</option>
                    <option value="BIDIRECTIONAL">BIDIRECTIONAL</option>
                    <option value="INTERSECTION">INTERSECTION</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Source Type</label>
                <select
                  value={formData.source_type}
                  onChange={(e) => setFormData({ ...formData, source_type: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="LOCAL_VIDEO">LOCAL_VIDEO</option>
                  <option value="RTSP">RTSP</option>
                  <option value="WEBCAM">WEBCAM</option>
                </select>
              </div>

              {formData.source_type === 'LOCAL_VIDEO' && (
                <div>
                  <label className="block text-slate-400 mb-1">Local Video Path</label>
                  <input
                    type="text"
                    value={formData.local_video_path}
                    onChange={(e) => setFormData({ ...formData, local_video_path: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              )}

              {formData.source_type === 'RTSP' && (
                <div>
                  <label className="block text-slate-400 mb-1">RTSP URL</label>
                  <input
                    type="text"
                    value={formData.source_url}
                    onChange={(e) => setFormData({ ...formData, source_url: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              )}

              <div>
                <label className="block text-slate-400 mb-1">Description</label>
                <textarea
                  rows="2"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500 font-sans"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsEditModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-300 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-bold transition disabled:opacity-50"
                >
                  {isSubmitting ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DELETE CONFIRMATION MODAL */}
      {cameraToDelete && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-md bg-slate-900 border border-rose-500/40 rounded-2xl p-6 space-y-4">
            <div className="flex items-center space-x-3 text-rose-400 font-bold">
              <AlertCircle className="w-6 h-6" />
              <span>Confirm Camera Deletion</span>
            </div>
            <p className="text-xs text-slate-300">
              Are you sure you want to delete camera node <span className="font-bold text-white font-mono">{cameraToDelete.camera_id}</span> ({cameraToDelete.camera_name})? Any active video stream will be terminated.
            </p>
            <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800">
              <button
                onClick={() => setCameraToDelete(null)}
                className="px-4 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-300 hover:text-white text-xs font-mono"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteCamera}
                className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-mono font-bold transition"
              >
                Delete Camera
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
