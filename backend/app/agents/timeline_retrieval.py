"""
Timeline Retrieval Agent: Retrieves relevant timeline events based on temporal scope.
"""
from typing import List, Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.agents.base import BaseAgent, PlannerOutput, TimelineChunk
from app.models.event import Event, EventEmbedding
from app.services.embedding_service import get_embedding_service
from app.config import get_settings

settings = get_settings()


class TimelineRetrievalAgent(BaseAgent):
    """
    Timeline Retrieval Agent uses temporal scope to narrow down events,
    then performs semantic search within that subset.
    """

    def __init__(self):
        self.embedding_service = get_embedding_service()

    async def execute(
        self,
        db: Session,
        user_id: int,
        question: str,
        planner_output: PlannerOutput,
        top_k: int = 10,
        focus_source_id: Optional[int] = None
    ) -> List[TimelineChunk]:
        """
        Retrieve relevant timeline events.

        Args:
            db: Database session
            user_id: User ID
            question: User's question
            planner_output: Output from Planner Agent
            top_k: Number of chunks to retrieve

        Returns:
            List of TimelineChunk objects
        """
        temporal_scope = planner_output.temporal_scope

        candidate_events: List[Event] = []

        # Step 0: If the question references a specific source (e.g., "this article"),
        # focus on that source's events before falling back to temporal filters.
        if focus_source_id:
            candidate_events = self._get_events_for_source(
                db, user_id, focus_source_id
            )

        # Step 1: Filter by temporal scope when no explicit source was requested
        if not candidate_events:
            if temporal_scope:
                candidate_events = self._filter_by_temporal_scope(
                    db, user_id, temporal_scope
                )
            else:
                # Fall back to recent events (last 30 days)
                candidate_events = self._get_recent_events(
                    db, user_id, days=settings.default_lookback_days
                )

        if not candidate_events:
            return []

        # Step 2: Perform semantic search within filtered events
        timeline_chunks = await self._semantic_search(
            db, question, candidate_events, top_k
        )

        return timeline_chunks

    def _filter_by_temporal_scope(
        self,
        db: Session,
        user_id: int,
        temporal_scope: dict
    ) -> List[Event]:
        """
        Filter events based on temporal scope.
        """
        if temporal_scope["type"] == "date":
            # Specific date
            target_date = temporal_scope["date"]
            events = db.query(Event).filter(
                and_(
                    Event.user_id == user_id,
                    Event.date == target_date
                )
            ).all()

        elif temporal_scope["type"] == "range":
            # Date range
            start_date = temporal_scope["start_date"]
            end_date = temporal_scope["end_date"]
            events = db.query(Event).filter(
                and_(
                    Event.user_id == user_id,
                    Event.date >= start_date,
                    Event.date <= end_date
                )
            ).all()

        else:
            events = []

        return events

    def _get_events_for_source(
        self,
        db: Session,
        user_id: int,
        source_id: int
    ) -> List[Event]:
        """
        Fetch all events for a specific source.
        """
        events = db.query(Event).filter(
            and_(
                Event.user_id == user_id,
                Event.source_id == source_id
            )
        ).order_by(Event.chunk_index.asc()).all()

        return events

    def _get_recent_events(
        self,
        db: Session,
        user_id: int,
        days: int
    ) -> List[Event]:
        """
        Get events from the last N days.
        """
        cutoff_date = date.today() - timedelta(days=days)

        events = db.query(Event).filter(
            and_(
                Event.user_id == user_id,
                Event.date >= cutoff_date
            )
        ).all()

        return events

    async def _semantic_search(
        self,
        db: Session,
        question: str,
        candidate_events: List[Event],
        top_k: int
    ) -> List[TimelineChunk]:
        """
        Perform semantic search over candidate events.
        """
        if not candidate_events:
            return []

        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(question)

        # Get embeddings for candidate events
        event_ids = [event.id for event in candidate_events]

        # Query using pgvector cosine similarity
        # We'll use raw SQL for efficient vector search
        from sqlalchemy import text

        query = text("""
            SELECT
                e.id,
                e.raw_text,
                e.date,
                e.event_type,
                1 - (emb.embedding <=> CAST(:query_embedding AS vector)) as similarity
            FROM events e
            JOIN event_embeddings emb ON e.id = emb.event_id
            WHERE e.id = ANY(:event_ids)
            ORDER BY similarity DESC
            LIMIT :top_k
        """)

        result = db.execute(
            query,
            {
                "query_embedding": query_embedding,
                "event_ids": event_ids,
                "top_k": top_k
            }
        )

        timeline_chunks = []
        for row in result:
            chunk = TimelineChunk(
                event_id=row.id,
                text=row.raw_text,
                date=row.date,
                event_type=row.event_type,
                relevance_score=float(row.similarity)
            )
            timeline_chunks.append(chunk)

        return timeline_chunks
