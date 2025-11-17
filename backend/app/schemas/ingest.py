"""
Pydantic schemas for ingestion endpoints.
"""
from pydantic import BaseModel, HttpUrl
from typing import Optional


class AudioIngestResponse(BaseModel):
    """Response after audio ingestion."""
    source_id: int
    title: str
    status: str
    events_created: int
    message: str


class DocumentIngestResponse(BaseModel):
    """Response after document ingestion."""
    source_id: int
    title: str
    status: str
    events_created: int
    message: str


class WebpageIngestRequest(BaseModel):
    """Request body for webpage ingestion."""
    url: HttpUrl
    user_id: int = 1  # For simplicity, default to user 1


class WebpageIngestResponse(BaseModel):
    """Response after webpage ingestion."""
    source_id: int
    title: str
    url: str
    status: str
    events_created: int
    message: str
