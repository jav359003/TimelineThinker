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
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://jav359003.github.io",
    "https://jav359003.github.io/TimelineThinker",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight for 1 hour
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
    Health check endpoint for Cloud Run and monitoring.
    """
    return {"status": "healthy", "service": "Timeline Thinker API"}


@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    """
    Handle CORS preflight requests explicitly.
    This ensures OPTIONS requests return 200 OK in Cloud Run.
    """
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
