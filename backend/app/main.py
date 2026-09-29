import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db, SessionLocal
from app.models.camera import Camera, CameraTopology
from app.api import system, cameras, detections, plates, reid
from app.services.video_processor import stream_manager
from app.utils.video_generator import generate_demo_traffic_video

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cityai.main")

def seed_demo_cameras_and_topology():
    """
    Seeds the 4 required DEMO CAMERAS and topology transitions if not present.
    Creates sample video files in backend/videos/ for zero-dependency local testing.
    """
    db = SessionLocal()
    try:
        # 1. Ensure sample demo videos exist in backend/videos/
        demo_videos = [
            settings.VIDEOS_DIR / "demo_traffic_cam01.mp4",
            settings.VIDEOS_DIR / "demo_traffic_cam02.mp4",
            settings.VIDEOS_DIR / "demo_traffic_cam03.mp4",
            settings.VIDEOS_DIR / "demo_traffic_cam04.mp4"
        ]
        for vid_path in demo_videos:
            needs_gen = not vid_path.exists()
            if not needs_gen:
                try:
                    import cv2
                    test_cap = cv2.VideoCapture(str(vid_path))
                    if not test_cap or not test_cap.isOpened() or test_cap.get(cv2.CAP_PROP_FRAME_COUNT) <= 0:
                        needs_gen = True
                    test_cap.release()
                except Exception:
                    needs_gen = True
            if needs_gen:
                generate_demo_traffic_video(vid_path, duration_seconds=10, fps=25)

        demo_video_path_1, demo_video_path_2, demo_video_path_3, demo_video_path_4 = demo_videos

        # 2. Seed Demo Cameras
        existing_count = db.query(Camera).count()
        if existing_count == 0:
            demo_cameras = [
                Camera(
                    camera_id="CAM01",
                    camera_name="CAM01 - Demo Junction North",
                    location_name="Demo Junction North",
                    latitude=13.0827,
                    longitude=80.2707,
                    zone="Zone A - Downtown",
                    direction="NORTHBOUND",
                    source_type="LOCAL_VIDEO",
                    local_video_path=str(demo_video_path_1),
                    status="STOPPED",
                    description="North arterial junction checkpoint. High commuter density. (DEMO CAMERA)",
                    is_demo=True
                ),
                Camera(
                    camera_id="CAM02",
                    camera_name="CAM02 - Demo Junction East",
                    location_name="Demo Junction East",
                    latitude=13.0850,
                    longitude=80.2780,
                    zone="Zone A - Downtown",
                    direction="EASTBOUND",
                    source_type="LOCAL_VIDEO",
                    local_video_path=str(demo_video_path_2),
                    status="STOPPED",
                    description="East financial corridor monitoring point. (DEMO CAMERA)",
                    is_demo=True
                ),
                Camera(
                    camera_id="CAM03",
                    camera_name="CAM03 - Demo Highway",
                    location_name="Demo Highway",
                    latitude=13.0910,
                    longitude=80.2850,
                    zone="Zone B - Highway",
                    direction="NORTHBOUND",
                    source_type="LOCAL_VIDEO",
                    local_video_path=str(demo_video_path_3),
                    status="STOPPED",
                    description="Multi-lane expressway high-speed corridor checkpoint. (DEMO CAMERA)",
                    is_demo=True
                ),
                Camera(
                    camera_id="CAM04",
                    camera_name="CAM04 - Demo Central Road",
                    location_name="Demo Central Road",
                    latitude=13.0780,
                    longitude=80.2650,
                    zone="Zone C - Commercial",
                    direction="SOUTHBOUND",
                    source_type="LOCAL_VIDEO",
                    local_video_path=str(demo_video_path_4),
                    status="STOPPED",
                    description="Central commercial avenue multi-directional node. (DEMO CAMERA)",
                    is_demo=True
                )
            ]
            db.add_all(demo_cameras)
            db.commit()
            logger.info("Successfully seeded 4 DEMO CAMERAS (CAM01, CAM02, CAM03, CAM04).")

        # 3. Seed Topology Transitions
        topology_count = db.query(CameraTopology).count()
        if topology_count == 0:
            demo_transitions = [
                CameraTopology(
                    source_camera_id="CAM01",
                    destination_camera_id="CAM02",
                    distance_km=1.2,
                    expected_min_minutes=2.0,
                    expected_max_minutes=6.0,
                    direction="EASTBOUND"
                ),
                CameraTopology(
                    source_camera_id="CAM02",
                    destination_camera_id="CAM03",
                    distance_km=2.4,
                    expected_min_minutes=3.0,
                    expected_max_minutes=8.0,
                    direction="NORTHBOUND"
                ),
                CameraTopology(
                    source_camera_id="CAM01",
                    destination_camera_id="CAM04",
                    distance_km=1.8,
                    expected_min_minutes=2.5,
                    expected_max_minutes=7.0,
                    direction="SOUTHBOUND"
                ),
                CameraTopology(
                    source_camera_id="CAM04",
                    destination_camera_id="CAM03",
                    distance_km=3.1,
                    expected_min_minutes=4.0,
                    expected_max_minutes=10.0,
                    direction="NORTHEAST"
                ),
            ]
            db.add_all(demo_transitions)
            db.commit()
            logger.info("Successfully seeded 4 Camera Topology transitions.")

    except Exception as e:
        logger.error(f"Error seeding demo cameras and topology: {e}")
    finally:
        db.close()

