# Timeline Thinker - AI-Powered Personal Knowledge Base

A full-stack AI system that ingests multi-modal data (audio, documents, web pages) and provides intelligent question-answering through a sophisticated multi-agent retrieval pipeline.

## Architecture Overview

### High-Level Flow

```
Ingestion: Audio/PDF/Web → Normalization → Events + Embeddings → Timelines
                                                    ↓
Query: Question → Planner → Timeline Retrieval → Document Retrieval → Alignment → Synthesizer → Answer
```

### Key Components

1. **Multi-Modal Ingestion Pipeline**: Processes audio (via Whisper), PDFs, Markdown, and web pages
2. **Event-Based Storage**: Normalizes all data into timestamped "memory events" with embeddings
3. **Timeline System**: Organizes events into daily/weekly summaries for efficient temporal retrieval
4. **Five-Agent Retrieval Pipeline**:
   - **Planner Agent**: Extracts temporal scope, topics, and entities from questions
   - **Timeline Retrieval Agent**: Temporal-first search within date ranges
   - **Document Retrieval Agent**: Semantic search over documents with entity-based refinement
   - **Alignment Agent**: Finds connections between timeline and document chunks
   - **Synthesizer Agent**: Generates final answer with self-checking

## Tech Stack

### Backend
- **Framework**: Python + FastAPI
- **Database**: PostgreSQL with pgvector extension
- **LLM**: OpenAI GPT-4 (or Anthropic Claude)
- **Embeddings**: OpenAI text-embedding-3-small
- **Transcription**: OpenAI Whisper API
- **ORM**: SQLAlchemy

### Frontend
- **Framework**: React + Vite
- **UI**: Custom components (Timeline Sidebar + Chat Interface)
- **API Client**: Axios

## Project Structure

```
second-brain/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic validation schemas
│   │   ├── api/             # FastAPI route handlers
│   │   ├── services/        # Business logic (LLM, embeddings, etc.)
│   │   ├── agents/          # Five-agent retrieval pipeline
│   │   ├── pipeline/        # Ingestion pipelines
│   │   ├── config.py        # Configuration
│   │   ├── database.py      # Database setup
│   │   └── main.py          # FastAPI app entry point
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/       # Chat interface components
│   │   │   └── Timeline/   # Timeline sidebar components
│   │   ├── services/       # API client
│   │   ├── App.jsx         # Main app component
│   │   └── main.jsx        # React entry point
│   └── package.json
│
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 14+ with pgvector extension
- OpenAI API key (or Anthropic API key)

### Backend Setup

1. **Install PostgreSQL and pgvector**:
```bash
# macOS with Homebrew
brew install REDACTEDql@14
brew install pgvector

# Start PostgreSQL
brew services start REDACTEDql@14

# Create database
createdb secondbrain
```

2. **Enable pgvector extension**:
```sql
psql secondbrain
CREATE EXTENSION vector;
\q
```

3. **Install Python dependencies**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

5. **Run the backend**:
```bash
python -m app.main
# Server runs on http://localhost:8000
```

### Frontend Setup

1. **Install dependencies**:
```bash
cd frontend
npm install
```

2. **Run the development server**:
```bash
npm run dev
# Frontend runs on http://localhost:3000
```

## API Documentation

### Ingestion Endpoints

#### 1. Ingest Audio

```bash
curl -X POST "http://localhost:8000/api/v1/ingest/audio" \
  -F "file=@meeting.mp3" \
  -F "user_id=1" \
  -F "title=Team Meeting Recording"
```

**Response**:
```json
{
  "source_id": 1,
  "title": "Team Meeting Recording",
  "status": "success",
  "events_created": 12,
  "message": "Audio file 'Team Meeting Recording' ingested successfully. Created 12 events."
}
```

#### 2. Ingest Document

```bash
curl -X POST "http://localhost:8000/api/v1/ingest/document" \
  -F "file=@report.pdf" \
  -F "user_id=1" \
  -F "title=Q4 Sales Report"
```

**Response**:
```json
{
  "source_id": 2,
  "title": "Q4 Sales Report",
  "status": "success",
  "events_created": 25,
  "message": "Document 'Q4 Sales Report' ingested successfully. Created 25 events."
}
```

#### 3. Ingest Webpage

```bash
curl -X POST "http://localhost:8000/api/v1/ingest/webpage" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article",
    "user_id": 1
  }'
```

**Response**:
```json
{
  "source_id": 3,
  "title": "How AI is Transforming Healthcare",
  "url": "https://example.com/article",
  "status": "success",
  "events_created": 8,
  "message": "Webpage 'How AI is Transforming Healthcare' ingested successfully. Created 8 events."
}
```

### Query Endpoint

#### Ask a Question

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "question": "What were the key points from the team meeting last Tuesday?"
  }'
```

**Response**:
```json
{
  "answer": "Based on the team meeting from January 9th, the key points discussed were: 1) The Q4 sales exceeded targets by 15%, 2) New product launch is scheduled for March, and 3) The team agreed to implement weekly standup meetings.",
  "dates_used": ["2024-01-09"],
  "timeline_chunks": [
    {
      "text": "Team discussed Q4 sales performance...",
      "relevance_score": 0.92,
      "date": "2024-01-09",
      "source_title": null
    }
  ],
  "document_chunks": [
    {
      "text": "Q4 Sales Report shows 15% growth...",
      "relevance_score": 0.87,
      "date": null,
      "source_title": "Q4 Sales Report"
    }
  ],
  "confidence": 0.85
}
```

### Timeline Endpoints

#### Get Daily Timeline

```bash
curl "http://localhost:8000/api/v1/timeline/daily?user_id=1&days=30"
```

