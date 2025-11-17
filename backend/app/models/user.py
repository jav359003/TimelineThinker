"""
User model for authentication and data ownership.
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """
    User table for managing user accounts.
    Each user has their own isolated set of events, sources, and timelines.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    sources = relationship("Source", back_populates="user", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    daily_timelines = relationship("DailyTimeline", back_populates="user", cascade="all, delete-orphan")
    weekly_timelines = relationship("WeeklyTimeline", back_populates="user", cascade="all, delete-orphan")
