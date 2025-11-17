"""
Models for tracking per-day user sessions and interactions.
"""
from datetime import date
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Text,
    DateTime,
    Date,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class SessionInteraction(Base):
    """
    Stores each question/answer pair so we can summarize daily sessions.
    """

    __tablename__ = "session_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"), nullable=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    session_date = Column(Date, nullable=False, index=True)

    user = relationship("User")
    source = relationship("Source")


class SessionSource(Base):
    """
    Tracks which sources are part of a user's session for a given day.
    """

    __tablename__ = "session_sources"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    session_date = Column(Date, nullable=False, index=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    removed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
    source = relationship("Source")

    __table_args__ = (
        UniqueConstraint("user_id", "source_id", "session_date", name="uq_session_source_per_day"),
    )
