import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings


def create_db_engine():
    target_url = settings.DATABASE_URL

    # If postgresql specified, test connection
    if target_url.startswith("postgresql"):
        try:
            # Try connecting with short timeout
            test_engine = create_engine(target_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
            with test_engine.connect() as conn:
                pass
            print(f"🐘 Connected to PostgreSQL database at {target_url.split('@')[-1]}")
            return test_engine
        except Exception as e:
            print(f"⚠️ Could not reach PostgreSQL service ({type(e).__name__}). Using local SQLite database: civiceye_dev.db")
            target_url = "sqlite:///./civiceye_dev.db"

    connect_args = {}
    if target_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    return create_engine(target_url, connect_args=connect_args)


engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency for yielding database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
