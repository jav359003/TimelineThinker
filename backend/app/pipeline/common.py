"""
Common utilities shared across ingestion pipelines.
"""
from typing import List, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session

from app.models.source import Source, SourceType
from app.models.event import Event, EventEmbedding
from app.models.entity import Entity, EventEntity
from app.models.topic import Topic, EventTopic
from app.services.chunking_service import get_chunking_service
from app.services.embedding_service import get_embedding_service
from app.services.entity_extraction import get_entity_extraction_service
from app.services.timeline_service import get_timeline_service


async def create_events_from_chunks(
    db: Session,
    user_id: int,
    source: Source,
    text_chunks: List[Tuple[str, int]],
    event_type: str,
    timestamp: datetime = None
) -> List[Event]:
    """
    Create Event objects from text chunks with embeddings.

    Args:
        db: Database session
        user_id: User ID
        source: Source object
        text_chunks: List of (chunk_text, chunk_index) tuples
        event_type: Type of event (audio, document, webpage, text)
        timestamp: Optional timestamp (defaults to now)

    Returns:
        List of created Event objects
    """
    if timestamp is None:
        timestamp = datetime.utcnow()

    embedding_service = get_embedding_service()
    events = []

    # Generate embeddings in batch
    chunk_texts = [chunk[0] for chunk in text_chunks]
    embeddings = await embedding_service.generate_embeddings_batch(chunk_texts)

    # Create events and embeddings
    for (chunk_text, chunk_index), embedding in zip(text_chunks, embeddings):
        # Create event
        event = Event(
            user_id=user_id,
            source_id=source.id,
            event_type=event_type,
            raw_text=chunk_text,
            chunk_index=chunk_index,
            timestamp=timestamp,
            date=timestamp.date()
        )
        db.add(event)
        db.flush()  # Get the event ID

        # Create embedding
        event_embedding = EventEmbedding(
            event_id=event.id,
            embedding=embedding
        )
        db.add(event_embedding)

        events.append(event)

    db.commit()
    return events


async def extract_and_link_entities(
    db: Session,
    events: List[Event],
    full_text: str
) -> None:
    """
    Extract entities from text and link them to events.

    Args:
        db: Database session
        events: List of Event objects to link entities to
        full_text: Full text to extract entities from
    """
    entity_service = get_entity_extraction_service()

    # Extract entities from full text
    entities_data, _ = await entity_service.extract_entities_and_topics(full_text)

    if not entities_data:
        return

    # Process each entity
    for entity_data in entities_data:
        entity_name = entity_data.get("name", "").strip()
        entity_type = entity_data.get("type", "OTHER")
        confidence = entity_data.get("confidence", 80)

        if not entity_name:
            continue

        # Get or create entity
        entity = db.query(Entity).filter(Entity.name == entity_name).first()
        if not entity:
            entity = Entity(name=entity_name, entity_type=entity_type)
            db.add(entity)
            db.flush()

        # Link entity to all events from this source
        for event in events:
            # Check if link already exists
            existing_link = db.query(EventEntity).filter(
                EventEntity.event_id == event.id,
                EventEntity.entity_id == entity.id
            ).first()

            if not existing_link:
                event_entity = EventEntity(
                    event_id=event.id,
                    entity_id=entity.id,
                    confidence=confidence
                )
                db.add(event_entity)

    db.commit()


async def extract_and_link_topics(
    db: Session,
    events: List[Event],
    full_text: str
) -> None:
    """
    Extract topics from text and link them to events.

    Args:
        db: Database session
        events: List of Event objects to link topics to
        full_text: Full text to extract topics from
    """
    entity_service = get_entity_extraction_service()

    # Extract topics from full text
    _, topics_data = await entity_service.extract_entities_and_topics(full_text)

    if not topics_data:
        return

    # Process each topic
    for topic_name in topics_data:
        topic_name = topic_name.strip()
        if not topic_name:
            continue

        # Get or create topic
        topic = db.query(Topic).filter(Topic.name == topic_name).first()
        if not topic:
            topic = Topic(name=topic_name)
            db.add(topic)
            db.flush()

        # Link topic to all events from this source
        for event in events:
            # Check if link already exists
            existing_link = db.query(EventTopic).filter(
                EventTopic.event_id == event.id,
                EventTopic.topic_id == topic.id
            ).first()

            if not existing_link:
                event_topic = EventTopic(
                    event_id=event.id,
                    topic_id=topic.id,
                    relevance=85  # Default relevance score
                )
                db.add(event_topic)

    db.commit()


async def update_timelines(
    db: Session,
    user_id: int,
    event_date: date
) -> None:
    """
    Update daily and weekly timelines after adding events.

    Args:
        db: Database session
        user_id: User ID
        event_date: Date of the events
    """
    timeline_service = get_timeline_service()
    await timeline_service.update_timelines_for_date(db, user_id, event_date)