# Alias for backwards-compatibility with test suites
seed_database = seed_demo_cameras_and_topology

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan Context Manager.
    Handles startup (DB initialization, Demo Camera seeding) and graceful shutdown.
    """
    logger.info(f"Starting {settings.SYSTEM_TITLE} v{settings.VERSION} [Phase 3]...")
    db_ok = init_db()
    if db_ok:
        logger.info("SQLite database verified and initialized.")
        seed_demo_cameras_and_topology()
    else:
        logger.warning("Database initialization encountered an issue.")
    
    yield
    
    logger.info("Releasing all active camera video streams...")
    # Release all streams in stream_manager
    for cam_id in list(stream_manager._processors.keys()):
        stream_manager.stop_camera(cam_id)
    logger.info(f"Shutting down {settings.SYSTEM_TITLE} cleanly...")

app = FastAPI(
    title=settings.SYSTEM_TITLE,
    version=settings.VERSION,
    description="City-Wide AI Traffic Command Center - Phase 3 Vehicle Detection & Multi-Object Tracking",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file mounts
app.mount("/videos", StaticFiles(directory=str(settings.VIDEOS_DIR)), name="videos")
app.mount("/snapshots", StaticFiles(directory=str(settings.SNAPSHOT_DIR)), name="snapshots")
app.mount("/evidence", StaticFiles(directory=str(settings.EVIDENCE_DIR)), name="evidence")

# Register Routers
app.include_router(system.router, prefix=settings.API_PREFIX)
app.include_router(system.router, prefix=settings.API_V1_STR)
app.include_router(cameras.router, prefix=settings.API_PREFIX)
app.include_router(cameras.router, prefix=settings.API_V1_STR)
app.include_router(detections.router, prefix=settings.API_PREFIX)
app.include_router(detections.router, prefix=settings.API_V1_STR)
app.include_router(plates.router, prefix=settings.API_PREFIX)
app.include_router(plates.router, prefix=settings.API_V1_STR)
app.include_router(plates.vehicle_router, prefix=settings.API_PREFIX)
app.include_router(plates.vehicle_router, prefix=settings.API_V1_STR)
app.include_router(reid.router, prefix=settings.API_PREFIX)
app.include_router(reid.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    """Root metadata endpoint."""
    return {
        "title": settings.SYSTEM_TITLE,
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "ONLINE",
        "phase": "PHASE 5 - VEHICLE RE-IDENTIFICATION",
        "endpoints": {
            "health": f"{settings.API_PREFIX}/system/health",
            "cameras": f"{settings.API_PREFIX}/cameras",
            "topology": f"{settings.API_PREFIX}/cameras/topology",
            "stats": f"{settings.API_PREFIX}/cameras/stats",
            "detections_live": f"{settings.API_PREFIX}/detections/live",
            "detections": f"{settings.API_PREFIX}/detections",
            "tracks": f"{settings.API_PREFIX}/detections/tracks",
            "detection_stats": f"{settings.API_PREFIX}/detections/stats",
            "plates": f"{settings.API_PREFIX}/plates",
            "plate_search": f"{settings.API_PREFIX}/plates/search",
            "plate_stats": f"{settings.API_PREFIX}/plates/stats",
            "vehicles": f"{settings.API_PREFIX}/vehicles",
            "reid_compare": f"{settings.API_PREFIX}/reid/compare",
            "reid_matches": f"{settings.API_PREFIX}/reid/matches",
            "reid_stats": f"{settings.API_PREFIX}/reid/stats",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


