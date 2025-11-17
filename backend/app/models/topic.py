"""
Topic model for thematic categorization of events.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Topic(Base):
    """
    Topic table for storing thematic topics extracted or assigned to events.

    Topics are higher-level semantic categories (e.g., "machine learning", "project planning")
    that help organize and retrieve related information.
    """
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)

    # Topic name (e.g., "Machine Learning", "Product Development")
    name = Column(String, nullable=False, unique=True, index=True)

    # Optional description of the topic
    description = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    event_topics = relationship("EventTopic", back_populates="topic", cascade="all, delete-orphan")


class EventTopic(Base):
    """
    Association table linking events to topics (many-to-many).

    Allows an event to belong to multiple topics and a topic to include multiple events.
    """
    __tablename__ = "event_topics"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)

    # Relevance score (0.0 - 1.0)
    relevance = Column(Integer, nullable=True)  # Store as int (0-100)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    event = relationship("Event", back_populates="event_topics")
    topic = relationship("Topic", back_populates="event_topics")

    # Composite index for efficient lookups
    __table_args__ = (
        Index("ix_event_topics_event_topic", "event_id", "topic_id", unique=True),
    )
