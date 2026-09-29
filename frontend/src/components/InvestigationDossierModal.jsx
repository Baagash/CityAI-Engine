import React, { useState, useEffect } from 'react';
import { X, Printer, Download, FileText, Shield, Clock, MapPin, CheckCircle } from 'lucide-react';
import { api } from '../services/api';

export default function InvestigationDossierModal({ caseId, onClose }) {
  const [dossier, setDossier] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!caseId) return;
    setLoading(true);
    api.getCaseDossier(caseId)
      .then(data => setDossier(data))
      .catch(err => console.error('Dossier error:', err))
      .finally(() => setLoading(false));
  }, [caseId]);

  if (!caseId) return null;

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadJSON = () => {
    if (!dossier) return;
    const blob = new Blob([JSON.stringify(dossier, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${caseId}_Intelligence_Dossier.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md overflow-y-auto">
      <div className="relative w-full max-w-3xl bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden my-6 text-slate-200">
        {/* Header with actions */}
        <div className="px-6 py-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <Shield className="w-5 h-5 text-purple-400" />
            <div>
              <h3 className="text-base font-bold text-slate-100">OFFICIAL INTELLIGENCE DOSSIER</h3>
              <p className="text-xs text-purple-400 font-mono">{caseId}</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handlePrint}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition"
            >
              <Printer className="w-4 h-4" />
              <span>Print</span>
            </button>
            <button
              onClick={handleDownloadJSON}
              className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition"
            >
              <Download className="w-4 h-4" />
              <span>Export JSON</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Dossier Document Content */}
        <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto">
          {loading ? (
            <div className="py-12 text-center text-slate-500 text-xs">Generating case evidence dossier...</div>
          ) : dossier ? (
            <>
              {/* Official Seal / Banner */}
              <div className="p-4 rounded-xl bg-slate-950 border border-purple-500/30 space-y-2">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-[10px] uppercase tracking-widest text-purple-400 font-bold">
                      {dossier.dossier_header?.classification}
                    </span>
                    <h2 className="text-lg font-black text-slate-100 mt-0.5">{dossier.dossier_header?.title}</h2>
                  </div>
                  <span className="px-2 py-0.5 bg-purple-950 border border-purple-700 text-purple-300 text-xs font-mono font-bold rounded">
                    STATUS: {dossier.dossier_header?.status}
                  </span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-2 border-t border-slate-800/80 text-xs text-slate-400">
                  <div>Assigned Officer: <span className="text-slate-200 font-semibold">{dossier.dossier_header?.assigned_officer}</span></div>
                  <div>Target Subject: <span className="text-cyan-400 font-mono font-bold">{dossier.target_subject?.plate_number}</span></div>
                  <div>Total Sightings: <span className="text-emerald-400 font-mono font-bold">{dossier.target_subject?.total_recorded_sightings}</span></div>
                </div>
              </div>

              {/* Executive Summary */}
              <div className="space-y-1.5">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Executive Summary</h4>
                <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-300 leading-relaxed">
                  {dossier.executive_summary}
                </div>
              </div>

              {/* Investigator Notes */}
              <div className="space-y-1.5">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Investigator Chronicle & Audit Notes</h4>
                <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300 whitespace-pre-wrap">
                  {dossier.investigator_chronicle_notes || 'No custom notes logged.'}
                </div>
              </div>

              {/* Sighting Timeline */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Camera Sighting Audit Logs ({dossier.sighting_audit_timeline?.length || 0})
                </h4>
                <div className="rounded-xl border border-slate-800 overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950 text-slate-400 font-semibold uppercase text-[10px] border-b border-slate-800">
                      <tr>
                        <th className="py-2.5 px-3">Camera</th>
                        <th className="py-2.5 px-3">Timestamp</th>
                        <th className="py-2.5 px-3">Observed Type/Color</th>
                        <th className="py-2.5 px-3">Speed</th>
                        <th className="py-2.5 px-3">OCR Conf</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-950/40 font-mono">
                      {dossier.sighting_audit_timeline?.map((item, idx) => (
                        <tr key={idx} className="hover:bg-slate-900/50">
                          <td className="py-2 px-3 text-cyan-400 font-bold">{item.camera_id}</td>
                          <td className="py-2 px-3 text-slate-400">{item.timestamp?.slice(0, 19).replace('T', ' ')}</td>
                          <td className="py-2 px-3 text-slate-200">{item.color} {item.vehicle_class}</td>
                          <td className="py-2 px-3 text-slate-300">{item.speed_kmh ? `${item.speed_kmh} km/h` : '—'}</td>
                          <td className="py-2 px-3 text-emerald-400 font-bold">
                            {Math.round(item.ocr_confidence * 100)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Disclaimer */}
              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-[11px] text-slate-500 leading-snug">
                {dossier.legal_disclaimer}
              </div>
            </>
          ) : (
            <div className="text-center text-red-400 text-xs py-8">Failed to generate case dossier.</div>
          )}
        </div>
      </div>
    </div>
  );
}
