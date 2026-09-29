import math
import networkx as nx
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

class CameraTopologyEngine:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.camera_metadata: Dict[str, Dict[str, Any]] = {}
        self._init_topology()

    def _init_topology(self):
        """Initializes the urban camera network graph with GPS coordinates and directional edge metrics."""
        # 4 Core Demo Cameras
        cameras = [
            {
                "camera_id": "CAM01",
                "name": "CAM01 - North Ring Road Interchange",
                "location": "North Ring Road, Outer Junction",
                "lat": 13.0827,
                "lon": 80.2707,
                "zone": "North Corridor",
                "direction": "Southbound"
            },
            {
                "camera_id": "CAM02",
                "name": "CAM02 - Central Business District Junction",
                "location": "Anna Salai - Mount Road Central",
                "lat": 13.0604,
                "lon": 80.2496,
                "zone": "Downtown Central",
                "direction": "South-West"
            },
            {
                "camera_id": "CAM03",
                "name": "CAM03 - Tech Park Expressway Tollway",
                "location": "OMR Expressway KM 12",
                "lat": 12.9716,
                "lon": 80.2435,
                "zone": "IT Expressway",
                "direction": "Southbound"
            },
            {
                "camera_id": "CAM04",
                "name": "CAM04 - South Harbour Terminal Gateway",
                "location": "Port Access Road & South Terminal",
                "lat": 12.9249,
                "lon": 80.2315,
                "zone": "South Terminal",
                "direction": "Eastbound"
            }
        ]

        for cam in cameras:
            cid = cam["camera_id"]
            self.camera_metadata[cid] = cam
            self.graph.add_node(cid, **cam)

        # Connect road topology with distance (km) and min/max plausible travel times (seconds)
        # Assuming typical urban speed limits: 40 km/h - 80 km/h, emergency upper bound 120 km/h
        edges = [
            # CAM01 -> CAM02 (~3.5 km, ~4 mins at 50 km/h = 240s, min=105s at 120km/h)
            ("CAM01", "CAM02", 3.5, 105, 900, "Southbound Corridor"),
            ("CAM02", "CAM01", 3.5, 105, 900, "Northbound Corridor"),
            # CAM02 -> CAM03 (~10.2 km, ~12 mins at 50 km/h = 720s, min=306s at 120km/h)
            ("CAM02", "CAM03", 10.2, 306, 2400, "Expressway South"),
            ("CAM03", "CAM02", 10.2, 306, 2400, "Expressway North"),
            # CAM03 -> CAM04 (~5.8 km, ~7 mins at 50 km/h = 420s, min=174s at 120km/h)
            ("CAM03", "CAM04", 5.8, 174, 1500, "Port Connector"),
            ("CAM04", "CAM03", 5.8, 174, 1500, "Port Connector Return"),
            # Direct alternate bypass CAM01 -> CAM04 (~18.0 km, min=540s at 120km/h)
            ("CAM01", "CAM04", 18.0, 540, 4200, "Peripheral Bypass"),
            ("CAM04", "CAM01", 18.0, 540, 4200, "Peripheral Bypass North")
        ]

        for src, dst, dist, t_min, t_max, direction in edges:
            self.graph.add_edge(
                src, dst,
                distance_km=dist,
                min_time_sec=t_min,
                max_time_sec=t_max,
                direction=direction
            )

    def get_all_cameras(self) -> List[Dict[str, Any]]:
        return list(self.camera_metadata.values())

    def get_camera(self, camera_id: str) -> Optional[Dict[str, Any]]:
        return self.camera_metadata.get(camera_id)

    def get_topology_edges(self) -> List[Dict[str, Any]]:
        result = []
        for u, v, data in self.graph.edges(data=True):
            result.append({
                "source_camera": u,
                "destination_camera": v,
                "distance_km": data.get("distance_km", 0.0),
                "expected_min_travel_time_sec": data.get("min_time_sec", 0),
                "expected_max_travel_time_sec": data.get("max_time_sec", 0),
                "direction": data.get("direction", "Unknown")
            })
        return result

    def get_distance_and_transit(self, source_cam: str, dest_cam: str) -> Optional[Dict[str, Any]]:
        """Finds shortest path distance and minimum plausible travel time between any two cameras."""
        if source_cam == dest_cam:
            return {"distance_km": 0.0, "min_time_sec": 0, "path": [source_cam]}

        try:
            if not self.graph.has_node(source_cam) or not self.graph.has_node(dest_cam):
                return None
            path = nx.shortest_path(self.graph, source_cam, dest_cam, weight="distance_km")
            total_dist = 0.0
            total_min_time = 0.0
            for i in range(len(path) - 1):
                edge_data = self.graph[path[i]][path[i+1]]
                total_dist += edge_data.get("distance_km", 0.0)
                total_min_time += edge_data.get("min_time_sec", 0.0)
            return {
                "distance_km": round(total_dist, 2),
                "min_time_sec": total_min_time,
                "path": path
            }
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            # Compute haversine straight-line distance if graph disconnected
            c1 = self.camera_metadata.get(source_cam)
            c2 = self.camera_metadata.get(dest_cam)
            if c1 and c2:
                dist = self._haversine(c1["lat"], c1["lon"], c2["lat"], c2["lon"])
                # At 120 km/h, min_time = (dist / 120) * 3600
                min_time = (dist / 120.0) * 3600.0
                return {"distance_km": round(dist, 2), "min_time_sec": min_time, "path": [source_cam, dest_cam]}
            return None

    def calculate_inter_camera_speed(
        self,
        source_cam: str,
        dest_cam: str,
        time_elapsed_sec: float
    ) -> Tuple[Optional[float], Optional[float], bool, str]:
        """
        Calculates inferred road travel speed between cameras.
        Returns (distance_km, speed_kmh, is_impossible, explanation).
        """
        if time_elapsed_sec <= 0:
            return 0.0, 999.9, True, "Simultaneous sighting at multiple cameras (Teleportation anomaly)."

        route_info = self.get_distance_and_transit(source_cam, dest_cam)
        if not route_info:
            return None, None, False, "Unknown camera topology pair."

        distance_km = route_info["distance_km"]
        if distance_km == 0:
            return 0.0, 0.0, False, "Same camera observation."

        # Speed = (distance in km) / (time in hours)
        speed_kmh = (distance_km / (time_elapsed_sec / 3600.0))

        # Check physical feasibility
        min_allowed_time = route_info["min_time_sec"]
        is_impossible = (time_elapsed_sec < min_allowed_time * 0.7) or (speed_kmh > 150.0)

        explanation = f"Estimated transit speed: {speed_kmh:.1f} km/h across {distance_km:.1f} km in {time_elapsed_sec:.0f}s."
        if is_impossible:
            explanation = (
                f"IMPOSSIBLE TRAVEL: Required speed of {speed_kmh:.1f} km/h exceeds maximum physical roadway limit "
                f"(Distance: {distance_km:.1f} km in {time_elapsed_sec:.0f}s, min required: {min_allowed_time:.0f}s)."
            )

        return round(distance_km, 2), round(speed_kmh, 1), is_impossible, explanation

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

topology_engine = CameraTopologyEngine()
