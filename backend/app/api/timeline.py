"""
API routes for timeline endpoints.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional
from datetime import date, timedelta
import io
from textwrap import wrap
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.database import get_db
from app.schemas.timeline import (
    DailyTimelineResponse,
    DailyTimelineItem,
    TopicsResponse,
    TopicItem,
    TimelineDayDetailResponse,
    TimelineEventDetail,
    TimelineInteractionDetail,
)
from app.models.timeline import DailyTimeline
from app.models.topic import Topic, EventTopic
from app.models.event import Event
from app.models.source import Source
from app.models.session import SessionInteraction

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("/daily", response_model=DailyTimelineResponse)
async def get_daily_timeline(
    user_id: int = Query(1),
    days: int = Query(30, description="Number of days to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Get daily timeline summaries for a user.

    Returns a list of daily timeline entries with summaries and event counts.
    Useful for displaying a timeline sidebar in the UI.

    Example using curl:
    ```bash
    curl "http://localhost:8000/api/v1/timeline/daily?user_id=1&days=30"
    ```

    Example Response:
    ```json
    {
      "timelines": [
        {
          "date": "2024-01-15",
          "summary": "Worked on project planning and reviewed documentation",
          "event_count": 5
        },
        ...
      ],
      "total_days": 15
    }
    ```
    """
    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Query daily timelines
    timelines = db.query(DailyTimeline).filter(
        and_(
            DailyTimeline.user_id == user_id,
            DailyTimeline.date >= start_date,
            DailyTimeline.date <= end_date
        )
    ).order_by(DailyTimeline.date.desc()).all()

    # Convert to response format
    timeline_items = [
        DailyTimelineItem(
            date=timeline.date,
            summary=timeline.summary_text,
            event_count=timeline.event_count
        )
        for timeline in timelines
    ]

    return DailyTimelineResponse(
        timelines=timeline_items,
        total_days=len(timeline_items)
    )


@router.get("/topics", response_model=TopicsResponse)
async def get_topics(
    user_id: int = Query(1),
    limit: int = Query(20, description="Maximum number of topics to return"),
    db: Session = Depends(get_db)
):
    """
    Get topics with event counts for a user.

    Returns a list of topics ordered by frequency (number of associated events).

    Example using curl:
    ```bash
    curl "http://localhost:8000/api/v1/timeline/topics?user_id=1&limit=20"
    ```

    Example Response:
    ```json
    {
      "topics": [
        {
          "name": "Machine Learning",
          "event_count": 15,
          "description": null
        },
        ...
      ],
      "total_topics": 12
    }
    ```
    """
    # Query topics with event counts
    # Join topics with event_topics and events to count events per topic for this user
    topic_counts = db.query(
        Topic.name,
        Topic.description,
        func.count(Event.id).label('event_count')
    ).join(
        EventTopic, EventTopic.topic_id == Topic.id
    ).join(
        Event, Event.id == EventTopic.event_id
    ).filter(
        Event.user_id == user_id
    ).group_by(
        Topic.id, Topic.name, Topic.description
    ).order_by(
        func.count(Event.id).desc()
    ).limit(limit).all()

    # Convert to response format
    topic_items = [
        TopicItem(
            name=row.name,
            event_count=row.event_count,
            description=row.description
        )
        for row in topic_counts
    ]

    return TopicsResponse(
        topics=topic_items,
        total_topics=len(topic_items)
    )


def _fetch_day_detail(
    db: Session,
    user_id: int,
    target_date: date,
    event_limit: int
) -> TimelineDayDetailResponse:
    daily_entry = db.query(DailyTimeline).filter(
        DailyTimeline.user_id == user_id,
        DailyTimeline.date == target_date
    ).first()

    event_rows = db.query(Event, Source).join(
        Source, Event.source_id == Source.id
    ).filter(
        Event.user_id == user_id,
        Event.date == target_date
    ).order_by(Event.chunk_index.asc()).limit(event_limit).all()

    events = [
        TimelineEventDetail(
            id=event.id,
            text=event.raw_text,
            source_title=source.title if source else None,
            event_type=event.event_type
        )
        for event, source in event_rows
    ]

    interaction_rows = db.query(
        SessionInteraction, Source
    ).outerjoin(
        Source, SessionInteraction.source_id == Source.id
    ).filter(
        SessionInteraction.user_id == user_id,
        SessionInteraction.session_date == target_date
    ).order_by(SessionInteraction.created_at.asc()).all()

    interactions = [
        TimelineInteractionDetail(
            id=interaction.id,
            question=interaction.question,
            answer=interaction.answer,
            created_at=interaction.created_at,
            source_title=source.title if source else None
        )
        for interaction, source in interaction_rows
    ]

    return TimelineDayDetailResponse(
        date=target_date,
        summary=daily_entry.summary_text if daily_entry else None,
        events=events,
        interactions=interactions
    )


@router.get("/day-detail", response_model=TimelineDayDetailResponse)
async def get_day_detail(
    user_id: int = Query(1),
    target_date: date = Query(..., description="Date to inspect (YYYY-MM-DD)"),
    event_limit: int = Query(20, le=100, ge=1),
    db: Session = Depends(get_db)
):
    """Return detailed information for a single timeline day."""
    return _fetch_day_detail(db, user_id, target_date, event_limit)


@router.get("/day-notes")
async def export_day_notes(
    user_id: int = Query(1),
    target_date: date = Query(..., description="Date to export (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Export daily notes as a PDF."""
    detail = _fetch_day_detail(db, user_id, target_date, event_limit=100)

    if not detail.events and not detail.interactions:
        raise HTTPException(status_code=404, detail="No notes available for this date.")

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin = 40
    y = height - margin

    def draw_block(text: str, bold: bool = False, size: int = 11, leading: int = 14):
        nonlocal y
        font_name = "Helvetica-Bold" if bold else "Helvetica"
        pdf.setFont(font_name, size)
        for line in wrap(text, 95) or [""]:
            if y <= margin:
                pdf.showPage()
                y = height - margin
                pdf.setFont(font_name, size)
            pdf.drawString(margin, y, line)
            y -= leading
        y -= 4

    draw_block(f"Timeline Notes - {detail.date.isoformat()}", bold=True, size=14, leading=18)
    if detail.summary:
        draw_block(f"Summary: {detail.summary}", size=12)

    if detail.events:
        draw_block("Sources & Events", bold=True)
        for event in detail.events:
            title = event.source_title or "Untitled Source"
            draw_block(f"- {title} ({event.event_type})", bold=True)
            draw_block(event.text[:600] + ("..." if len(event.text) > 600 else ""))

    if detail.interactions:
        draw_block("Conversations", bold=True)
        for interaction in detail.interactions:
            draw_block(f"Q: {interaction.question}", bold=True)
            draw_block(f"A: {interaction.answer}")

    pdf.save()
    buffer.seek(0)
    headers = {
        "Content-Disposition": f"attachment; filename=timeline_{detail.date.isoformat()}.pdf"
    }
    return StreamingResponse(buffer, media_type="application/pdf", headers=headers)
