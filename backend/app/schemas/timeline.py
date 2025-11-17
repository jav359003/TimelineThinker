"""
Pydantic schemas for timeline endpoints.
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime


class DailyTimelineItem(BaseModel):
    """Daily timeline item."""
    date: date
    summary: Optional[str]
    event_count: int

    class Config:
        from_attributes = True


class TopicItem(BaseModel):
    """Topic item with count."""
    name: str
    event_count: int
    description: Optional[str] = None


class DailyTimelineResponse(BaseModel):
    """Response for daily timeline."""
    timelines: List[DailyTimelineItem]
    total_days: int


class TopicsResponse(BaseModel):
    """Response for topics."""
    topics: List[TopicItem]
    total_topics: int


class TimelineEventDetail(BaseModel):
    """Detailed event information for a day."""
    id: int
    text: str
    source_title: Optional[str]
    event_type: str


class TimelineInteractionDetail(BaseModel):
    """Session interaction that occurred on a given day."""
    id: int
    question: str
    answer: str
    created_at: datetime
    source_title: Optional[str] = None


class TimelineDayDetailResponse(BaseModel):
    """Detailed breakdown for a specific timeline date."""
    date: date
    summary: Optional[str]
    events: List[TimelineEventDetail]
    interactions: List[TimelineInteractionDetail]
