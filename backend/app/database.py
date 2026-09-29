import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

logger = logging.getLogger("cityai.database")

# Create SQLAlchemy engine for SQLite (or configured DATABASE_URL)
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency for obtaining a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes the database schema and verifies connectivity."""
    try:
        # Create all tables defined in Base models
        Base.metadata.create_all(bind=engine)
        
        # Verify connection with a test query
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info(f"Database initialized successfully at: {settings.DATABASE_URL}")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def check_db_status() -> dict:
    """Checks and returns live connectivity status of the database."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {
            "status": "CONNECTED",
            "dialect": engine.dialect.name,
            "connected": True
        }
    except Exception as e:
        logger.error(f"Database health check error: {e}")
        return {
            "status": "DISCONNECTED",
            "dialect": engine.dialect.name if hasattr(engine, "dialect") else "unknown",
            "connected": False,
            "error": str(e)
        }
