import React, { useState, useEffect } from 'react';
import { 
  Camera, 
  Video, 
  Radio, 
  Layers, 
  Maximize2, 
  Eye, 
  RefreshCw, 
  ShieldCheck,
  Car,
  Activity,
  Sliders
} from 'lucide-react';
import { api } from '../services/api';

export default function LiveCCTV() {
  const [cameras, setCameras] = useState([]);
  const [selectedCamera, setSelectedCamera] = useState('CAM01');
  const [detections, setDetections] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadCctvData = async () => {
    try {
      const [cams, dets] = await Promise.all([
        api.getCameras(),
        api.getDetections({ camera_id: selectedCamera, limit: 15 })
      ]);
      setCameras(cams);
      setDetections(dets);
    } catch (err) {
      console.error('CCTV error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCctvData();
    const interval = setInterval(loadCctvData, 3000);
    return () => clearInterval(interval);
  }, [selectedCamera]);

  const activeCamObj = cameras.find(c => c.camera_id === selectedCamera) || cameras[0] || {};

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl">
        <div>
          <div className="flex items-center space-x-2">
            <Video className="w-4 h-4 text-cyan-400" />
            <span className="text-[10px] uppercase font-bold text-cyan-400 tracking-wider">
              MULTI-STREAM CCTV SURVEILLANCE
            </span>
          </div>
          <h1 className="text-xl font-black text-slate-100 mt-0.5">City Traffic Camera Matrix</h1>
          <p className="text-xs text-slate-400">
            Real-time object detection, localized tracking (ByteTrack), and ANPR OCR engine streaming live feeds.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {cameras.map((c) => (
            <button
              key={c.camera_id}
              onClick={() => setSelectedCamera(c.camera_id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition ${
                selectedCamera === c.camera_id
                  ? 'bg-cyan-500 text-slate-950 shadow-[0_0_12px_rgba(0,242,254,0.4)]'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {c.camera_id}
            </button>
          ))}
        </div>
      </div>

      {/* Main Focus View & Side Detections Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Stream Player (2 Cols) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-2xl">
            {/* Player Header */}
            <div className="px-4 py-3 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="font-mono font-bold text-sm text-cyan-300">
                  {activeCamObj.camera_id || selectedCamera}: {activeCamObj.camera_name || 'Traffic Camera'}
                </span>
              </div>
              <div className="flex items-center space-x-2 text-xs font-mono text-slate-400">
                <span className="px-2 py-0.5 rounded bg-slate-800 text-[11px] text-slate-300">
                  {activeCamObj.zone || 'Corridor'}
                </span>
                <span className="text-emerald-400 font-bold">15 FPS / MJPEG</span>
              </div>
            </div>

            {/* Live Video Canvas */}
            <div className="relative aspect-video bg-black flex items-center justify-center scanlines">
              <img
                src={api.getLiveStreamUrl(selectedCamera)}
                alt={selectedCamera}
                className="w-full h-full object-cover"
              />

              {/* Live HUD Watermark */}
              <div className="absolute top-3 left-3 px-2.5 py-1 rounded bg-slate-950/80 backdrop-blur-sm border border-slate-700/60 text-[11px] font-mono text-slate-200 space-y-0.5">
                <div>LOC: {activeCamObj.location_name}</div>
                <div className="text-cyan-400 font-bold">DIRECTION: {activeCamObj.direction}</div>
              </div>
            </div>

            {/* Player Footer Specs */}
            <div className="p-3 bg-slate-950 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400 border-t border-slate-800">
              <div className="flex items-center space-x-3">
                <span>Status: <strong className="text-emerald-400">STREAMING</strong></span>
                <span>Active Density: <strong className="text-slate-200">{activeCamObj.active_vehicles_count || 4} vehicles</strong></span>
              </div>
              <div>
                Congestion Index: <strong className="text-cyan-400">{activeCamObj.congestion_level || 'LOW'}</strong>
              </div>
            </div>
          </div>

          {/* Mini 3-Camera Preview Thumbnails */}
          <div className="grid grid-cols-3 gap-3">
            {cameras.filter(c => c.camera_id !== selectedCamera).map((cam) => (
              <div
                key={cam.camera_id}
                onClick={() => setSelectedCamera(cam.camera_id)}
                className="p-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-cyan-500/50 cursor-pointer transition space-y-1.5"
              >
                <div className="flex justify-between text-[11px] font-mono">
                  <span className="font-bold text-slate-300">{cam.camera_id}</span>
                  <span className="text-slate-500">{cam.zone}</span>
                </div>
                <div className="aspect-video bg-black rounded overflow-hidden">
                  <img
                    src={api.getLiveStreamUrl(cam.camera_id)}
                    alt={cam.camera_id}
                    className="w-full h-full object-cover"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Real-Time Detection Feed (1 Col) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                Live ANPR Ingestion Logs
              </h3>
            </div>
            <span className="text-[10px] font-mono text-slate-500">
              {detections.length} recorded
            </span>
          </div>

          <div className="space-y-2.5 max-h-[620px] overflow-y-auto pr-1">
            {detections.length === 0 ? (
              <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 text-center text-xs text-slate-500">
                Listening for incoming vehicle tracks on {selectedCamera}...
              </div>
            ) : (
              detections.map((det) => (
                <div
                  key={det.detection_id}
                  className="p-3 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition space-y-2 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] font-bold text-cyan-400">
                      {det.tracker_id}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {new Date(det.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <span className="text-slate-300 font-semibold uppercase">
                        {det.color} {det.vehicle_class}
                      </span>
                      <p className="text-[11px] text-slate-400">
                        Inferred Speed: <strong className="text-slate-200">{det.speed_estimate || 48} km/h</strong>
                      </p>
                    </div>

                    {det.plate && (
                      <div className="text-right">
                        <div className="px-2 py-0.5 rounded bg-emerald-950 border border-emerald-700 text-emerald-300 font-mono font-bold text-xs">
                          {det.plate.plate_text}
                        </div>
                        <span className="text-[10px] text-slate-500">
                          OCR: {Math.round(det.plate.ocr_confidence * 100)}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
