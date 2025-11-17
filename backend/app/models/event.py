"""
Event model representing normalized memory units.
Events are the core atomic unit of information in the Timeline Thinker.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Date, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base
from app.config import get_settings

settings = get_settings()


class Event(Base):
    """
    Event table storing normalized, chunked pieces of information.

    All ingested data (audio, documents, web pages) is normalized into events.
    Each event represents a semantic chunk of text with associated metadata.
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)

    # The type of event derived from source (audio, document, webpage, text)
    event_type = Column(String, nullable=False, index=True)

    # The actual text content of this chunk
    raw_text = Column(Text, nullable=False)

    # Position of this chunk within the source (0-indexed)
    chunk_index = Column(Integer, nullable=False, default=0)

    # When this event occurred or was created (from source timestamp or ingestion time)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # Date component for efficient daily bucketing
    date = Column(Date, nullable=False, index=True)

    # When this event was ingested into the system
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="events")
    source = relationship("Source", back_populates="events")
    embedding = relationship("EventEmbedding", back_populates="event", uselist=False, cascade="all, delete-orphan")
    event_entities = relationship("EventEntity", back_populates="event", cascade="all, delete-orphan")
    event_topics = relationship("EventTopic", back_populates="event", cascade="all, delete-orphan")

    # Composite indexes for common query patterns
    __table_args__ = (
        Index("ix_events_user_date", "user_id", "date"),
        Index("ix_events_user_timestamp", "user_id", "timestamp"),
        Index("ix_events_user_type", "user_id", "event_type"),
    )


class EventEmbedding(Base):
    """
    Event embeddings stored as vectors for semantic search.

    Separated into its own table for efficient vector operations.
    Uses pgvector extension for similarity search.
    """
    __tablename__ = "event_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Vector embedding (dimension configured in settings)
    embedding = Column(Vector(settings.embedding_dimension), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    event = relationship("Event", back_populates="embedding")

    # Index for vector similarity search (cosine distance)
    __table_args__ = (
        Index(
            "ix_event_embeddings_vector",
            "embedding",
            REDACTEDql_using="ivfflat",
            REDACTEDql_with={"lists": 100},
            REDACTEDql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
