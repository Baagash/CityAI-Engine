import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import LiveCameras from './pages/LiveCameras';
import CameraManagement from './pages/CameraManagement';
import VehicleDetection from './pages/VehicleDetection';
import PlaceholderPage from './pages/PlaceholderPage';
import { api } from './services/api';

export default function App() {
  const [telemetry, setTelemetry] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const fetchHealth = useCallback(async (isManual = false) => {
    if (isManual) setIsRefreshing(true);
    try {
      const res = await api.getSystemHealth();
      if (res.success && res.data) {
        setTelemetry({ ...res.data, latencyMs: res.latencyMs });
        setError(null);
      } else {
        setError(res.error || 'Unable to establish link with backend.');
      }
    } catch (err) {
      setError(err.message || 'Network anomaly detected.');
    } finally {
      setIsLoading(false);
      if (isManual) setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth(false);
    const interval = setInterval(() => {
      fetchHealth(false);
    }, 5000); // Live poll every 5s
    return () => clearInterval(interval);
  }, [fetchHealth]);

  const handleManualRefresh = () => {
    fetchHealth(true);
  };

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
        
        {/* Top Command Navbar */}
        <Navbar 
          systemStatus={error ? 'OFFLINE' : (telemetry?.status || 'ONLINE')}
          isRefreshing={isRefreshing}
          onRefresh={handleManualRefresh}
          isMobileMenuOpen={isMobileMenuOpen}
          setIsMobileMenuOpen={setIsMobileMenuOpen}
        />

        {/* Command Body */}
        <div className="flex flex-1 overflow-hidden relative">
          
          {/* Collapsible Sidebar */}
          <Sidebar 
            isOpen={isMobileMenuOpen} 
            onClose={() => setIsMobileMenuOpen(false)} 
          />

          {/* Main Telemetry Viewport */}
          <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto max-w-7xl mx-auto w-full">
            <Routes>
              {/* Dashboard */}
              <Route 
                path="/" 
                element={
                  <Dashboard 
                    telemetry={telemetry} 
                    isLoading={isLoading} 
                    error={error} 
                    onRetry={handleManualRefresh} 
                  />
                } 
              />

              {/* Live Cameras */}
              <Route 
                path="/live-cameras" 
                element={<LiveCameras />} 
              />

              {/* Camera Management */}
              <Route 
                path="/camera-management" 
                element={<CameraManagement />} 
              />

              {/* Vehicle Detection & Tracking (Phase 3) */}
              <Route 
                path="/vehicle-search" 
                element={<VehicleDetection />} 
              />
              <Route 
                path="/detections" 
                element={<VehicleDetection />} 
              />


              {/* Trajectories (Phase 4) */}
              <Route 
                path="/trajectories" 
                element={
                  <PlaceholderPage 
                    title="Trajectories" 
                    phase="Phase 4"
                    description="Cross-camera vehicle spatiotemporal movement paths, graph route tracking, and transit timing analysis."
                    details={[
                      { title: "Graph Topology Engine", desc: "NetworkX camera graph connecting urban corridors and checkpoints." },
                      { title: "Transit Velocity Check", desc: "Mathematical velocity calculation between non-adjacent cameras." }
                    ]}
                  />
                } 
              />

              {/* Traffic Analytics (Phase 4) */}
              <Route 
                path="/analytics" 
                element={
                  <PlaceholderPage 
                    title="Traffic Analytics" 
                    phase="Phase 4"
                    description="City-wide traffic density, peak congestion forecasting, hourly flow heatmaps, and average corridor velocities."
                    details={[
                      { title: "Urban Density Heatmap", desc: "Spatial congestion distribution and bottleneck identification." },
                      { title: "Throughput Metrics", desc: "Vehicles per hour per zone with historical comparisons." }
                    ]}
                  />
                } 
              />

              {/* Alerts (Phase 4) */}
              <Route 
                path="/alerts" 
                element={
                  <PlaceholderPage 
                    title="Alerts" 
                    phase="Phase 4"
                    description="Human-in-the-loop security alerts, cloned plate warnings, impossible transit velocity triggers, and audit workflows."
                    details={[
                      { title: "Cloned Plate Detection", desc: "Flagging same plate seen on separate cameras in impossible timeframes." },
                      { title: "Human Verification", desc: "Officer approval workflow with high/low confidence categorization." }
                    ]}
                  />
                } 
              />

              {/* Investigations (Phase 4) */}
              <Route 
                path="/investigations" 
                element={
                  <PlaceholderPage 
                    title="Investigations" 
                    phase="Phase 4"
                    description="Case dossier generation, multi-camera evidence compilation, exportable law-enforcement investigation records."
                    details={[
                      { title: "Case Dossiers", desc: "Consolidated evidence files with chain-of-custody timestamps." },
                      { title: "Evidence Export", desc: "PDF / JSON summary packages with high-res detection crops." }
                    ]}
                  />
                } 
              />

              {/* Settings */}
              <Route 
                path="/settings" 
                element={
                  <PlaceholderPage 
                    title="Settings" 
                    phase="Phase 2"
                    description="System configuration, database connectivity parameters, OpenCV capture options, and MJPEG streaming settings."
                    details={[
                      { title: "FastAPI Runtime", desc: "Uvicorn server hosting REST endpoints at port 8000 / 8001." },
                      { title: "OpenCV Ingest Engine", desc: "VideoCapture thread manager with automated loop pacing." }
                    ]}
                  />
                } 
              />

              {/* Aliases & Fallbacks */}
              <Route path="/cctv" element={<Navigate to="/live-cameras" replace />} />
              <Route path="/map" element={<Navigate to="/" replace />} />
              <Route path="/vehicles" element={<Navigate to="/vehicle-search" replace />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>

      </div>
    </BrowserRouter>
  );
}
