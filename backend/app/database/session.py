from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Attempt to create engine for configured database; if it fails (e.g., no local Postgres during tests),
# fall back to an in-memory SQLite database to allow tests to run without external dependencies.
try:
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
    # Test connection eagerly to surface configuration errors early
    try:
        conn = engine.connect()
        conn.close()
    except Exception:
        # If connection test fails, raise to trigger fallback
        raise
except Exception as exc:
    # In production we should fail fast instead of silently falling back.
    if getattr(settings, "ENVIRONMENT", "development").lower() == "production":
        logger.error("Database connection failed in production: %s", exc)
        raise
    logger.warning("Database connection failed (%s). Falling back to file-based SQLite for tests.", exc)
    # Use a file-backed SQLite DB to ensure the database is shared across connections
    engine = create_engine("sqlite:///./backend_test.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
