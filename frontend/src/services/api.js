/**
 * CityAI Traffic Intelligence - Frontend API Service
 */

const API_BASE = '/api';

export const api = {
  // System Health
  async getSystemHealth() {
    const startTime = performance.now();
    try {
      const response = await fetch(`${API_BASE}/system/health`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' }
      });
      const latencyMs = Math.round(performance.now() - startTime);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return { success: true, data, latencyMs };
    } catch (error) {
      const latencyMs = Math.round(performance.now() - startTime);
      return { success: false, error: error.message || 'Failed to connect to backend server', latencyMs, data: null };
    }
  },

  // Cameras CRUD & Telemetry
  async getCameras(params = {}) {
    const query = new URLSearchParams();
    if (params.zone) query.append('zone', params.zone);
    if (params.status) query.append('status', params.status);

    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await fetch(`${API_BASE}/cameras${qs}`);
    if (!res.ok) throw new Error(`Failed to fetch cameras: ${res.statusText}`);
    return res.json();
  },

  async getCamera(cameraId) {
    const res = await fetch(`${API_BASE}/cameras/${encodeURIComponent(cameraId)}`);
    if (!res.ok) throw new Error(`Failed to fetch camera ${cameraId}: ${res.statusText}`);
    return res.json();
  },

  async createCamera(cameraData) {
    const res = await fetch(`${API_BASE}/cameras`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cameraData)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to create camera: ${res.statusText}`);
    }
    return res.json();
  },

  async updateCamera(cameraId, cameraData) {
    const res = await fetch(`${API_BASE}/cameras/${encodeURIComponent(cameraId)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cameraData)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to update camera: ${res.statusText}`);
    }
    return res.json();
  },

  async deleteCamera(cameraId) {
    const res = await fetch(`${API_BASE}/cameras/${encodeURIComponent(cameraId)}`, {
      method: 'DELETE'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to delete camera: ${res.statusText}`);
    }
    return res.json();
  },

  // Camera Video Stream Ingestion Actions
  async startCamera(cameraId) {
    const res = await fetch(`${API_BASE}/cameras/${encodeURIComponent(cameraId)}/start`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to start camera stream: ${res.statusText}`);
    }
    return res.json();
  },

  async stopCamera(cameraId) {
    const res = await fetch(`${API_BASE}/cameras/${encodeURIComponent(cameraId)}/stop`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to stop camera stream: ${res.statusText}`);
    }
    return res.json();
  },

  async getCameraStatus(cameraId) {
    const res = await fetch(`${API_BASE}/cameras/${encodeURIComponent(cameraId)}/status`);
    if (!res.ok) throw new Error(`Failed to fetch camera status for ${cameraId}`);
    return res.json();
  },

  getCameraStreamUrl(cameraId, annotated = false) {
    if (annotated) {
      return `${API_BASE}/cameras/${encodeURIComponent(cameraId)}/annotated-stream`;
    }
    return `${API_BASE}/cameras/${encodeURIComponent(cameraId)}/stream`;
  },

  getCameraAnnotatedStreamUrl(cameraId) {
    return `${API_BASE}/cameras/${encodeURIComponent(cameraId)}/annotated-stream`;
  },

  // Topology & Aggregated Stats
  async getCameraTopology() {
    const res = await fetch(`${API_BASE}/cameras/topology`);
    if (!res.ok) throw new Error(`Failed to fetch camera topology: ${res.statusText}`);
    return res.json();
  },

  async getCameraStats() {
    const res = await fetch(`${API_BASE}/cameras/stats`);
    if (!res.ok) throw new Error(`Failed to fetch camera stats: ${res.statusText}`);
    return res.json();
  },

  // Phase 3 — Real Vehicle Detection & Multi-Object Tracking
  async getLiveDetections() {
    const res = await fetch(`${API_BASE}/detections/live`);
    if (!res.ok) throw new Error(`Failed to fetch live detections: ${res.statusText}`);
    return res.json();
  },

  async getHistoricalDetections(params = {}) {
    const query = new URLSearchParams();
    if (params.camera_id) query.append('camera_id', params.camera_id);
    if (params.vehicle_class) query.append('vehicle_class', params.vehicle_class);
    if (params.min_confidence !== undefined) query.append('min_confidence', params.min_confidence);
    if (params.limit) query.append('limit', params.limit);
    if (params.offset) query.append('offset', params.offset);

    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await fetch(`${API_BASE}/detections${qs}`);
    if (!res.ok) throw new Error(`Failed to fetch historical detections: ${res.statusText}`);
    return res.json();
  },

  async getActiveTracks(cameraId = null) {
    const url = cameraId 
      ? `${API_BASE}/detections/tracks/${encodeURIComponent(cameraId)}`
      : `${API_BASE}/detections/tracks`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to fetch active tracks: ${res.statusText}`);
    return res.json();
  },

  async getDetectionStats() {
    const res = await fetch(`${API_BASE}/detections/stats`);
    if (!res.ok) throw new Error(`Failed to fetch detection stats: ${res.statusText}`);
    return res.json();
  },

  async detectImage(file, confidence = null) {
    const formData = new FormData();
    formData.append('file', file);
    const qs = confidence !== null ? `?confidence=${confidence}` : '';
    const res = await fetch(`${API_BASE}/detections/detect${qs}`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Inference failed: ${res.statusText}`);
    }
    return res.json();
  },

  // Phase 5 — Global Vehicle Intelligence & Multi-Camera Re-ID
  async searchVehicles(params = {}) {
    const query = new URLSearchParams();
    if (params.plate) query.append('plate', params.plate);
    if (params.global_id) query.append('global_id', params.global_id);
    if (params.vehicle_type) query.append('vehicle_type', params.vehicle_type);
    if (params.color) query.append('color', params.color);
    if (params.colour) query.append('colour', params.colour);

    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await fetch(`${API_BASE}/vehicles${qs}`);
    if (!res.ok) throw new Error(`Failed to search vehicles: ${res.statusText}`);
    return res.json();
  },

  async getVehicle(globalId) {
    const res = await fetch(`${API_BASE}/vehicles/${encodeURIComponent(globalId)}`);
    if (!res.ok) throw new Error(`Failed to fetch vehicle ${globalId}: ${res.statusText}`);
    return res.json();
  },

  async getVehicleTrajectories(globalId) {
    const res = await fetch(`${API_BASE}/vehicles/${encodeURIComponent(globalId)}/trajectories`);
    if (!res.ok) throw new Error(`Failed to fetch trajectories for ${globalId}: ${res.statusText}`);
    return res.json();
  },

  async matchReID(payload) {
    const res = await fetch(`${API_BASE}/vehicles/reid/match`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Re-ID Match request failed: ${res.statusText}`);
    }
    return res.json();
  },

  async compareObservations(payload) {
    const res = await fetch(`${API_BASE}/reid/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Re-ID Comparison failed: ${res.statusText}`);
    }
    return res.json();
  },

  async getReIDMatches(params = {}) {
    const query = new URLSearchParams();
    if (params.decision) query.append('decision', params.decision);
    if (params.camera_id) query.append('camera_id', params.camera_id);
    if (params.tracker_id) query.append('tracker_id', params.tracker_id);
    if (params.limit) query.append('limit', params.limit);
    if (params.offset) query.append('offset', params.offset);

    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await fetch(`${API_BASE}/reid/matches${qs}`);
    if (!res.ok) throw new Error(`Failed to fetch Re-ID matches: ${res.statusText}`);
    return res.json();
  },

  async getReIDStats() {
    const res = await fetch(`${API_BASE}/reid/stats`);
    if (!res.ok) throw new Error(`Failed to fetch Re-ID stats: ${res.statusText}`);
    return res.json();
  }
};

