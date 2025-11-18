"""
Database connection and session management.
Provides SQLAlchemy engine, session factory, and base model class.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.config import get_settings

settings = get_settings()

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verify connections before using them
    echo=settings.debug,  # Log SQL statements in debug mode
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get a database session.
    Yields a session and ensures it's closed after use.

    Usage in FastAPI:
        @app.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    Creates all tables defined by models inheriting from Base.
    """
    # Import all models here to ensure they're registered with Base
    from app.models import user, source, event, entity, topic, timeline
    from app.models.user import User

    Base.metadata.create_all(bind=engine)

    # Ensure default demo user exists (Cloud deployments seed empty DBs)
    session = SessionLocal()
    try:
        default_user_id = 1
        existing = session.get(User, default_user_id)
        if not existing:
            demo_user = User(
                id=default_user_id,
                email="demo@timeline-thinker.app",
                name="Timeline Thinker Demo",
            )
            session.add(demo_user)
            session.commit()
    finally:
        session.close()
