import React, { useState, useEffect } from 'react';
import { 
  CopyCheck, 
  ShieldAlert, 
  AlertTriangle, 
  ArrowRight, 
  Camera, 
  CheckCircle2, 
  XCircle, 
  Briefcase, 
  Car,
  Gauge,
  Clock,
  Sparkles
} from 'lucide-react';
import { AlertTypeBadge, SeverityBadge, StatusBadge } from '../components/AlertBadge';
import SideBySideEvidenceModal from '../components/SideBySideEvidenceModal';
import { api } from '../services/api';

export default function ClonedPlates() {
  const [alerts, setAlerts] = useState([]);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [modalAlert, setModalAlert] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadAlerts = async () => {
    try {
      const data = await api.getAlerts();
      // Filter for duplicate plate or impossible travel anomalies
      const filtered = data.filter(a => 
        a.alert_type === 'POSSIBLE_DUPLICATE_PLATE' || 
        a.alert_type === 'IMPOSSIBLE_TRAVEL' ||
        a.alert_type === 'REGISTRY_MISMATCH'
      );
      setAlerts(filtered);
      if (filtered.length > 0 && !selectedAlert) {
        setSelectedAlert(filtered[0]);
      }
    } catch (err) {
      console.error('Cloned plate load error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
    const interval = setInterval(loadAlerts, 4000);
    return () => clearInterval(interval);
  }, []);

  let details = {};
  if (selectedAlert) {
    try {
      details = typeof selectedAlert.details_json === 'string'
        ? JSON.parse(selectedAlert.details_json)
        : (selectedAlert.details_json || {});
    } catch (e) {
      details = {};
    }
  }

  const obsA = details.previous_observation || details.observation || {};
  const obsB = details.new_observation || {};
  const discrepancies = details.discrepancy_scores || {};

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-red-950/60 via-slate-900 to-purple-950/40 border border-red-900/50 shadow-2xl">
        <div className="flex items-center space-x-2">
          <CopyCheck className="w-5 h-5 text-red-400" />
          <span className="text-[10px] uppercase font-bold text-red-400 tracking-wider">
            CENTRAL INNOVATION ENGINE
          </span>
        </div>
        <h1 className="text-xl sm:text-2xl font-black text-slate-100 mt-1">
          Duplicate & Cloned Plate Intelligence Studio
        </h1>
        <p className="text-xs text-slate-300 max-w-3xl mt-1 leading-relaxed">
          <strong>"Do not blindly trust the registration plate."</strong> Correlating plate OCR, vehicle classification, dominant color, and camera network topology to flag duplicate identities and impossible speed anomalies.
        </p>
      </div>

      {/* Main Grid: Active Cloned Alerts (1 Col) & Split Screen Studio (2 Cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Alerts List (1 Col) */}
        <div className="space-y-3">
          <div className="flex items-center justify-between px-1 text-xs font-semibold text-slate-400">
            <span>Conflicting Identifiers ({alerts.length})</span>
            <span className="text-[10px] text-red-400 font-bold">HUMAN REVIEW</span>
          </div>

          <div className="space-y-2.5 max-h-[650px] overflow-y-auto pr-1">
            {alerts.length === 0 ? (
              <div className="p-8 rounded-xl bg-slate-900 border border-slate-800 text-center text-xs text-slate-500">
                No active duplicate plate anomalies detected. Trigger a test scenario from the controller!
              </div>
            ) : (
              alerts.map((a) => (
                <div
                  key={a.alert_id}
                  onClick={() => setSelectedAlert(a)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition space-y-2 ${
                    selectedAlert?.alert_id === a.alert_id
                      ? 'bg-red-950/40 border-red-500/80 shadow-[0_0_15px_rgba(239,68,68,0.2)]'
                      : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 bg-red-950 border border-red-700 text-red-300 font-mono font-bold text-xs rounded">
                      {a.plate_text || 'UNKNOWN'}
                    </span>
                    <SeverityBadge severity={a.severity} />
                  </div>

                  <h4 className="text-xs font-bold text-slate-200 line-clamp-1">{a.title}</h4>
                  <p className="text-[11px] text-slate-400 line-clamp-2">{a.description}</p>

                  <div className="flex items-center justify-between pt-1 border-t border-slate-800/80 text-[10px]">
                    <span className="text-slate-500">{new Date(a.timestamp).toLocaleTimeString()}</span>
                    <StatusBadge status={a.status} />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Deep Split-Screen Inspector Studio (2 Cols) */}
        <div className="lg:col-span-2 space-y-5">
          {selectedAlert ? (
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-6">
              {/* Studio Header */}
              <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg font-black text-slate-100">{selectedAlert.title}</span>
                    <SeverityBadge severity={selectedAlert.severity} />
                  </div>
                  <p className="text-xs text-slate-400">
                    Case Evaluation for Plate: <strong className="font-mono text-cyan-400">{selectedAlert.plate_text}</strong>
                  </p>
                </div>

                <button
                  onClick={() => setModalAlert(selectedAlert)}
                  className="px-3.5 py-2 bg-red-600 hover:bg-red-500 text-white text-xs font-semibold rounded-xl flex items-center space-x-1.5 transition shadow-lg shadow-red-900/30"
                >
                  <ShieldAlert className="w-4 h-4" />
                  <span>Interactive Verification Tool</span>
                </button>
              </div>

              {/* Observation Comparison Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Observation A */}
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between text-xs font-bold text-cyan-400 border-b border-slate-800 pb-2">
                    <span className="flex items-center space-x-1.5">
                      <Camera className="w-4 h-4" />
                      <span>Observation A ({obsA.camera_id || selectedAlert.source_camera_id || 'CAM01'})</span>
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {obsA.timestamp ? new Date(obsA.timestamp).toLocaleTimeString() : 'Earlier'}
                    </span>
                  </div>

                  <div className="h-32 rounded-lg bg-slate-900 border border-slate-800 flex flex-col items-center justify-center space-y-1">
                    <Car className="w-10 h-10 text-slate-400" />
                    <span className="text-xs font-mono font-bold text-slate-200">
                      {obsA.color || 'WHITE'} {(obsA.vehicle_type || 'SEDAN').toUpperCase()}
                    </span>
                    <span className="text-[10px] text-emerald-400 font-mono font-bold">
                      PLATE: {selectedAlert.plate_text}
                    </span>
                  </div>

                  <div className="text-xs space-y-1 text-slate-300">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Vehicle Type:</span>
                      <strong className="uppercase">{obsA.vehicle_type || 'Sedan'}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Body Color:</span>
                      <strong>{obsA.color || 'WHITE'}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">OCR Confidence:</span>
                      <strong className="text-emerald-400 font-mono">
                        {Math.round((obsA.ocr_confidence || 0.95) * 100)}%
                      </strong>
                    </div>
                  </div>
                </div>

                {/* Observation B */}
                <div className="p-4 rounded-xl bg-slate-950 border border-red-900/40 space-y-3">
                  <div className="flex items-center justify-between text-xs font-bold text-red-400 border-b border-slate-800 pb-2">
                    <span className="flex items-center space-x-1.5">
                      <Camera className="w-4 h-4" />
                      <span>Observation B ({obsB.camera_id || selectedAlert.target_camera_id || 'CAM04'})</span>
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {obsB.timestamp ? new Date(obsB.timestamp).toLocaleTimeString() : 'Recent'}
                    </span>
                  </div>

                  <div className="h-32 rounded-lg bg-slate-900 border border-red-900/60 flex flex-col items-center justify-center space-y-1">
                    <Car className="w-10 h-10 text-red-400" />
                    <span className="text-xs font-mono font-bold text-slate-200">
                      {obsB.color || 'BLACK'} {(obsB.vehicle_type || 'SUV').toUpperCase()}
                    </span>
                    <span className="text-[10px] text-emerald-400 font-mono font-bold">
                      PLATE: {selectedAlert.plate_text}
                    </span>
                  </div>

                  <div className="text-xs space-y-1 text-slate-300">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Vehicle Type:</span>
                      <strong className="text-red-300 uppercase">{obsB.vehicle_type || 'SUV'}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Body Color:</span>
                      <strong className="text-red-300">{obsB.color || 'BLACK'}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">OCR Confidence:</span>
                      <strong className="text-emerald-400 font-mono">
                        {Math.round((obsB.ocr_confidence || 0.94) * 100)}%
                      </strong>
                    </div>
                  </div>
                </div>
              </div>

              {/* Discrepancy & Speed Matrix */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
                  Automated Correlation Diagnostics
                </span>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-center">
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-[10px] text-slate-500 uppercase">Visual Match</span>
                    <p className="text-base font-bold text-red-400 font-mono mt-1">
                      {discrepancies.type_match_score !== undefined ? `${Math.round(discrepancies.type_match_score * 100)}%` : '0%'}
                    </p>
                    <span className="text-[10px] text-red-400/80">Conflicting Shape</span>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-[10px] text-slate-500 uppercase">Color Similarity</span>
                    <p className="text-base font-bold text-red-400 font-mono mt-1">
                      {discrepancies.color_match_score !== undefined ? `${Math.round(discrepancies.color_match_score * 100)}%` : '0%'}
                    </p>
                    <span className="text-[10px] text-red-400/80">Conflicting Pigment</span>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-[10px] text-slate-500 uppercase">Estimated Speed</span>
                    <p className="text-base font-bold text-cyan-400 font-mono mt-1">
                      {discrepancies.estimated_transit_speed_kmh ? `${discrepancies.estimated_transit_speed_kmh} km/h` : 'N/A'}
                    </p>
                    <span className="text-[10px] text-cyan-400/80">Inferred Velocity</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-16 rounded-2xl bg-slate-900 border border-slate-800 text-center text-slate-500 text-xs">
              Select an alert from the queue to start side-by-side inspection.
            </div>
          )}
        </div>
      </div>

      {/* Modal Tool */}
      {modalAlert && (
        <SideBySideEvidenceModal
          alert={modalAlert}
          onClose={() => setModalAlert(null)}
          onReviewed={loadAlerts}
        />
      )}
    </div>
  );
}
