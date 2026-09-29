import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  Filter, 
  CheckCircle2, 
  XCircle, 
  Briefcase, 
  Search, 
  RefreshCw,
  Eye
} from 'lucide-react';
import { AlertTypeBadge, SeverityBadge, StatusBadge } from '../components/AlertBadge';
import SideBySideEvidenceModal from '../components/SideBySideEvidenceModal';
import { api } from '../services/api';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const data = await api.getAlerts({
        severity: severityFilter,
        status: statusFilter,
        alert_type: typeFilter
      });
      setAlerts(data);
    } catch (err) {
      console.error('Alerts load error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [severityFilter, statusFilter, typeFilter]);

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-red-400" />
            <span className="text-[10px] uppercase font-bold text-red-400 tracking-wider">
              HUMAN-IN-THE-LOOP VERIFICATION QUEUE
            </span>
          </div>
          <h1 className="text-xl font-black text-slate-100 mt-0.5">Alert Verification & Audit Log</h1>
          <p className="text-xs text-slate-400">
            Review AI anomaly alerts, inspect side-by-side evidence dossiers, and log authorized human decisions.
          </p>
        </div>

        <button
          onClick={loadAlerts}
          className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl flex items-center space-x-1.5 transition self-start md:self-auto"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh Queue</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Filter Severity</label>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-400"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="WARNING">Warning</option>
            <option value="INFO">Info</option>
          </select>
        </div>

        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Filter Status</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-400"
          >
            <option value="">All Statuses</option>
            <option value="REQUIRES_VERIFICATION">Requires Verification</option>
            <option value="VERIFIED_ANOMALY">Verified Anomaly</option>
            <option value="UNDER_INVESTIGATION">Under Investigation</option>
            <option value="DISMISSED_FALSE_POSITIVE">Dismissed False Positive</option>
          </select>
        </div>

        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Filter Anomaly Type</label>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-400"
          >
            <option value="">All Anomaly Types</option>
            <option value="POSSIBLE_DUPLICATE_PLATE">Possible Duplicate Plate</option>
            <option value="IMPOSSIBLE_TRAVEL">Impossible / Unusual Travel</option>
            <option value="REGISTRY_MISMATCH">DMV Registry Mismatch</option>
            <option value="TRAFFIC_CONGESTION">Traffic Congestion</option>
          </select>
        </div>
      </div>

      {/* Alerts Table */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900 overflow-hidden shadow-xl">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950 text-slate-400 font-semibold uppercase text-[10px] border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">Severity / Type</th>
              <th className="py-3 px-4">Subject Plate</th>
              <th className="py-3 px-4">Alert Description</th>
              <th className="py-3 px-4">Time</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4 text-right">Evidence Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-sans">
            {alerts.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-slate-500 text-xs">
                  No alerts match the selected criteria.
                </td>
              </tr>
            ) : (
              alerts.map((alert) => (
                <tr key={alert.alert_id} className="hover:bg-slate-850/60 transition">
                  <td className="py-3 px-4 space-y-1">
                    <div className="flex items-center space-x-1.5">
                      <SeverityBadge severity={alert.severity} />
                    </div>
                    <div>
                      <AlertTypeBadge type={alert.alert_type} />
                    </div>
                  </td>

                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 bg-slate-950 border border-slate-700 rounded text-cyan-300 font-mono font-bold text-xs">
                      {alert.plate_text || 'UNKNOWN'}
                    </span>
                  </td>

                  <td className="py-3 px-4 max-w-md">
                    <p className="font-bold text-slate-200 line-clamp-1">{alert.title}</p>
                    <p className="text-[11px] text-slate-400 line-clamp-2 mt-0.5">{alert.description}</p>
                  </td>

                  <td className="py-3 px-4 text-slate-400 font-mono text-[11px] whitespace-nowrap">
                    {new Date(alert.timestamp).toLocaleString([], {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </td>

                  <td className="py-3 px-4 whitespace-nowrap">
                    <StatusBadge status={alert.status} />
                  </td>

                  <td className="py-3 px-4 text-right whitespace-nowrap">
                    <button
                      onClick={() => setSelectedAlert(alert)}
                      className="px-3 py-1.5 bg-cyan-600/20 hover:bg-cyan-600/40 border border-cyan-500/40 text-cyan-300 rounded-lg text-xs font-semibold flex items-center space-x-1 ml-auto transition"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Review Evidence</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Review Modal */}
      {selectedAlert && (
        <SideBySideEvidenceModal
          alert={selectedAlert}
          onClose={() => setSelectedAlert(null)}
          onReviewed={loadAlerts}
        />
      )}
    </div>
  );
}
