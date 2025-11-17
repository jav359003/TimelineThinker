"""
Pydantic schemas for query endpoints.
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class QueryRequest(BaseModel):
    """Request body for query endpoint."""
    user_id: int = 1
    question: str
    source_id: Optional[int] = None


class ChunkInfo(BaseModel):
    """Information about a retrieved chunk."""
    text: str
    relevance_score: float
    date: Optional[str] = None  # Date as ISO string (YYYY-MM-DD)
    source_title: Optional[str] = None


class QueryResponse(BaseModel):
    """Response from query endpoint."""
    answer: str
    dates_used: List[str]  # Dates as ISO strings (YYYY-MM-DD)
    timeline_chunks: List[ChunkInfo]
    document_chunks: List[ChunkInfo]
    confidence: float
