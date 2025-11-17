"""
Document ingestion pipeline.
"""
from datetime import datetime
from sqlalchemy.orm import Session
import json

from app.models.source import Source, SourceType
from app.services.document_service import get_document_service
from app.services.chunking_service import get_chunking_service
from app.pipeline.common import (
    create_events_from_chunks,
    extract_and_link_entities,
    extract_and_link_topics,
    update_timelines
)


async def process_document(
    db: Session,
    user_id: int,
    document_content: bytes,
    filename: str,
    title: str = None
) -> Source:
    """
    Complete document ingestion pipeline.

    Steps:
    1. Create Source record
    2. Extract text from document (PDF/Markdown)
    3. Chunk document text
    4. Create events with embeddings
    5. Extract entities and topics
    6. Update timelines

    Args:
        db: Database session
        user_id: User ID
        document_content: Binary document file content
        filename: Original filename
        title: Optional title (defaults to filename)

    Returns:
        Created Source object
    """
    # Step 1: Create source record
    source = Source(
        user_id=user_id,
        source_type=SourceType.DOCUMENT.value,
        title=title or filename,
        uri=filename,  # In production, this would be a storage path/URL
        file_size=len(document_content),
        mime_type="application/pdf"  # Determine from file extension
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    try:
        # Step 2: Extract text from document
        document_service = get_document_service()
        extracted_text, metadata = document_service.extract_text_from_file(
            document_content, filename
        )

        # Update source with metadata
        source.source_metadata = json.dumps(metadata)
        db.commit()

        # Step 3: Chunk document text
        chunking_service = get_chunking_service()
        text_chunks = chunking_service.chunk_text(extracted_text)

        # Step 4: Create events with embeddings
        events = await create_events_from_chunks(
            db=db,
            user_id=user_id,
            source=source,
            text_chunks=text_chunks,
            event_type="document",
            timestamp=datetime.utcnow()
        )

        # Step 5: Extract and link entities and topics (DISABLED for faster uploads)
        # TODO: Move to background task queue (Celery/Redis) for production
        # await extract_and_link_entities(db, events, extracted_text)
        # await extract_and_link_topics(db, events, extracted_text)

        # Step 6: Update timelines (DISABLED for faster uploads)
        # TODO: Move to background task queue for production
        # if events:
        #     await update_timelines(db, user_id, events[0].date)

        return source

    except Exception as e:
        db.rollback()
        raise e
