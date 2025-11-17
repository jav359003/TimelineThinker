"""
API routes for working with sources.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.source import Source
from app.schemas.source import SourceListResponse, SourceInfo

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=SourceListResponse)
def list_sources(
    user_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Return recent sources uploaded by the user.
    """
    if limit <= 0:
        raise HTTPException(status_code=400, detail="limit must be positive")

    sources = (
        db.query(Source)
        .filter(Source.user_id == user_id)
        .order_by(Source.created_at.desc())
        .limit(limit)
        .all()
    )

    source_infos = [
        SourceInfo(
            id=source.id,
            title=source.title,
            source_type=source.source_type,
            uri=source.uri,
            created_at=source.created_at,
        )
        for source in sources
    ]

    return SourceListResponse(sources=source_infos)


@router.delete("/{source_id}")
def delete_source(
    source_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Permanently delete a source and all associated events for the user.
    """
    source = (
        db.query(Source)
        .filter(Source.id == source_id, Source.user_id == user_id)
        .first()
    )

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    db.delete(source)
    db.commit()

    return {"status": "deleted", "source_id": source_id}
