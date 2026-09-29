import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  Camera, 
  Play, 
  Square, 
  Maximize2, 
  Minimize2, 
  RefreshCw, 
  AlertCircle, 
  CheckCircle2, 
  Activity, 
  Layers, 
  Radio, 
  Clock, 
  MapPin, 
  Compass, 
  Sliders, 
  Info,
  Film,
  Search,
  Cpu
} from 'lucide-react';
import { api } from '../services/api';

export default function LiveCameras() {
  const [searchParams, setSearchParams] = useSearchParams();
  const requestedCamId = searchParams.get('camera');

  const [cameras, setCameras] = useState([]);
  const [selectedCameraId, setSelectedCameraId] = useState(requestedCamId || null);
  const [cameraTelemetry, setCameraTelemetry] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isStartingStream, setIsStartingStream] = useState(false);
  const [error, setError] = useState(null);
  const [searchFilter, setSearchFilter] = useState('');
  const [selectedZone, setSelectedZone] = useState('ALL');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const videoContainerRef = useRef(null);

  // Fetch all cameras
  const loadCameras = async () => {
    setIsLoading(true);
    try {
      const camList = await api.getCameras();
      setCameras(camList);
      if (!selectedCameraId && camList.length > 0) {
        setSelectedCameraId(camList[0].camera_id);
      } else if (requestedCamId && camList.some(c => c.camera_id === requestedCamId)) {
        setSelectedCameraId(requestedCamId);
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch camera registry.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCameras();
  }, []);

  // Sync with URL query parameter
  useEffect(() => {
    if (requestedCamId && requestedCamId !== selectedCameraId) {
      setSelectedCameraId(requestedCamId);
    }
  }, [requestedCamId]);

  // Selected camera object
  const activeCamera = cameras.find(c => c.camera_id === selectedCameraId) || null;

  // Poll active camera telemetry
  const fetchCameraTelemetry = async () => {
    if (!selectedCameraId) return;
    try {
      const statusData = await api.getCameraStatus(selectedCameraId);
      setCameraTelemetry(statusData);
    } catch (err) {
      // Background poll fail catch
    }
  };

  useEffect(() => {
    if (selectedCameraId) {
      fetchCameraTelemetry();
      const interval = setInterval(fetchCameraTelemetry, 1000); // 1s telemetry ping
      return () => clearInterval(interval);
    }
  }, [selectedCameraId]);

  const handleSelectCamera = (camId) => {
    setSelectedCameraId(camId);
    setSearchParams({ camera: camId });
  };

  const handleToggleStream = async () => {
    if (!activeCamera) return;
    setIsStartingStream(true);
    try {
      if (activeCamera.status === 'ONLINE') {
        await api.stopCamera(activeCamera.camera_id);
      } else {
        await api.startCamera(activeCamera.camera_id);
      }
      // Refresh list and telemetry
      const updatedList = await api.getCameras();
      setCameras(updatedList);
      await fetchCameraTelemetry();
    } catch (err) {
      alert(`Error modifying stream state: ${err.message}`);
    } finally {
      setIsStartingStream(false);
    }
  };

  const toggleFullscreen = () => {
    if (!videoContainerRef.current) return;
    if (!document.fullscreenElement) {
      videoContainerRef.current.requestFullscreen().catch(err => {
        alert(`Error enabling fullscreen: ${err.message}`);
      });
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  // Filtered cameras
  const filteredCameras = cameras.filter(cam => {
    const matchSearch = cam.camera_id.toLowerCase().includes(searchFilter.toLowerCase()) ||
                        cam.location_name.toLowerCase().includes(searchFilter.toLowerCase());
    const matchZone = selectedZone === 'ALL' || cam.zone === selectedZone;
    return matchSearch && matchZone;
  });

  const availableZones = ['ALL', ...new Set(cameras.map(c => c.zone))];
  const isOnline = activeCamera?.status === 'ONLINE' || cameraTelemetry?.is_streaming;

  return (
    <div className="space-y-6 animate-fade-in">
      
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-slate-900/90 via-slate-900/60 to-cyan-950/30 border border-slate-800 backdrop-blur-xl">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
              LIVE CCTV MATRIX
            </span>
            <span className="text-slate-500 font-mono text-xs">•</span>
            <span className="text-slate-400 font-mono text-xs">OPENCV MJPEG STREAMING</span>
          </div>
          <h2 className="text-2xl font-black tracking-tight text-white uppercase">
            LIVE CCTV FEEDS & STREAMING
          </h2>
          <p className="text-sm text-slate-400">
            Real-time video ingestion, multi-node stream monitoring, frame telemetry, and visual viewport.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadCameras}
            disabled={isLoading}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-300 text-xs font-mono transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-cyan-400' : ''}`} />
            <span>Refresh Feeds</span>
          </button>
        </div>
      </div>

      {/* 3-Column Command Viewport */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* LEFT COLUMN: Camera Selector List (3 cols) */}
        <div className="lg:col-span-3 space-y-4 p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs font-mono font-bold text-slate-400 uppercase tracking-wider">
              <Camera className="w-4 h-4 text-cyan-400" />
              <span>Camera Nodes ({cameras.length})</span>
            </div>
          </div>

          {/* Search & Zone Filters */}
          <div className="space-y-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Filter cameras..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>

            <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 text-[10px] font-mono">
              {availableZones.map(z => (
                <button
                  key={z}
                  onClick={() => setSelectedZone(z)}
                  className={`px-2 py-1 rounded whitespace-nowrap transition ${
                    selectedZone === z 
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-bold'
                      : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
                  }`}
                >
                  {z === 'ALL' ? 'ALL' : z.replace('Zone ', '')}
                </button>
              ))}
            </div>
          </div>

          {/* Camera List Items */}
          <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
            {filteredCameras.map((cam) => {
              const isSelected = cam.camera_id === selectedCameraId;
              const camIsOnline = cam.status === 'ONLINE';

              return (
                <div
                  key={cam.camera_id}
                  onClick={() => handleSelectCamera(cam.camera_id)}
                  className={`p-3 rounded-xl cursor-pointer transition flex items-center justify-between border ${
                    isSelected
                      ? 'bg-cyan-950/40 border-cyan-500/50 shadow-[0_0_15px_rgba(6,182,212,0.2)] text-white'
                      : 'bg-slate-950/70 border-slate-800/80 text-slate-300 hover:bg-slate-900 hover:border-slate-700'
                  }`}
                >
                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono font-black text-xs">{cam.camera_id}</span>
                      {cam.is_demo && (
                        <span className="px-1 py-0.2 rounded text-[8px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                          DEMO
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-400 truncate">{cam.location_name}</div>
                    <div className="text-[10px] text-slate-500 font-mono flex items-center space-x-1">
                      <span>{cam.zone}</span>
                    </div>
                  </div>

                  <div className="flex flex-col items-end space-y-1 shrink-0 ml-2">
                    <span className={`w-2 h-2 rounded-full ${camIsOnline ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'}`} />
                    <span className={`text-[9px] font-mono font-bold uppercase ${camIsOnline ? 'text-emerald-400' : 'text-slate-500'}`}>
                      {cam.status}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* CENTER COLUMN: Live Video Viewport (6 cols) */}
        <div className="lg:col-span-6 space-y-4">
          <div 
            ref={videoContainerRef}
            className="rounded-2xl bg-slate-950 border border-slate-800 overflow-hidden shadow-2xl relative flex flex-col justify-between"
            style={{ minHeight: '440px' }}
          >
            {/* Viewport Header */}
            <div className="p-3.5 bg-slate-950/90 border-b border-slate-800/80 flex items-center justify-between z-20">
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2">
                  <span className="font-mono font-black text-sm text-cyan-400">
                    {activeCamera?.camera_id || 'NO CAMERA'}
                  </span>
                  {activeCamera?.is_demo && (
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      DEMO CAMERA
                    </span>
                  )}
                </div>
                <span className="text-slate-600 font-mono">•</span>
                <span className="text-xs text-slate-300 truncate max-w-xs font-mono">
                  {activeCamera?.location_name || 'Select a camera node'}
                </span>
              </div>

              {/* Status Pill */}
              <div className="flex items-center space-x-2 font-mono text-xs">
                {isOnline ? (
                  <div className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-emerald-950/60 text-emerald-400 border border-emerald-500/40 text-[10px] font-bold animate-pulse">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    <span>LIVE</span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-slate-900 text-slate-400 border border-slate-800 text-[10px] font-bold">
                    <span>STOPPED</span>
                  </div>
                )}
              </div>
            </div>

            {/* Video Feed Area */}
            <div className="relative flex-1 bg-black flex items-center justify-center overflow-hidden min-h-[360px]">
              
              {/* Tactical scanline HUD effect */}
              <div className="absolute inset-0 pointer-events-none z-10 scanlines opacity-40" />

              {!activeCamera ? (
                <div className="text-center space-y-2 p-6 z-20">
                  <Camera className="w-12 h-12 text-slate-700 mx-auto" />
                  <div className="text-sm font-bold text-slate-400 font-mono">No Camera Selected</div>
                  <div className="text-xs text-slate-600">Select a camera node from the left panel to initialize feed.</div>
                </div>
              ) : isOnline ? (
                /* Real OpenCV MJPEG Stream */
                <img
                  key={`${activeCamera.camera_id}-${activeCamera.status}`}
                  src={api.getCameraStreamUrl(activeCamera.camera_id)}
                  alt={`Live Stream - ${activeCamera.camera_id}`}
                  className="w-full h-full object-contain z-10"
                  onError={(e) => {
                    console.warn("Stream error or reconnecting...");
                  }}
                />
              ) : (
                /* Tactical Standby / Stopped State */
                <div className="text-center space-y-4 p-8 z-20 max-w-md">
                  <div className="w-16 h-16 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-center mx-auto text-slate-500">
                    <Film className="w-8 h-8" />
                  </div>
                  <div className="space-y-1">
                    <div className="text-base font-bold text-white font-mono uppercase">
                      {activeCamera.status === 'ERROR' ? 'Video Source Unavailable' : 'Camera Stopped'}
                    </div>
                    <p className="text-xs text-slate-400">
                      {activeCamera.status === 'ERROR'
                        ? 'OpenCV VideoCapture was unable to open the local video path or stream source.'
                        : 'Video ingestion for this node is in standby mode.'}
                    </p>
                  </div>
                  
                  <button
                    onClick={handleToggleStream}
                    disabled={isStartingStream}
                    className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-mono font-bold text-xs transition shadow-[0_0_20px_rgba(6,182,212,0.3)] disabled:opacity-50"
                  >
                    {isStartingStream ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Play className="w-4 h-4" />
                    )}
                    <span>{isStartingStream ? 'Connecting OpenCV...' : 'Start Camera Stream'}</span>
                  </button>
                </div>
              )}

              {/* Watermark HUD Overlay */}
              {isOnline && (
                <div className="absolute top-3 left-3 z-20 px-2 py-1 rounded bg-black/70 border border-slate-800 text-[10px] font-mono text-cyan-300 pointer-events-none flex items-center space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
                  <span>RAW CCTV FEED (AI DEFERRED)</span>
                </div>
              )}
            </div>

            {/* Viewport Footer Controls */}
            <div className="p-3 bg-slate-950/90 border-t border-slate-800/80 flex items-center justify-between z-20 font-mono text-xs">
              <div className="flex items-center space-x-3">
                <button
                  onClick={handleToggleStream}
                  disabled={!activeCamera || isStartingStream}
                  className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-bold transition disabled:opacity-50 ${
                    isOnline 
                      ? 'bg-amber-950/50 hover:bg-amber-900/60 text-amber-300 border border-amber-500/40' 
                      : 'bg-emerald-950/50 hover:bg-emerald-900/60 text-emerald-300 border border-emerald-500/40'
                  }`}
                >
                  {isOnline ? <Square className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                  <span>{isOnline ? 'Stop Stream' : 'Start Stream'}</span>
                </button>

                <span className="text-[11px] text-slate-500">
                  SRC: {activeCamera?.source_type || 'NONE'}
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={toggleFullscreen}
                  title="Toggle Fullscreen"
                  className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition"
                >
                  {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                </button>
              </div>
            </div>

          </div>
        </div>

        {/* RIGHT COLUMN: Camera Telemetry & Specs (3 cols) */}
        <div className="lg:col-span-3 space-y-4 p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="flex items-center space-x-2 text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">
            <Activity className="w-4 h-4" />
            <span>Node Frame Telemetry</span>
          </div>

          {!activeCamera ? (
            <div className="text-xs text-slate-500 font-mono py-8 text-center">
              Select a camera to inspect frame telemetry.
            </div>
          ) : (
            <div className="space-y-4">
              
              {/* Telemetry Metrics Grid */}
              <div className="space-y-2.5 font-mono text-xs">
                
                {/* Node ID */}
                <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">Camera ID:</span>
                  <span className="text-white font-bold">{activeCamera.camera_id}</span>
                </div>

                {/* Status */}
                <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">Stream Status:</span>
                  <span className={`font-bold ${isOnline ? 'text-emerald-400' : 'text-slate-400'}`}>
                    {cameraTelemetry?.status || activeCamera.status}
                  </span>
                </div>

                {/* FPS */}
                <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">Ingestion FPS:</span>
                  <span className="text-cyan-400 font-bold">
                    {cameraTelemetry?.fps ? `${cameraTelemetry.fps} FPS` : '0.0 FPS'}
                  </span>
                </div>

                {/* Resolution */}
                <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">Resolution:</span>
                  <span className="text-slate-200 font-bold">
                    {cameraTelemetry?.resolution || 'N/A'}
                  </span>
                </div>

                {/* Frame Counter */}
                <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">Frame Counter:</span>
                  <span className="text-purple-400 font-bold">
                    #{cameraTelemetry?.frame_number || 0}
                  </span>
                </div>

                {/* GIS Coordinates */}
                <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">GIS Coords:</span>
                  <span className="text-slate-300 text-[11px]">
                    {activeCamera.latitude?.toFixed(4)}, {activeCamera.longitude?.toFixed(4)}
                  </span>
                </div>

                {/* Source Path */}
                <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
                  <div className="text-[10px] text-slate-500 uppercase">Video Source Path:</div>
                  <div className="text-[11px] text-slate-300 break-all font-sans">
                    {activeCamera.local_video_path || activeCamera.source_url || 'None'}
                  </div>
                </div>

              </div>

              {/* Phase 3 Modular AI Pipeline Notice */}
              <div className="p-3.5 rounded-xl bg-purple-950/20 border border-purple-500/20 space-y-1.5 text-xs text-purple-200/90">
                <div className="flex items-center space-x-1.5 font-bold text-purple-300">
                  <Cpu className="w-3.5 h-3.5 text-purple-400" />
                  <span>Phase 2 Compliance</span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed font-sans">
                  OpenCV frame ingestion active. YOLOv8 detection & ANPR modules will hook directly into this pipeline in Phase 3.
                </p>
              </div>

            </div>
          )}
        </div>

      </div>

    </div>
  );
}
