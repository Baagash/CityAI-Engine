import React, { useState } from 'react';
import { 
  X, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  Briefcase, 
  ArrowRight, 
  ShieldAlert,
  Car,
  Camera,
  Gauge
} from 'lucide-react';
import { AlertTypeBadge, SeverityBadge, StatusBadge } from './AlertBadge';
import { api } from '../services/api';

export default function SideBySideEvidenceModal({ alert, onClose, onReviewed }) {
  const [reviewNotes, setReviewNotes] = useState('');
  const [officerName, setOfficerName] = useState('Officer J. Vance (Traffic Command)');
  const [submitting, setSubmitting] = useState(false);

  if (!alert) return null;

  let details = {};
  try {
    details = typeof alert.details_json === 'string' ? JSON.parse(alert.details_json) : (alert.details_json || {});
  } catch (e) {
    details = {};
  }

  const obsA = details.previous_observation || details.observation || {};
  const obsB = details.new_observation || {};
  const discrepancies = details.discrepancy_scores || {};

  const handleAction = async (status) => {
    setSubmitting(true);
    try {
      await api.reviewAlert(alert.alert_id, {
        status,
        reviewed_by: officerName,
        review_notes: reviewNotes || `Reviewed and marked as ${status}`
      });
      if (onReviewed) onReviewed();
      onClose();
    } catch (err) {
      console.error('Review failed:', err);
      alert('Failed to submit review: ' + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md overflow-y-auto">
      <div className="relative w-full max-w-4xl bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden my-8">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-bold text-slate-100">{alert.title}</h3>
                <SeverityBadge severity={alert.severity} />
                <StatusBadge status={alert.status} />
              </div>
              <p className="text-xs text-slate-400">
                Alert ID: <span className="font-mono text-cyan-400">{alert.alert_id}</span> | Time: {new Date(alert.timestamp).toLocaleString()}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6">
          {/* Executive Overview Box */}
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs space-y-1.5">
            <div className="flex items-center space-x-2 text-amber-400 font-bold">
              <AlertTriangle className="w-4 h-4" />
              <span>AI CORRELATION ANALYSIS & EVIDENCE DOSSIER</span>
            </div>
            <p className="text-slate-300 leading-relaxed">{alert.description}</p>
          </div>

          {/* Side-by-Side Observation Panels */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Panel A (Previous / Source Sighting) */}
            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <span className="text-xs font-bold text-cyan-400 flex items-center space-x-1.5">
                  <Camera className="w-4 h-4" />
                  <span>OBSERVATION A — {obsA.camera_id || alert.source_camera_id || 'CAM01'}</span>
                </span>
                <span className="text-[10px] text-slate-400 font-mono">
                  {obsA.timestamp ? new Date(obsA.timestamp).toLocaleTimeString() : 'Earlier'}
                </span>
              </div>

              {/* Visual Simulated Crop Placeholder */}
              <div className="h-32 w-full rounded-lg bg-slate-900 border border-slate-700/60 flex flex-col items-center justify-center relative overflow-hidden">
                <Car className="w-12 h-12 text-slate-400 mb-1" />
                <span className="text-xs font-mono font-bold text-slate-200">
                  {obsA.color || 'WHITE'} {(obsA.vehicle_type || 'SEDAN').toUpperCase()}
                </span>
                <div className="mt-1 px-2 py-0.5 bg-emerald-950 border border-emerald-700 text-emerald-300 text-[11px] font-mono font-bold rounded">
                  PLATE: {obsA.plate_text || alert.plate_text}
                </div>
              </div>

              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between text-slate-400">
                  <span>Vehicle Type:</span>
                  <span className="text-slate-200 font-semibold uppercase">{obsA.vehicle_type || 'sedan'}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Observed Color:</span>
                  <span className="text-slate-200 font-semibold">{obsA.color || 'WHITE'}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>OCR Confidence:</span>
                  <span className="text-emerald-400 font-mono font-bold">
                    {Math.round((obsA.ocr_confidence || 0.95) * 100)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Panel B (New / Conflicting Sighting) */}
            <div className="p-4 rounded-xl bg-slate-950/70 border border-red-900/40 space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <span className="text-xs font-bold text-red-400 flex items-center space-x-1.5">
                  <Camera className="w-4 h-4" />
                  <span>OBSERVATION B — {obsB.camera_id || alert.target_camera_id || 'CAM04'}</span>
                </span>
                <span className="text-[10px] text-slate-400 font-mono">
                  {obsB.timestamp ? new Date(obsB.timestamp).toLocaleTimeString() : 'Recent'}
                </span>
              </div>

              {/* Visual Simulated Crop Placeholder */}
              <div className="h-32 w-full rounded-lg bg-slate-900 border border-red-800/60 flex flex-col items-center justify-center relative overflow-hidden">
                <Car className="w-12 h-12 text-red-400 mb-1" />
                <span className="text-xs font-mono font-bold text-slate-200">
                  {obsB.color || 'BLACK'} {(obsB.vehicle_type || 'SUV').toUpperCase()}
                </span>
                <div className="mt-1 px-2 py-0.5 bg-emerald-950 border border-emerald-700 text-emerald-300 text-[11px] font-mono font-bold rounded">
                  PLATE: {obsB.plate_text || alert.plate_text}
                </div>
              </div>

              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between text-slate-400">
                  <span>Vehicle Type:</span>
                  <span className="text-red-300 font-semibold uppercase">{obsB.vehicle_type || 'SUV'}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Observed Color:</span>
                  <span className="text-red-300 font-semibold">{obsB.color || 'BLACK'}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>OCR Confidence:</span>
                  <span className="text-emerald-400 font-mono font-bold">
                    {Math.round((obsB.ocr_confidence || 0.94) * 100)}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Anomaly & Discrepancy Breakdown */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Discrepancy Correlation Matrix
            </h4>
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase">Visual Match Score</span>
                <p className="text-sm font-bold text-red-400 font-mono mt-1">
                  {discrepancies.type_match_score !== undefined ? `${Math.round(discrepancies.type_match_score * 100)}%` : '0% (Mismatch)'}
                </p>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase">Color Similarity</span>
                <p className="text-sm font-bold text-red-400 font-mono mt-1">
                  {discrepancies.color_match_score !== undefined ? `${Math.round(discrepancies.color_match_score * 100)}%` : '0% (Conflict)'}
                </p>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase">Estimated Speed</span>
                <p className="text-sm font-bold text-cyan-400 font-mono mt-1">
                  {discrepancies.estimated_transit_speed_kmh ? `${discrepancies.estimated_transit_speed_kmh} km/h` : 'N/A'}
                </p>
              </div>
            </div>
          </div>

          {/* Human-in-the-Loop Review Controls */}
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-300">Human Verification Decision</span>
              <span className="text-[10px] text-slate-500">Authorized Operator Review Required</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Reviewing Officer</label>
                <input
                  type="text"
                  value={officerName}
                  onChange={(e) => setOfficerName(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200"
                />
              </div>
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Verification Notes</label>
                <input
                  type="text"
                  placeholder="e.g. Visual confirmation of cloned plate on conflicting SUV..."
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200"
                />
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                disabled={submitting}
                onClick={() => handleAction('DISMISSED_FALSE_POSITIVE')}
                className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold flex items-center space-x-1.5 transition"
              >
                <XCircle className="w-4 h-4" />
                <span>Dismiss False Positive</span>
              </button>

              <button
                disabled={submitting}
                onClick={() => handleAction('VERIFIED_ANOMALY')}
                className="px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center space-x-1.5 shadow-lg shadow-emerald-900/30 transition"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Verify Anomaly</span>
              </button>

              <button
                disabled={submitting}
                onClick={() => handleAction('UNDER_INVESTIGATION')}
                className="px-3.5 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold flex items-center space-x-1.5 shadow-lg shadow-purple-900/30 transition"
              >
                <Briefcase className="w-4 h-4" />
                <span>Escalate to Case File</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
