"""
Web content ingestion pipeline.
"""
from datetime import datetime
from sqlalchemy.orm import Session
import json

from app.models.source import Source, SourceType
from app.services.web_scraper import get_web_scraper_service
from app.services.chunking_service import get_chunking_service
from app.pipeline.common import (
    create_events_from_chunks,
    extract_and_link_entities,
    extract_and_link_topics,
    update_timelines
)


async def process_webpage(
    db: Session,
    user_id: int,
    url: str
) -> Source:
    """
    Complete webpage ingestion pipeline.

    Steps:
    1. Scrape webpage content
    2. Create Source record
    3. Chunk webpage text
    4. Create events with embeddings
    5. Extract entities and topics
    6. Update timelines

    Args:
        db: Database session
        user_id: User ID
        url: Web page URL to scrape

    Returns:
        Created Source object
    """
    # Step 1: Scrape webpage
    web_scraper = get_web_scraper_service()
    scraped_text, metadata = web_scraper.scrape_url(url)

    # Step 2: Create source record
    source = Source(
        user_id=user_id,
        source_type=SourceType.WEBPAGE.value,
        title=metadata.get("title", url),
        uri=url,
        source_metadata=json.dumps(metadata)
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    try:
        # Step 3: Chunk webpage text
        chunking_service = get_chunking_service()
        text_chunks = chunking_service.chunk_text(scraped_text)

        # Step 4: Create events with embeddings
        events = await create_events_from_chunks(
            db=db,
            user_id=user_id,
            source=source,
            text_chunks=text_chunks,
            event_type="webpage",
            timestamp=datetime.utcnow()
        )

        # Step 5: Extract and link entities and topics (DISABLED for faster uploads)
        # TODO: Move to background task queue (Celery/Redis) for production
        # await extract_and_link_entities(db, events, scraped_text)
        # await extract_and_link_topics(db, events, scraped_text)

        # Step 6: Update timelines (DISABLED for faster uploads)
        # TODO: Move to background task queue for production
        # if events:
        #     await update_timelines(db, user_id, events[0].date)

        return source

    except Exception as e:
        db.rollback()
        raise e
