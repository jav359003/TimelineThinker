"""
Pydantic schemas for source metadata.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class SourceInfo(BaseModel):
    """Minimal information about an ingested source."""

    id: int
    title: str
    source_type: str
    uri: Optional[str] = None
    created_at: datetime


class SourceListResponse(BaseModel):
    """Response schema for listing sources."""

    sources: List[SourceInfo]
