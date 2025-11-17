"""
Source model representing the origin of ingested data.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class SourceType(str, enum.Enum):
    """Enumeration of supported source types."""
    AUDIO = "audio"
    DOCUMENT = "document"
    WEBPAGE = "webpage"
    TEXT = "text"


class Source(Base):
    """
    Source table tracking the original files or URLs that were ingested.

    Each source represents a single ingestion operation (one file, one URL, etc.)
    and can generate multiple events after chunking.
    """
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    source_type = Column(String, nullable=False, index=True)

    # For files: original filename; for web: URL; for text: title or first N chars
    title = Column(String, nullable=False)

    # File path (if stored locally) or URL
    uri = Column(Text, nullable=True)

    # Original file size in bytes (if applicable)
    file_size = Column(Integer, nullable=True)

    # MIME type for files
    mime_type = Column(String, nullable=True)

    # JSON metadata (e.g., audio duration, document page count, etc.)
    source_metadata = Column(Text, nullable=True)  # Store as JSON string

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="sources")
    events = relationship("Event", back_populates="source", cascade="all, delete-orphan")
