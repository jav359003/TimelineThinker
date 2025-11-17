"""
API routes for query endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional
import json

from app.database import get_db
from app.schemas.query import QueryRequest, QueryResponse, ChunkInfo
from app.agents.planner import PlannerAgent
from app.agents.timeline_retrieval import TimelineRetrievalAgent
from app.agents.document_retrieval import DocumentRetrievalAgent
from app.agents.alignment import AlignmentAgent
from app.agents.synthesizer import SynthesizerAgent
from app.models.source import Source, SourceType
from app.services.session_service import get_session_service

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Query Timeline Thinker with a natural language question.

    This endpoint runs the full agentic retrieval pipeline:
    1. Planner Agent: Analyzes the question and extracts temporal scope, topics, entities
    2. Timeline Retrieval Agent: Retrieves relevant timeline events based on temporal scope
    3. Document Retrieval Agent: Retrieves relevant document chunks
    4. Alignment Agent: Aligns timeline and document chunks, finds connections
    5. Synthesizer Agent: Generates the final answer with self-checking

    Example using curl:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/query" \\
      -H "Content-Type: application/json" \\
      -d '{"user_id": 1, "question": "What did I work on last week?"}'
    ```

    Example Response:
    ```json
    {
      "answer": "Last week you worked on...",
      "dates_used": ["2024-01-15", "2024-01-16"],
      "timeline_chunks": [...],
      "document_chunks": [...],
      "confidence": 0.85
    }
    ```
    """
    try:
        focus_source_id = _resolve_source_focus(
            db=db,
            user_id=request.user_id,
            requested_source_id=request.source_id,
            question=request.question
        )

        # Step 1: Planner Agent
        planner = PlannerAgent()
        planner_output = await planner.execute(
            question=request.question,
            current_date=date.today()
        )

        # Step 2: Timeline Retrieval Agent
        timeline_agent = TimelineRetrievalAgent()
        timeline_chunks = await timeline_agent.execute(
            db=db,
            user_id=request.user_id,
            question=request.question,
            planner_output=planner_output,
            top_k=10,
            focus_source_id=focus_source_id
        )

        # Step 3: Document Retrieval Agent
        document_agent = DocumentRetrievalAgent()
        document_chunks = await document_agent.execute(
            db=db,
            user_id=request.user_id,
            question=request.question,
            planner_output=planner_output,
            timeline_chunks=timeline_chunks,
            top_k=10,
            focus_source_id=focus_source_id
        )

        # Step 4: Alignment Agent
        alignment_agent = AlignmentAgent()
        alignment_output = await alignment_agent.execute(
            db=db,
            timeline_chunks=timeline_chunks,
            document_chunks=document_chunks,
            question=request.question
        )

        # Step 5: Synthesizer Agent
        synthesizer = SynthesizerAgent()
        result = await synthesizer.execute(
            question=request.question,
            planner_output=planner_output,
            timeline_chunks=timeline_chunks,
            document_chunks=document_chunks,
            alignment_output=alignment_output
        )

        # Convert to response format
        timeline_chunk_infos = [
            ChunkInfo(
                text=chunk.text[:200],  # Truncate for response
                relevance_score=chunk.relevance_score,
                date=chunk.date.isoformat() if chunk.date else None,  # Convert date to string
                source_title=None
            )
            for chunk in timeline_chunks[:5]
        ]

        document_chunk_infos = [
            ChunkInfo(
                text=chunk.text[:200],  # Truncate for response
                relevance_score=chunk.relevance_score,
                date=None,
                source_title=chunk.source_title
            )
            for chunk in document_chunks[:5]
        ]

        # Log interaction for session tracking
        session_service = get_session_service()
        session_service.log_interaction(
            db=db,
            user_id=request.user_id,
            question=request.question,
            answer=result.answer,
            source_id=focus_source_id,
        )

        return QueryResponse(
            answer=result.answer,
            dates_used=[],
            timeline_chunks=timeline_chunk_infos,
            document_chunks=document_chunk_infos,
            confidence=result.confidence
        )

    except Exception as e:
        import traceback
        print("=" * 80)
        print("QUERY ERROR:")
        traceback.print_exc()
        print("=" * 80)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post("/stream")
