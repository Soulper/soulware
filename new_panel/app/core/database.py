from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool
from app.core.config import settings
import os
import logging

logger = logging.getLogger(__name__)

# Detect if running on Railway/Production
IS_RAILWAY = os.getenv("RAILWAY_STATIC_URL") is not None or os.getenv("PORT") is not None

# Optimized connection pool
if IS_RAILWAY:
    # Use StaticPool for SQLite in single-instance containers to avoid locking issues
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=QueuePool,
        pool_size=50,
        max_overflow=50,
        pool_timeout=60,
        pool_recycle=1800,
        pool_pre_ping=True,
    )

# Log pool stats periodically
@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    logger.debug(f"Connection checked out. Pool size: {engine.pool.size()}")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    logger.debug(f"Connection returned to pool")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    from app.models import user
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency that provides a database session with proper cleanup"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()
