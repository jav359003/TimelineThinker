"""
Pydantic schemas for session-related endpoints.
"""
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class SessionSourceInfo(BaseModel):
    id: int
    source_id: int
    title: str
    source_type: str
    uri: Optional[str]
    added_at: datetime


class SessionInteractionInfo(BaseModel):
    id: int
    question: str
    answer: str
    source_id: Optional[int]
    created_at: datetime


class SessionSnapshotResponse(BaseModel):
    date: date
    sources: List[SessionSourceInfo]
    interactions: List[SessionInteractionInfo]
    summary: Optional[str]