async def query_stream(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Query with streaming response (for real-time UI updates).

    This endpoint runs the same pipeline but streams the answer token-by-token.

    Example using JavaScript fetch:
    ```javascript
    const response = await fetch('/api/v1/query/stream', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({user_id: 1, question: "What did I learn today?"})
    });

    const reader = response.body.getReader();
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      const text = new TextDecoder().decode(value);
      console.log(text);
    }
    ```
    """
    async def generate():
        try:
            # Run the same pipeline as above
            focus_source_id = _resolve_source_focus(
                db=db,
                user_id=request.user_id,
                requested_source_id=request.source_id,
                question=request.question
            )

            planner = PlannerAgent()
            planner_output = await planner.execute(
                question=request.question,
                current_date=date.today()
            )

            timeline_agent = TimelineRetrievalAgent()
            timeline_chunks = await timeline_agent.execute(
                db=db,
                user_id=request.user_id,
                question=request.question,
                planner_output=planner_output,
                top_k=10,
                focus_source_id=focus_source_id
            )

            document_agent = DocumentRetrievalAgent()
            document_chunks = await document_agent.execute(
                db=db,
                user_id=request.user_id,
                question=request.question,
                planner_output=planner_output,
                timeline_chunks=timeline_chunks,
                top_k=10,
                focus_source_id=focus_source_id
            )

            alignment_agent = AlignmentAgent()
            alignment_output = await alignment_agent.execute(
                db=db,
                timeline_chunks=timeline_chunks,
                document_chunks=document_chunks,
                question=request.question
            )

            # For streaming, we'd need to modify the synthesizer to use streaming
            # For now, send the full response
            synthesizer = SynthesizerAgent()
            result = await synthesizer.execute(
                question=request.question,
                planner_output=planner_output,
                timeline_chunks=timeline_chunks,
                document_chunks=document_chunks,
                alignment_output=alignment_output
            )

            session_service = get_session_service()
            session_service.log_interaction(
                db=db,
                user_id=request.user_id,
                question=request.question,
                answer=result.answer,
                source_id=focus_source_id,
            )

            # Stream the answer word by word
            words = result.answer.split()
            for word in words:
                yield f"{word} "

        except Exception as e:
            yield f"Error: {str(e)}"

    return StreamingResponse(generate(), media_type="text/plain")


def _resolve_source_focus(
    db: Session,
    user_id: int,
    requested_source_id: Optional[int],
    question: str
) -> Optional[int]:
    """
    Determine which source (if any) the query should focus on.
    Preference order:
    1. Explicit source_id provided in the request
    2. Heuristic based on "this article" style phrasing
    """
    if requested_source_id is not None:
        source = db.query(Source).filter(
            Source.id == requested_source_id,
            Source.user_id == user_id
        ).first()

        if not source:
            raise HTTPException(
                status_code=404,
                detail="Source not found for this user"
            )

        return source.id

    text = question.lower()
    recency_tokens = [
        "this", "that", "these", "those", "recent", "latest",
        "just", "new", "uploaded", "ingested", "added"
    ]

    if not any(token in text for token in recency_tokens):
        return None

    type_priority: list[str] = []

    if any(word in text for word in ["article", "webpage", "website", "page", "link"]):
        type_priority.extend([
            SourceType.WEBPAGE.value,
            SourceType.DOCUMENT.value
        ])

    if any(word in text for word in ["document", "pdf", "paper", "file"]):
        type_priority.append(SourceType.DOCUMENT.value)

    if any(word in text for word in ["audio", "recording", "meeting", "transcript", "call", "podcast"]):
        type_priority.append(SourceType.AUDIO.value)

    if any(word in text for word in ["note", "text", "summary"]):
        type_priority.append(SourceType.TEXT.value)

    query = db.query(Source).filter(Source.user_id == user_id)
    if type_priority:
        query = query.filter(Source.source_type.in_(type_priority))

    source = query.order_by(Source.created_at.desc()).first()
    return source.id if source else None
