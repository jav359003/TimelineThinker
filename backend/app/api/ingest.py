"""
API routes for ingestion endpoints.
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.ingest import (
    AudioIngestResponse,
    DocumentIngestResponse,
    WebpageIngestRequest,
    WebpageIngestResponse
)
from app.pipeline.audio_pipeline import process_audio
from app.pipeline.document_pipeline import process_document
from app.pipeline.web_pipeline import process_webpage
from app.models.event import Event

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/audio", response_model=AudioIngestResponse)
async def ingest_audio(
    file: UploadFile = File(...),
    user_id: int = Form(1),
    title: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Ingest an audio file.

    This endpoint:
    1. Accepts an audio file upload
    2. Transcribes the audio using Whisper API
    3. Chunks the transcript
    4. Creates events with embeddings
    5. Extracts entities and topics
    6. Updates timelines

    Example using curl:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/ingest/audio" \\
      -F "file=@meeting.mp3" \\
      -F "user_id=1" \\
      -F "title=Team Meeting Recording"
    ```
    """
    try:
        # Read file content
        audio_content = await file.read()

        # Process audio through pipeline
        source = await process_audio(
            db=db,
            user_id=user_id,
            audio_content=audio_content,
            filename=file.filename,
            title=title
        )

        # Count events created
        event_count = db.query(Event).filter(Event.source_id == source.id).count()

        return AudioIngestResponse(
            source_id=source.id,
            title=source.title,
            status="success",
            events_created=event_count,
            message=f"Audio file '{source.title}' ingested successfully. Created {event_count} events."
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest audio: {str(e)}")


@router.post("/document", response_model=DocumentIngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    user_id: int = Form(1),
    title: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Ingest a document file (PDF or Markdown).

    This endpoint:
    1. Accepts a document file upload
    2. Extracts text from the document
    3. Chunks the document
    4. Creates events with embeddings
    5. Extracts entities and topics
    6. Updates timelines

    Example using curl:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/ingest/document" \\
      -F "file=@report.pdf" \\
      -F "user_id=1" \\
      -F "title=Q4 Report"
    ```
    """
    try:
        # Read file content
        document_content = await file.read()

        # Process document through pipeline
        source = await process_document(
            db=db,
            user_id=user_id,
            document_content=document_content,
            filename=file.filename,
            title=title
        )

        # Count events created
        event_count = db.query(Event).filter(Event.source_id == source.id).count()

        return DocumentIngestResponse(
            source_id=source.id,
            title=source.title,
            status="success",
            events_created=event_count,
            message=f"Document '{source.title}' ingested successfully. Created {event_count} events."
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to ingest document: {str(e)}")


@router.post("/webpage", response_model=WebpageIngestResponse)
async def ingest_webpage(
    request: WebpageIngestRequest,
    db: Session = Depends(get_db)
):
    """
    Ingest a webpage by URL.

    This endpoint:
    1. Accepts a URL
    2. Scrapes the webpage content
    3. Chunks the text
    4. Creates events with embeddings
    5. Extracts entities and topics
    6. Updates timelines

    Example using curl:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/ingest/webpage" \\
      -H "Content-Type: application/json" \\
      -d '{"url": "https://example.com/article", "user_id": 1}'
    ```
    """
    try:
        # Process webpage through pipeline
        source = await process_webpage(
            db=db,
            user_id=request.user_id,
            url=str(request.url)
        )

        # Count events created
        event_count = db.query(Event).filter(Event.source_id == source.id).count()

        return WebpageIngestResponse(
            source_id=source.id,
            title=source.title,
            url=str(request.url),
            status="success",
            events_created=event_count,
            message=f"Webpage '{source.title}' ingested successfully. Created {event_count} events."
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest webpage: {str(e)}")
