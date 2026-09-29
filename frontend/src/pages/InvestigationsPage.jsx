import React, { useState, useEffect } from 'react';
import { 
  Briefcase, 
  Plus, 
  FileText, 
  Clock, 
  User, 
  CheckCircle, 
  AlertCircle,
  MessageSquare,
  Printer,
  ChevronRight
} from 'lucide-react';
import InvestigationDossierModal from '../components/InvestigationDossierModal';
import { api } from '../services/api';

export default function InvestigationsPage() {
  const [cases, setCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [dossierCaseId, setDossierCaseId] = useState(null);
  const [newNote, setNewNote] = useState('');
  const [loading, setLoading] = useState(true);

  // New Case Form State
  const [caseTitle, setCaseTitle] = useState('');
  const [officerName, setOfficerName] = useState('Special Investigator - Unit 4');
  const [targetPlate, setTargetPlate] = useState('');
  const [priority, setPriority] = useState('HIGH');
  const [summary, setSummary] = useState('');

  const loadCases = async () => {
    setLoading(true);
    try {
      const data = await api.getInvestigationCases();
      setCases(data);
      if (data.length > 0 && !selectedCase) {
        setSelectedCase(data[0]);
      }
    } catch (err) {
      console.error('Cases load error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, []);

  const handleCreateCase = async (e) => {
    e.preventDefault();
    try {
      await api.createInvestigationCase({
        title: caseTitle,
        assigned_officer: officerName,
        target_plate: targetPlate.toUpperCase().trim(),
        priority,
        summary
      });
      setShowCreateModal(false);
      setCaseTitle('');
      setTargetPlate('');
      setSummary('');
      loadCases();
    } catch (err) {
      console.error('Create case failed:', err);
      alert('Failed to create case: ' + err.message);
    }
  };

  const handleAddNote = async () => {
    if (!newNote.trim() || !selectedCase) return;
    try {
      await api.updateInvestigationCase(selectedCase.case_id, {
        notes: newNote.trim()
      });
      setNewNote('');
      // Reload updated case
      const updated = await api.getInvestigationCases();
      setCases(updated);
      const cur = updated.find(c => c.case_id === selectedCase.case_id);
      if (cur) setSelectedCase(cur);
    } catch (err) {
      console.error('Update note error:', err);
    }
  };

  const handleUpdateStatus = async (status) => {
    if (!selectedCase) return;
    try {
      await api.updateInvestigationCase(selectedCase.case_id, { status });
      const updated = await api.getInvestigationCases();
      setCases(updated);
      const cur = updated.find(c => c.case_id === selectedCase.case_id);
      if (cur) setSelectedCase(cur);
    } catch (err) {
      console.error('Status update error:', err);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Briefcase className="w-4 h-4 text-purple-400" />
            <span className="text-[10px] uppercase font-bold text-purple-400 tracking-wider">
              OPERATIONAL CASE FILES
            </span>
          </div>
          <h1 className="text-xl font-black text-slate-100 mt-0.5">Investigation Case Management</h1>
          <p className="text-xs text-slate-400">
            Formally manage suspicious cloned plate investigations, log analyst chronicles, and export intelligence dossiers.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold rounded-xl flex items-center space-x-1.5 transition shadow-lg shadow-purple-900/30 self-start md:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Open New Investigation</span>
        </button>
      </div>

      {/* Main Grid: Cases List (1 Col) & Case Detail & Timeline (2 Cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cases List */}
        <div className="space-y-3">
          <div className="flex justify-between items-center text-xs font-semibold text-slate-400 px-1">
            <span>Case Files ({cases.length})</span>
            <span className="text-[10px]">Select to review notes</span>
          </div>

          <div className="space-y-2.5 max-h-[620px] overflow-y-auto pr-1">
            {cases.length === 0 ? (
              <div className="p-8 rounded-xl bg-slate-900 border border-slate-800 text-center text-xs text-slate-500">
                No active investigation cases. Verify an alert to open a case file.
              </div>
            ) : (
              cases.map((c) => (
                <div
                  key={c.case_id}
                  onClick={() => setSelectedCase(c)}
                  className={`p-4 rounded-xl border cursor-pointer transition space-y-2 ${
                    selectedCase?.case_id === c.case_id
                      ? 'bg-purple-950/40 border-purple-500/80 shadow-[0_0_15px_rgba(168,85,247,0.15)]'
                      : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-purple-300">{c.case_id}</span>
                    <span className={`px-2 py-0.5 text-[10px] font-bold rounded uppercase ${
                      c.status === 'OPEN'
                        ? 'bg-purple-950 text-purple-300 border border-purple-700'
                        : 'bg-emerald-950 text-emerald-300 border border-emerald-700'
                    }`}>
                      {c.status}
                    </span>
                  </div>

                  <h4 className="text-xs font-bold text-slate-200 line-clamp-1">{c.title}</h4>

                  <div className="flex justify-between items-center text-[11px] text-slate-400">
                    <span>Target: <strong className="font-mono text-cyan-400">{c.target_plate || 'N/A'}</strong></span>
                    <span>{new Date(c.updated_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Selected Case Workspace (2 Cols) */}
        <div className="lg:col-span-2 space-y-5">
          {selectedCase ? (
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-6">
              {/* Top Banner */}
              <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2.5">
                    <span className="text-lg font-black text-slate-100">{selectedCase.title}</span>
                    <span className="text-xs font-mono px-2 py-0.5 bg-purple-950 text-purple-300 border border-purple-800 rounded">
                      {selectedCase.case_id}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Assigned: <strong className="text-slate-200">{selectedCase.assigned_officer}</strong> | Priority: <strong className="text-amber-400">{selectedCase.priority}</strong>
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setDossierCaseId(selectedCase.case_id)}
                    className="px-3.5 py-2 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold rounded-xl flex items-center space-x-1.5 transition shadow-lg shadow-purple-900/30"
                  >
                    <FileText className="w-4 h-4" />
                    <span>Generate Dossier</span>
                  </button>
                </div>
              </div>

              {/* Case Summary */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
                  Executive Case Narrative
                </span>
                <p className="text-xs text-slate-300 leading-relaxed">{selectedCase.summary}</p>
              </div>

              {/* Investigator Chronicle & Audit Notes */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
                    <MessageSquare className="w-4 h-4 text-purple-400" />
                    <span>Investigator Chronicle Logs</span>
                  </span>
                </div>

                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 max-h-52 overflow-y-auto font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
                  {selectedCase.notes || 'No chronicle entries logged yet.'}
                </div>

                {/* Add Note Bar */}
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    placeholder="Append new investigator observation or interview record..."
                    value={newNote}
                    onChange={(e) => setNewNote(e.target.value)}
                    className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-purple-400"
                  />
                  <button
                    onClick={handleAddNote}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition"
                  >
                    Log Entry
                  </button>
                </div>
              </div>

              {/* Status Controls */}
              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-between">
                <span className="text-xs text-slate-400">Case Operational State:</span>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleUpdateStatus('OPEN')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                      selectedCase.status === 'OPEN' ? 'bg-purple-600 text-white' : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    Active / Open
                  </button>
                  <button
                    onClick={() => handleUpdateStatus('CLOSED_RESOLVED')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                      selectedCase.status === 'CLOSED_RESOLVED' ? 'bg-emerald-600 text-white' : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    Resolve & Close
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-16 rounded-2xl bg-slate-900 border border-slate-800 text-center text-slate-500 text-xs">
              Select a case file to view details or generate intelligence dossier.
            </div>
          )}
        </div>
      </div>

      {/* Create Case Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-700 rounded-2xl p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-slate-100">Initialize New Investigation File</h3>
            <form onSubmit={handleCreateCase} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Case Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Investigation: Suspected Cloned Plate TN38AB1234"
                  value={caseTitle}
                  onChange={(e) => setCaseTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Target Plate</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. TN38AB1234"
                    value={targetPlate}
                    onChange={(e) => setTargetPlate(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 uppercase"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Assigned Officer</label>
                  <input
                    type="text"
                    value={officerName}
                    onChange={(e) => setOfficerName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Executive Summary</label>
                <textarea
                  rows={3}
                  required
                  placeholder="Describe initial anomaly reasons and cross-camera evidence..."
                  value={summary}
                  onChange={(e) => setSummary(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3.5 py-2 rounded-lg bg-slate-800 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-semibold"
                >
                  Create Case File
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Dossier Modal */}
      {dossierCaseId && (
        <InvestigationDossierModal
          caseId={dossierCaseId}
          onClose={() => setDossierCaseId(null)}
        />
      )}
    </div>
  );
}
