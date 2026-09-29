import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  Car, 
  Truck, 
  Bus, 
  Bike, 
  Activity, 
  Cpu, 
  Layers, 
  Eye, 
  EyeOff, 
  Play, 
  Square, 
  RefreshCw, 
  Crosshair, 
  Sliders, 
  Upload, 
  CheckCircle, 
  AlertCircle,
  Clock,
  MapPin,
  Maximize2,
  Video
} from 'lucide-react';
import { api } from '../services/api';

const CLASS_CONFIG = {
  car: { label: 'Car', icon: Car, color: 'text-cyan-400 bg-cyan-950/60 border-cyan-500/40' },
  truck: { label: 'Truck', icon: Truck, color: 'text-amber-400 bg-amber-950/60 border-amber-500/40' },
  bus: { label: 'Bus', icon: Bus, color: 'text-purple-400 bg-purple-950/60 border-purple-500/40' },
  motorcycle: { label: 'Motorcycle', icon: Bike, color: 'text-emerald-400 bg-emerald-950/60 border-emerald-500/40' },
};

export default function VehicleDetection() {
  const [cameras, setCameras] = useState([]);
  const [selectedCameraId, setSelectedCameraId] = useState('CAM01');
  const [cameraStatus, setCameraStatus] = useState(null);
  const [isAnnotated, setIsAnnotated] = useState(true);
  const [activeTracks, setActiveTracks] = useState([]);
  const [historicalDetections, setHistoricalDetections] = useState([]);
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [error, setError] = useState(null);
  const [classFilter, setClassFilter] = useState('all');
  
  // Custom Image Upload Test State
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);

  // Fetch Camera List & Stats
  const fetchInitialData = useCallback(async () => {
    try {
      const [cams, detStats] = await Promise.all([
        api.getCameras(),
        api.getDetectionStats().catch(() => null)
      ]);
      setCameras(cams);
      if (cams.length > 0 && !cams.some(c => c.camera_id === selectedCameraId)) {
        setSelectedCameraId(cams[0].camera_id);
      }
      if (detStats) setStats(detStats);
    } catch (err) {
      setError(err.message || 'Failed to initialize detection console.');
    } finally {
      setIsLoading(false);
    }
  }, [selectedCameraId]);

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  // Poll Active Camera Telemetry & Tracks
  const pollCameraData = useCallback(async () => {
    if (!selectedCameraId) return;
    try {
      const [statusRes, tracksRes, histRes] = await Promise.all([
        api.getCameraStatus(selectedCameraId).catch(() => null),
        api.getActiveTracks(selectedCameraId).catch(() => []),
        api.getHistoricalDetections({ camera_id: selectedCameraId, limit: 15 }).catch(() => [])
      ]);

      if (statusRes) setCameraStatus(statusRes);
      setActiveTracks(tracksRes || []);
      setHistoricalDetections(histRes || []);
    } catch (err) {
      console.warn('Poll error:', err);
    }
  }, [selectedCameraId]);

  useEffect(() => {
    pollCameraData();
    const interval = setInterval(pollCameraData, 2000);
    return () => clearInterval(interval);
  }, [pollCameraData]);

  // Start Stream Action
  const handleStartStream = async () => {
    setIsActionLoading(true);
    try {
      await api.startCamera(selectedCameraId);
      await pollCameraData();
    } catch (err) {
      alert(`Start failed: ${err.message}`);
    } finally {
      setIsActionLoading(false);
    }
  };

  // Stop Stream Action
  const handleStopStream = async () => {
    setIsActionLoading(true);
    try {
      await api.stopCamera(selectedCameraId);
      await pollCameraData();
    } catch (err) {
      alert(`Stop failed: ${err.message}`);
    } finally {
      setIsActionLoading(false);
    }
  };

  // Upload Test Image
  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setTestResult(null);
    try {
      const res = await api.detectImage(file);
      setTestResult(res);
    } catch (err) {
      alert(`Image inference error: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const selectedCamObj = cameras.find(c => c.camera_id === selectedCameraId);
  const isStreaming = cameraStatus?.is_streaming || false;
  const streamUrl = api.getCameraStreamUrl(selectedCameraId, isAnnotated);

  const filteredDetections = historicalDetections.filter(d => {
    if (classFilter === 'all') return true;
    return d.vehicle_class === classFilter;
  });

  return (
    <div className="space-y-6">
      
      {/* Top Header & Telemetry Bar */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 bg-slate-900/80 backdrop-blur border border-slate-800 p-5 rounded-2xl shadow-xl">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <Crosshair className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                Vehicle Detection & Tracking
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 font-mono">
                  PHASE 3
                </span>
              </h1>
              <p className="text-xs text-slate-400">
                Ultralytics YOLOv8 inference & per-camera spatial tracking pipeline
              </p>
            </div>
          </div>
        </div>

        {/* Camera Selector Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto max-w-full pb-2 lg:pb-0">
          {cameras.map(cam => (
            <button
              key={cam.camera_id}
              onClick={() => setSelectedCameraId(cam.camera_id)}
              className={`px-3.5 py-2 rounded-xl text-xs font-mono font-medium transition-all flex items-center gap-2 border ${
                selectedCameraId === cam.camera_id
                  ? 'bg-cyan-500/20 text-cyan-200 border-cyan-500/40 shadow-lg shadow-cyan-950/50'
                  : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              <div className={`w-2 h-2 rounded-full ${cam.status === 'ONLINE' ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'}`} />
              {cam.camera_id}
            </button>
          ))}

          <button
            onClick={() => setIsUploadModalOpen(true)}
            className="px-3.5 py-2 rounded-xl text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1.5 transition-colors"
            title="Upload Test Frame for YOLO Inference"
          >
            <Upload className="w-3.5 h-3.5 text-cyan-400" />
            <span>Test Image</span>
          </button>
        </div>
      </div>

      {/* Telemetry Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        {/* Model Card */}
        <div className="bg-slate-900/60 border border-slate-800 p-3.5 rounded-xl">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span>AI Model</span>
          </div>
          <div className="text-sm font-bold font-mono text-white">
            {stats?.model_name || 'yolov8n.pt'}
          </div>
          <div className="text-[10px] text-cyan-400/80 mt-0.5 font-mono">
            {stats?.device?.toUpperCase() === 'CPU' ? 'CPU Mode' : 'CUDA Active'}
          </div>
        </div>

        {/* Processing FPS */}
        <div className="bg-slate-900/60 border border-slate-800 p-3.5 rounded-xl">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
            <Activity className="w-3.5 h-3.5 text-emerald-400" />
            <span>Processing FPS</span>
          </div>
          <div className="text-sm font-bold font-mono text-emerald-300">
            {cameraStatus?.processing_fps ? `${cameraStatus.processing_fps.toFixed(1)} FPS` : (isStreaming ? '25.0 FPS' : '0.0 FPS')}
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">
            {cameraStatus?.inference_ms ? `${cameraStatus.inference_ms.toFixed(1)} ms latency` : 'Paced capture'}
          </div>
        </div>

        {/* Active Local Tracks */}
        <div className="bg-slate-900/60 border border-slate-800 p-3.5 rounded-xl">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            <span>Active Tracks</span>
          </div>
          <div className="text-sm font-bold font-mono text-indigo-300">
            {activeTracks.length} Vehicles
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">
            Local to {selectedCameraId}
          </div>
        </div>

        {/* Total In-Camera Detections */}
        <div className="bg-slate-900/60 border border-slate-800 p-3.5 rounded-xl">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
            <Crosshair className="w-3.5 h-3.5 text-amber-400" />
            <span>Total Detections</span>
          </div>
          <div className="text-sm font-bold font-mono text-amber-300">
            {cameraStatus?.total_detections_count || 0}
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">
            Cumulative frames
          </div>
        </div>

        {/* Stream Resolution */}
        <div className="bg-slate-900/60 border border-slate-800 p-3.5 rounded-xl">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
            <Video className="w-3.5 h-3.5 text-purple-400" />
            <span>Resolution</span>
          </div>
          <div className="text-sm font-bold font-mono text-purple-300">
            {cameraStatus?.resolution || '640x360'}
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">
            Frame #{cameraStatus?.frame_number || 0}
          </div>
        </div>

        {/* Ingestion Status */}
        <div className="bg-slate-900/60 border border-slate-800 p-3.5 rounded-xl">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
            <span>Stream Status</span>
          </div>
          <div className={`text-sm font-bold font-mono ${isStreaming ? 'text-emerald-400' : 'text-slate-400'}`}>
            {isStreaming ? 'ONLINE' : 'STOPPED'}
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">
            {selectedCamObj?.zone || 'Downtown'}
          </div>
        </div>
      </div>

      {/* Main Grid: Video Viewport (Left) + Active Tracks (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Video Viewport (2 spans) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl relative">
            
            {/* Viewport Control Bar */}
            <div className="px-4 py-3 bg-slate-950/80 border-b border-slate-800/80 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className={`w-2.5 h-2.5 rounded-full ${isStreaming ? 'bg-emerald-400 animate-pulse' : 'bg-red-500'}`} />
                <span className="text-xs font-mono font-bold text-white tracking-wider">
                  {selectedCameraId}
                </span>
                <span className="text-xs text-slate-400">
                  • {selectedCamObj?.location_name || 'Corridor Viewport'}
                </span>
              </div>

              {/* Viewport Action Controls */}
              <div className="flex items-center gap-2">
                {/* AI HUD Mode Toggle */}
                <button
                  onClick={() => setIsAnnotated(!isAnnotated)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 border transition-all ${
                    isAnnotated 
                      ? 'bg-cyan-500/20 text-cyan-200 border-cyan-500/40'
                      : 'bg-slate-800 text-slate-400 border-slate-700'
                  }`}
                  title="Toggle YOLO Bounding Boxes & Tracker IDs"
                >
                  {isAnnotated ? <Eye className="w-3.5 h-3.5 text-cyan-400" /> : <EyeOff className="w-3.5 h-3.5" />}
                  <span>{isAnnotated ? 'AI HUD: ON' : 'Raw Feed'}</span>
                </button>

                {/* Start / Stop Ingestion */}
                {isStreaming ? (
                  <button
                    onClick={handleStopStream}
                    disabled={isActionLoading}
                    className="px-3 py-1.5 rounded-lg text-xs font-medium bg-red-500/20 hover:bg-red-500/30 text-red-300 border border-red-500/40 flex items-center gap-1.5 transition-colors disabled:opacity-50"
                  >
                    <Square className="w-3 h-3 fill-red-400 text-red-400" />
                    <span>Stop</span>
                  </button>
                ) : (
                  <button
                    onClick={handleStartStream}
                    disabled={isActionLoading}
                    className="px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 flex items-center gap-1.5 transition-colors disabled:opacity-50"
                  >
                    <Play className="w-3 h-3 fill-emerald-400 text-emerald-400" />
                    <span>Start</span>
                  </button>
                )}
              </div>
            </div>

            {/* Video Frame Canvas / Stream */}
            <div className="relative aspect-video bg-slate-950 flex items-center justify-center overflow-hidden">
              {isStreaming ? (
                <img
                  key={`${selectedCameraId}-${isAnnotated}`}
                  src={streamUrl}
                  alt={`${selectedCameraId} Live Stream`}
                  className="w-full h-full object-contain"
                  onError={(e) => {
                    console.error('MJPEG stream load error');
                  }}
                />
              ) : (
                <div className="text-center p-8 space-y-3">
                  <div className="w-14 h-14 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-slate-500">
                    <Video className="w-7 h-7" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-300">Camera Stream Offline</h3>
                    <p className="text-xs text-slate-500 max-w-xs mx-auto mt-1">
                      Click 'Start' to begin OpenCV video ingestion and launch live YOLOv8 multi-object tracking.
                    </p>
                  </div>
                  <button
                    onClick={handleStartStream}
                    disabled={isActionLoading}
                    className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-lg shadow-cyan-950/50 transition-all inline-flex items-center gap-2"
                  >
                    <Play className="w-3.5 h-3.5 fill-white" />
                    <span>Launch Live Feed</span>
                  </button>
                </div>
              )}

              {/* Real-Time HUD Overlay Tag */}
              {isStreaming && (
                <div className="absolute top-3 left-3 bg-slate-950/80 backdrop-blur border border-slate-800/80 px-3 py-1.5 rounded-lg flex items-center gap-2 text-[11px] font-mono text-cyan-300 shadow-md">
                  <div className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
                  <span>LIVE INFERENCE</span>
                  <span className="text-slate-500">|</span>
                  <span>{isAnnotated ? 'ANNOTATED' : 'RAW'}</span>
                </div>
              )}
            </div>

            {/* Viewport Footer Info */}
            <div className="px-4 py-2.5 bg-slate-950/90 border-t border-slate-800/80 flex flex-wrap items-center justify-between text-xs text-slate-400 gap-2">
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-cyan-400" />
                  <span>{selectedCamObj?.direction || 'NORTHBOUND'}</span>
                </span>
                <span>•</span>
                <span>Source: {selectedCamObj?.source_type || 'LOCAL_VIDEO'}</span>
              </div>
              <div className="text-[11px] font-mono text-slate-400">
                {stats?.supported_classes?.join(' • ') || 'car • motorcycle • bus • truck'}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Active Tracks in Viewport */}
        <div className="space-y-4">
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 shadow-xl flex flex-col h-[520px]">
            
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h2 className="text-sm font-bold text-white flex items-center gap-2">
                  <Crosshair className="w-4 h-4 text-cyan-400" />
                  Camera-Local Tracks
                </h2>
                <p className="text-[11px] text-slate-400">
                  Active objects tracked in {selectedCameraId}
                </p>
              </div>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-md bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                {activeTracks.length} Active
              </span>
            </div>

            {/* Active Tracks Scrollable List */}
            <div className="flex-1 overflow-y-auto space-y-2.5 pt-3 pr-1">
              {activeTracks.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-2 text-slate-500">
                  <Car className="w-8 h-8 opacity-40" />
                  <p className="text-xs">No active vehicles detected in current camera frame.</p>
                  {isStreaming && (
                    <p className="text-[10px] text-slate-600 font-mono">
                      YOLO is actively scanning incoming frames...
                    </p>
                  )}
                </div>
              ) : (
                activeTracks.map(track => {
                  const cfg = CLASS_CONFIG[track.vehicle_class] || CLASS_CONFIG.car;
                  const Icon = cfg.icon;
                  const confPct = Math.round(track.confidence * 100);

                  return (
                    <div 
                      key={track.tracker_id} 
                      className="bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 p-3 rounded-xl transition-all space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold border flex items-center gap-1 ${cfg.color}`}>
                            <Icon className="w-3 h-3" />
                            {cfg.label.toUpperCase()}
                          </span>
                          <span className="text-xs font-mono font-bold text-white">
                            {track.tracker_id}
                          </span>
                        </div>
                        <span className="text-xs font-mono font-bold text-cyan-300">
                          {confPct}%
                        </span>
                      </div>

                      {/* Confidence Progress Bar */}
                      <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                        <div 
                          className="bg-cyan-400 h-full rounded-full transition-all duration-300"
                          style={{ width: `${confPct}%` }}
                        />
                      </div>

                      {/* Coordinates & Life Span */}
                      <div className="grid grid-cols-2 text-[10px] font-mono text-slate-400 pt-1">
                        <div>
                          <span className="text-slate-500">Center: </span>
                          [{track.center?.[0] || 0}, {track.center?.[1] || 0}]
                        </div>
                        <div className="text-right">
                          <span className="text-slate-500">Frames: </span>
                          {track.total_frames}
                        </div>
                      </div>

                      {track.trajectory_points?.length > 0 && (
                        <div className="text-[10px] text-slate-500 flex items-center justify-between border-t border-slate-800/60 pt-1">
                          <span>Trajectory Waypoints:</span>
                          <span className="font-mono text-slate-300">{track.trajectory_points.length} pts</span>
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>

            {/* Note banner */}
            <div className="mt-3 pt-2.5 border-t border-slate-800 text-[10px] text-slate-500 flex items-start gap-1.5">
              <AlertCircle className="w-3 h-3 text-cyan-400 shrink-0 mt-0.5" />
              <span>Camera-local IDs are isolated per viewport and NOT global identities.</span>
            </div>
          </div>
        </div>

      </div>

      {/* Historical Detections Log Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              Recent Detection Records
            </h2>
            <p className="text-xs text-slate-400">
              Per-frame vehicle detections captured by {selectedCameraId} and saved to SQLite
            </p>
          </div>

          {/* Class Filter Pills */}
          <div className="flex items-center gap-1.5 bg-slate-950/80 p-1 rounded-xl border border-slate-800">
            {['all', 'car', 'truck', 'bus', 'motorcycle'].map(c => (
              <button
                key={c}
                onClick={() => setClassFilter(c)}
                className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                  classFilter === c 
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {c.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800 font-mono text-[11px] uppercase">
              <tr>
                <th className="py-2.5 px-3">Detection ID</th>
                <th className="py-2.5 px-3">Camera</th>
                <th className="py-2.5 px-3">Vehicle Class</th>
                <th className="py-2.5 px-3">Confidence</th>
                <th className="py-2.5 px-3">Bounding Box [X1, Y1, X2, Y2]</th>
                <th className="py-2.5 px-3">Center [X, Y]</th>
                <th className="py-2.5 px-3">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
              {filteredDetections.length === 0 ? (
                <tr>
                  <td colSpan="7" className="py-8 text-center text-slate-500 font-sans">
                    No detection records recorded yet for {selectedCameraId}. Start the video stream to capture vehicles.
                  </td>
                </tr>
              ) : (
                filteredDetections.map(det => {
                  const cfg = CLASS_CONFIG[det.vehicle_class] || CLASS_CONFIG.car;
                  const Icon = cfg.icon;

                  return (
                    <tr key={det.detection_id || det.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-2.5 px-3 text-cyan-400 font-semibold">{det.detection_id}</td>
                      <td className="py-2.5 px-3 text-white">{det.camera_id}</td>
                      <td className="py-2.5 px-3">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] border ${cfg.color}`}>
                          <Icon className="w-3 h-3" />
                          {det.vehicle_class.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-emerald-400 font-bold">
                        {(det.confidence * 100).toFixed(1)}%
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">
                        [{det.bbox?.join(', ')}]
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">
                        [{det.center?.join(', ')}]
                      </td>
                      <td className="py-2.5 px-3 text-slate-500">
                        {det.timestamp ? new Date(det.timestamp).toLocaleTimeString() : 'Live'}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Test Image Inference Modal */}
      {isUploadModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Upload className="w-4 h-4 text-cyan-400" />
                Upload Image for Instant YOLOv8 Inference
              </h3>
              <button 
                onClick={() => { setIsUploadModalOpen(false); setTestResult(null); }}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3">
              <p className="text-xs text-slate-400">
                Test the real Ultralytics YOLOv8 vehicle detector directly on any local image file.
              </p>

              <input 
                type="file" 
                ref={fileInputRef} 
                accept="image/*" 
                onChange={handleFileUpload}
                className="hidden" 
              />

              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="w-full py-8 border-2 border-dashed border-slate-700 hover:border-cyan-500/50 rounded-xl flex flex-col items-center justify-center space-y-2 bg-slate-950/40 hover:bg-slate-950/70 transition-all text-slate-300"
              >
                <Upload className="w-8 h-8 text-cyan-400" />
                <span className="text-xs font-medium">Click to select an image from your computer</span>
                <span className="text-[10px] text-slate-500">Supports JPG, PNG, WebP</span>
              </button>

              {isUploading && (
                <div className="p-4 bg-cyan-950/40 border border-cyan-800/40 rounded-xl text-xs text-cyan-300 flex items-center gap-2">
                  <RefreshCw className="w-4 h-4 animate-spin text-cyan-400" />
                  <span>Running YOLOv8 inference...</span>
                </div>
              )}

              {testResult && (
                <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3 font-mono text-xs">
                  <div className="flex items-center justify-between text-emerald-400 font-bold">
                    <span>STATUS: {testResult.status}</span>
                    <span>{testResult.inference_ms} ms</span>
                  </div>
                  <div className="text-white">
                    Total Vehicles Detected: <span className="text-cyan-400 font-bold">{testResult.total_vehicles_detected}</span>
                  </div>
                  {testResult.vehicle_counts && Object.keys(testResult.vehicle_counts).length > 0 && (
                    <div className="flex flex-wrap gap-2 pt-1">
                      {Object.entries(testResult.vehicle_counts).map(([cls, count]) => (
                        <span key={cls} className="px-2 py-0.5 rounded bg-slate-800 text-slate-200 border border-slate-700 text-[11px]">
                          {cls}: {count}
                        </span>
                      ))}
                    </div>
                  )}
                  {testResult.detections?.length > 0 && (
                    <div className="max-h-40 overflow-y-auto space-y-1 pt-2 border-t border-slate-800 text-[10px] text-slate-400">
                      {testResult.detections.map((d, i) => (
                        <div key={i} className="flex justify-between">
                          <span className="text-cyan-300">{d.class.toUpperCase()}</span>
                          <span>Conf: {(d.confidence * 100).toFixed(1)}%</span>
                          <span>[{d.bbox.map(n => Math.round(n)).join(', ')}]</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => { setIsUploadModalOpen(false); setTestResult(null); }}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
