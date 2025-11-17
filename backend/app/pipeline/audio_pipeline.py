"""
Audio ingestion pipeline.
"""
from datetime import datetime
from sqlalchemy.orm import Session
import json

from app.models.source import Source, SourceType
from app.services.transcription_service import get_transcription_service
from app.services.chunking_service import get_chunking_service
from app.pipeline.common import (
    create_events_from_chunks,
    extract_and_link_entities,
    extract_and_link_topics,
    update_timelines
)


async def process_audio(
    db: Session,
    user_id: int,
    audio_content: bytes,
    filename: str,
    title: str = None
) -> Source:
    """
    Complete audio ingestion pipeline.

    Steps:
    1. Create Source record
    2. Transcribe audio
    3. Chunk transcript
    4. Create events with embeddings
    5. Extract entities and topics
    6. Update timelines

    Args:
        db: Database session
        user_id: User ID
        audio_content: Binary audio file content
        filename: Original filename
        title: Optional title (defaults to filename)

    Returns:
        Created Source object
    """
    # Step 1: Create source record
    source = Source(
        user_id=user_id,
        source_type=SourceType.AUDIO.value,
        title=title or filename,
        uri=filename,  # In production, this would be a storage path/URL
        file_size=len(audio_content),
        mime_type="audio/mpeg"  # Determine from file
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    try:
        # Step 2: Transcribe audio
        transcription_service = get_transcription_service()
        transcript_text, metadata = await transcription_service.transcribe_audio(
            audio_content, filename
        )

        # Update source with metadata
        source.source_metadata = json.dumps(metadata)
        db.commit()

        # Step 3: Chunk transcript
        chunking_service = get_chunking_service()
        text_chunks = chunking_service.chunk_text(transcript_text)

        # Step 4: Create events with embeddings
        events = await create_events_from_chunks(
            db=db,
            user_id=user_id,
            source=source,
            text_chunks=text_chunks,
            event_type="audio",
            timestamp=datetime.utcnow()
        )

        # Step 5: Extract and link entities and topics (DISABLED for faster uploads)
        # TODO: Move to background task queue (Celery/Redis) for production
        # await extract_and_link_entities(db, events, transcript_text)
        # await extract_and_link_topics(db, events, transcript_text)

        # Step 6: Update timelines (DISABLED for faster uploads)
        # TODO: Move to background task queue for production
        # if events:
        #     await update_timelines(db, user_id, events[0].date)

        return source

    except Exception as e:
        # If processing fails, we could mark the source as failed
        # For now, re-raise the exception
        db.rollback()
        raise e
