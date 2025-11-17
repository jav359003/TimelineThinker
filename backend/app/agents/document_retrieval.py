"""
Document Retrieval Agent: Retrieves relevant document chunks.
"""
from typing import List, Set, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.agents.base import BaseAgent, PlannerOutput, TimelineChunk, DocumentChunk
from app.models.event import Event, EventEmbedding
from app.models.entity import Entity, EventEntity
from app.models.topic import Topic, EventTopic
from app.services.embedding_service import get_embedding_service


class DocumentRetrievalAgent(BaseAgent):
    """
    Document Retrieval Agent retrieves relevant document and webpage chunks
    based on semantic similarity and shared entities/topics.
    """

    def __init__(self):
        self.embedding_service = get_embedding_service()

    async def execute(
        self,
        db: Session,
        user_id: int,
        question: str,
        planner_output: PlannerOutput,
        timeline_chunks: List[TimelineChunk],
        top_k: int = 10,
        focus_source_id: Optional[int] = None
    ) -> List[DocumentChunk]:
        """
        Retrieve relevant document chunks.

        Args:
            db: Database session
            user_id: User ID
            question: User's question
            planner_output: Output from Planner Agent
            timeline_chunks: Timeline chunks from Timeline Retrieval Agent
            top_k: Number of chunks to retrieve

        Returns:
            List of DocumentChunk objects
        """
        # Get entity IDs from timeline chunks for refinement
        timeline_entity_ids = self._get_entity_ids_from_timeline(
            db, timeline_chunks
        )

        document_events = []
        if focus_source_id:
            document_events = self._get_events_for_source(
                db, user_id, focus_source_id
            )

            # If the focused source isn't a document/webpage, fall back to general retrieval
            if document_events and not any(
                evt.event_type in {"document", "webpage"} for evt in document_events
            ):
                document_events = []

        if not document_events:
            # Get all document/webpage events for this user
            document_events = db.query(Event).filter(
                and_(
                    Event.user_id == user_id,
                    or_(
                        Event.event_type == "document",
                        Event.event_type == "webpage"
                    )
                )
            ).all()

        if not document_events:
            return []

        # Perform semantic search
        document_chunks = await self._semantic_search(
            db, question, document_events, top_k * 2  # Get more candidates
        )

        # Refine by prioritizing chunks with shared entities
        if timeline_entity_ids:
            document_chunks = self._prioritize_by_entities(
                db, document_chunks, timeline_entity_ids
            )

        # Return top_k after refinement
        return document_chunks[:top_k]

    def _get_entity_ids_from_timeline(
        self,
        db: Session,
        timeline_chunks: List[TimelineChunk]
    ) -> Set[int]:
        """
        Extract entity IDs from timeline chunks.
        """
        if not timeline_chunks:
            return set()

        event_ids = [chunk.event_id for chunk in timeline_chunks]

        # Query entities linked to these events
        event_entities = db.query(EventEntity.entity_id).filter(
            EventEntity.event_id.in_(event_ids)
        ).distinct().all()

        entity_ids = {ee.entity_id for ee in event_entities}
        return entity_ids

    async def _semantic_search(
        self,
        db: Session,
        question: str,
        candidate_events: List[Event],
        top_k: int
    ) -> List[DocumentChunk]:
        """
        Perform semantic search over document events.
        """
        if not candidate_events:
            return []

        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(question)

        # Get event IDs
        event_ids = [event.id for event in candidate_events]

        # Query using pgvector
        from sqlalchemy import text

        query = text("""
            SELECT
                e.id,
                e.raw_text,
                e.event_type,
                s.title as source_title,
                1 - (emb.embedding <=> CAST(:query_embedding AS vector)) as similarity
            FROM events e
            JOIN event_embeddings emb ON e.id = emb.event_id
            JOIN sources s ON e.source_id = s.id
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

        document_chunks = []
        for row in result:
            chunk = DocumentChunk(
                event_id=row.id,
                text=row.raw_text,
                source_title=row.source_title,
                event_type=row.event_type,
                relevance_score=float(row.similarity)
            )
            document_chunks.append(chunk)

        return document_chunks

    def _prioritize_by_entities(
        self,
        db: Session,
        document_chunks: List[DocumentChunk],
        timeline_entity_ids: Set[int]
    ) -> List[DocumentChunk]:
        """
        Re-rank document chunks by prioritizing those with shared entities.
        """
        if not timeline_entity_ids:
            return document_chunks

        # Get entity counts for each document chunk
        chunk_entity_scores = {}

        for chunk in document_chunks:
            # Get entities for this event
            event_entities = db.query(EventEntity.entity_id).filter(
                EventEntity.event_id == chunk.event_id
            ).all()

            event_entity_ids = {ee.entity_id for ee in event_entities}

            # Count shared entities
            shared_count = len(event_entity_ids & timeline_entity_ids)

            # Boost score based on shared entities
            boosted_score = chunk.relevance_score + (shared_count * 0.1)
            chunk_entity_scores[chunk.event_id] = boosted_score

        # Re-sort chunks
        sorted_chunks = sorted(
            document_chunks,
            key=lambda c: chunk_entity_scores.get(c.event_id, c.relevance_score),
            reverse=True
        )

        return sorted_chunks

    def _get_events_for_source(
        self,
        db: Session,
        user_id: int,
        source_id: int
    ) -> List[Event]:
        """
        Fetch events for a specific source belonging to the user.
        """
        return db.query(Event).filter(
            and_(
                Event.user_id == user_id,
                Event.source_id == source_id
            )
        ).all()
