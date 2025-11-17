"""
Entity model for named entities extracted from events.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Entity(Base):
    """
    Entity table for storing named entities (people, places, organizations, etc.)

    Entities are extracted from event text and used for:
    - Filtering and refinement during retrieval
    - Building connections between related events
    """
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)

    # Normalized entity name (e.g., "John Smith", "OpenAI", "New York")
    name = Column(String, nullable=False, unique=True, index=True)

    # Entity type (PERSON, ORG, GPE, etc. - from NER)
    entity_type = Column(String, nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    event_entities = relationship("EventEntity", back_populates="entity", cascade="all, delete-orphan")


class EventEntity(Base):
    """
    Association table linking events to entities (many-to-many).

    Allows an event to reference multiple entities and an entity to appear in multiple events.
    """
    __tablename__ = "event_entities"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)

    # Confidence score from entity extraction (0.0 - 1.0)
    confidence = Column(Integer, nullable=True)  # Store as int (0-100) for simplicity

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    event = relationship("Event", back_populates="event_entities")
    entity = relationship("Entity", back_populates="event_entities")

    # Composite index for efficient lookups
    __table_args__ = (
        Index("ix_event_entities_event_entity", "event_id", "entity_id", unique=True),
    )
