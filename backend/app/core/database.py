import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings


def create_db_engine():
    target_url = settings.DATABASE_URL
    is_production = settings.ENVIRONMENT.lower() == "production" or os.getenv("ENVIRONMENT", "").lower() == "production"

    if is_production and target_url.startswith("sqlite"):
        raise RuntimeError(
            "CRITICAL: Production environment is configured with an ephemeral SQLite database URL. "
            "A persistent PostgreSQL/Supabase database URL is required in production."
        )

    # If postgresql specified, test connection
    if target_url.startswith("postgresql"):
        try:
            # Connect with resilient 10-second timeout for cloud networks
            test_engine = create_engine(
                target_url,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={"connect_timeout": 10},
            )
            with test_engine.connect() as conn:
                pass
            print(f"🐘 Connected to PostgreSQL database at {target_url.split('@')[-1]}")
            return test_engine
        except Exception as e:
            if is_production:
                raise RuntimeError(
                    f"CRITICAL: Failed to connect to production PostgreSQL database: {e}. "
                    "Ephemeral SQLite fallback is strictly prohibited in production mode to prevent silent data loss."
                )
            print(f"⚠️ Could not reach PostgreSQL service ({type(e).__name__}). Dev fallback: Using local SQLite database: civiceye_dev.db")
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
