"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import init_db
from app.api import ingest, query, timeline, source, session

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Timeline Thinker API",
    description="AI-powered personal timeline and knowledge base with multi-modal ingestion and intelligent retrieval",
    version="1.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router, prefix=settings.api_v1_prefix)
app.include_router(query.router, prefix=settings.api_v1_prefix)
app.include_router(timeline.router, prefix=settings.api_v1_prefix)
app.include_router(source.router, prefix=settings.api_v1_prefix)
app.include_router(session.router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
async def startup_event():
    """
    Initialize database on startup.
    In production, use Alembic migrations instead.
    """
    init_db()


@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": "Timeline Thinker API",
        "version": "1.0.0",
        "description": "AI-powered personal knowledge base",
        "endpoints": {
            "ingestion": {
                "audio": f"{settings.api_v1_prefix}/ingest/audio",
                "document": f"{settings.api_v1_prefix}/ingest/document",
                "webpage": f"{settings.api_v1_prefix}/ingest/webpage"
            },
            "query": f"{settings.api_v1_prefix}/query",
            "timeline": {
                "daily": f"{settings.api_v1_prefix}/timeline/daily",
                "topics": f"{settings.api_v1_prefix}/timeline/topics"
            }
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