**Response**:
```json
{
  "timelines": [
    {
      "date": "2024-01-15",
      "summary": "Worked on project planning and reviewed quarterly reports",
      "event_count": 5
    },
    {
      "date": "2024-01-14",
      "summary": "Team meeting and customer feedback analysis",
      "event_count": 3
    }
  ],
  "total_days": 15
}
```

#### Get Topics

```bash
curl "http://localhost:8000/api/v1/timeline/topics?user_id=1&limit=10"
```

**Response**:
```json
{
  "topics": [
    {
      "name": "Product Development",
      "event_count": 25,
      "description": null
    },
    {
      "name": "Sales Strategy",
      "event_count": 18,
      "description": null
    }
  ],
  "total_topics": 10
}
```

## Data Model

### Core Tables

1. **users**: User accounts
2. **sources**: Original files/URLs (audio, document, webpage)
3. **events**: Normalized memory events (chunks of text)
4. **event_embeddings**: Vector embeddings for semantic search
5. **entities**: Named entities (people, orgs, locations)
6. **topics**: Thematic topics
7. **event_entities**: Many-to-many relationship
8. **event_topics**: Many-to-many relationship
9. **daily_timeline**: Daily summaries
10. **weekly_timeline**: Weekly summaries

### Data Flow

```
Source (File/URL)
  ↓ [Extract Text]
Text
  ↓ [Chunk]
Chunks
  ↓ [Embed + Store]
Events + EventEmbeddings
  ↓ [Extract]
Entities + Topics
  ↓ [Generate]
Daily/Weekly Timelines
```

## Retrieval Strategy: Temporal-First, Then Semantic

The system uses a unique **temporal-first** approach:

1. **Planner Agent** extracts temporal scope from question
   - "last Tuesday" → specific date
   - "this week" → date range
   - No temporal reference → fall back to recent 30 days

2. **Timeline Retrieval Agent** narrows search to temporal scope
   - Filters events by date/date range
   - Runs semantic search within that subset
   - Returns top-k most relevant chunks

3. **Document Retrieval Agent** performs semantic search over documents
   - Prioritizes chunks sharing entities with timeline chunks
   - Returns top-k document chunks

4. **Alignment Agent** finds connections
   - Computes similarity between timeline and document chunks
   - Identifies related pairs
   - Creates unified context

5. **Synthesizer Agent** generates answer
   - Combines all context
   - Self-checks for completeness
   - Regenerates if needed

## Design Decisions & Trade-offs

### 1. Temporal-First Retrieval

**Choice**: Narrow by date before semantic search

**Rationale**:
- Humans naturally think in temporal terms
- Dramatically reduces search space for better accuracy
- Most questions have implicit temporal scope

**Trade-off**: May miss relevant older information if temporal scope is too narrow

### 2. Event-Based Normalization

**Choice**: All modalities → events (same schema)

**Rationale**:
- Unified interface for retrieval
- Consistent embedding strategy
- Easy to extend to new modalities

**Trade-off**: Loses some modality-specific metadata

### 3. PostgreSQL + pgvector

**Choice**: Single database for relational + vector data

**Rationale**:
- Avoids data synchronization issues
- Transactional consistency
- Simple deployment

**Trade-off**: Specialized vector databases (Pinecone, Weaviate) may offer better performance at scale

### 4. Multi-Agent Pipeline

**Choice**: Five specialized agents vs. single monolithic retrieval

**Rationale**:
- Modularity and testability
- Each agent has clear responsibility
- Easy to improve individual components

**Trade-off**: More complex orchestration and latency

## Scalability Considerations

### For Thousands of Documents (Single User)

**Current Design**:
- PostgreSQL can handle 100K+ events per user
- pgvector IVFFlat index for fast similarity search
- Temporal filtering reduces search space

**Optimizations**:
1. Add caching layer (Redis) for frequent queries
2. Pre-compute daily summaries asynchronously
3. Implement query result caching

### For Multiple Users

**Current Design**:
- All queries filtered by `user_id`
- Row-level isolation

**Optimizations**:
1. Partition tables by `user_id`
2. Separate databases per user (if very large)
3. Add background workers for ingestion

## Privacy & Security

### Current Approach

- All data scoped to `user_id`
- No cross-user data leakage
- API keys stored in environment variables

### For Production

1. **Authentication**: Add JWT-based auth
2. **Encryption**: Encrypt embeddings and sensitive text at rest
3. **Local-First Option**:
   - Run PostgreSQL locally
   - Use local LLM (Ollama, llama.cpp)
   - Keep all data on device

**Trade-off**: Local-first sacrifices cloud LLM quality for privacy

## Future Enhancements

1. **Real-time Streaming**: Stream LLM responses token-by-token
2. **Multi-modal Retrieval**: Support images, videos
3. **Hybrid Search**: Combine dense (embeddings) + sparse (BM25) retrieval
4. **Graph Memory**: Build knowledge graph for complex reasoning
5. **Active Learning**: Let users correct/refine answers
6. **Mobile App**: iOS/Android clients

## Testing the System

### 1. Start Backend
```bash
cd backend
source venv/bin/activate
python -m app.main
```

### 2. Start Frontend
```bash
cd frontend
npm run dev
```

### 3. Ingest Sample Data

```bash
# Upload a document
curl -X POST "http://localhost:8000/api/v1/ingest/document" \
  -F "file=@sample.pdf" \
  -F "user_id=1"

# Upload a webpage
curl -X POST "http://localhost:8000/api/v1/ingest/webpage" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://en.wikipedia.org/wiki/Artificial_intelligence", "user_id": 1}'
```

### 4. Ask Questions

Open http://localhost:3000 and ask:
- "What did I work on today?"
- "Summarize the main points from the article I saved"
- "What were the key topics discussed last week?"

## License

MIT

## Author

Built as a take-home assignment showcasing full-stack AI systems design.
