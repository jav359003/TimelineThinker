"""
Session API endpoints for managing daily sessions.
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.session import SessionSnapshotResponse
from app.services.session_service import get_session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/current", response_model=SessionSnapshotResponse)
async def get_current_session(
    user_id: int,
    session_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Return the session snapshot for the specified day (defaults to today).
    """
    service = get_session_service()
    date_value = session_date or date.today()
    snapshot = service.get_session_snapshot(db, user_id, date_value)

    summary = None
    if snapshot["interactions"]:
        summary = await service.summarize_interactions(snapshot["interactions"][::-1])

    return SessionSnapshotResponse(
        date=snapshot["date"],
        sources=snapshot["sources"],
        interactions=snapshot["interactions"],
        summary=summary,
    )


@router.delete("/current/source/{source_id}")
def remove_source_from_session(
    source_id: int,
    user_id: int,
    session_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Remove a source from today's session.
    """
    service = get_session_service()
    date_value = session_date or date.today()
    service.remove_session_source(db, user_id, source_id, date_value)
    return {"status": "removed"}


@router.delete("/current")
def clear_session(
    user_id: int,
    session_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Clear all sources and interactions for today's session.
    """
    service = get_session_service()
    date_value = session_date or date.today()
    service.clear_session(db, user_id, date_value)
    return {"status": "cleared"}
