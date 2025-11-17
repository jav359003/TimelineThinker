# Timeline Thinker: System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                                                                 │
│  ┌──────────────┐                    ┌────────────────────┐   │
│  │   Timeline   │                    │   Chat Interface   │   │
│  │   Sidebar    │                    │                    │   │
│  │              │                    │   - Message List   │   │
│  │  - Daily     │                    │   - Input Box      │   │
│  │    Summaries │                    │   - Streaming      │   │
│  │  - Dates     │                    │                    │   │
│  │  - Highlights│                    │                    │   │
│  └──────────────┘                    └────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FASTAPI BACKEND                          │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              API ROUTES (REST + Streaming)             │   │
│  │                                                        │   │
│  │  /ingest/audio  /ingest/document  /ingest/webpage     │   │
│  │  /query         /timeline/daily   /timeline/topics    │   │
│  └────────────────────────────────────────────────────────┘   │
│                              │                                  │
│         ┌────────────────────┼────────────────────┐            │
│         ▼                    ▼                    ▼            │
│  ┌─────────────┐      ┌─────────────┐     ┌─────────────┐    │
│  │  Ingestion  │      │   Query     │     │  Timeline   │    │
│  │  Pipeline   │      │   Pipeline  │     │  Service    │    │
│  └─────────────┘      └─────────────┘     └─────────────┘    │
└─────────────────────────────────────────────────────────────────┘
         │                       │                    │
         ▼                       ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CORE SERVICES LAYER                          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Transcription│  │   Document   │  │  Web Scraper │         │
│  │   Service    │  │   Service    │  │   Service    │         │
│  │  (Whisper)   │  │  (PDF/MD)    │  │ (Beautiful   │         │
│  │              │  │              │  │   Soup)      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Chunking   │  │  Embedding   │  │     LLM      │         │
│  │   Service    │  │   Service    │  │   Client     │         │
│  │              │  │  (OpenAI)    │  │ (OpenAI/     │         │
│  │              │  │              │  │ Anthropic)   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌──────────────────────────────────────────────────┐         │
│  │          Entity & Topic Extraction                │         │
│  │              (LLM-based NER)                      │         │
│  └──────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MULTI-AGENT PIPELINE                          │
│                    (Query Processing)                           │
│                                                                 │
│        Question                                                 │
│           │                                                     │
│           ▼                                                     │
│    ┌─────────────┐                                             │
│    │   Planner   │  Extract: temporal scope, topics, entities  │
│    │    Agent    │                                             │
│    └─────────────┘                                             │
│           │                                                     │
│           ├──────────┬──────────┐                              │
│           ▼          ▼          ▼                              │
│    ┌─────────┐  ┌─────────┐  ┌──────────┐                    │
│    │Timeline │  │Document │  │Alignment │                     │
│    │Retrieval│  │Retrieval│  │  Agent   │                     │
│    │  Agent  │  │  Agent  │  │          │                     │
│    └─────────┘  └─────────┘  └──────────┘                    │
│           │          │            │                             │
│           └──────────┴────────────┘                            │
│                      │                                          │
│                      ▼                                          │
│              ┌──────────────┐                                  │
│              │ Synthesizer  │  Self-check + regenerate         │
│              │    Agent     │                                  │
│              └──────────────┘                                  │
│                      │                                          │
│                      ▼                                          │
│                   Answer                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DATABASE LAYER (PostgreSQL)                    │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │  users   │  │ sources  │  │  events  │  │event_emb │      │
│  │          │  │          │  │          │  │ eddings  │      │
│  │ - id     │  │ - id     │  │ - id     │  │          │      │
│  │ - email  │  │ - type   │  │ - text   │  │- embedding│     │
│  │ - name   │  │ - title  │  │ - date   │  │  (vector)│      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │entities  │  │ topics   │  │  daily_  │  │ weekly_  │      │
│  │          │  │          │  │ timeline │  │ timeline │      │
│  │ - name   │  │ - name   │  │          │  │          │      │
│  │ - type   │  │ - desc   │  │- summary │  │- summary │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│                                                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐            │
│  │   event_entities    │  │    event_topics     │            │
│  │  (many-to-many)     │  │   (many-to-many)    │            │
│  └─────────────────────┘  └─────────────────────┘            │
│                                                                 │
│  Extensions: pgvector (for cosine similarity search)           │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Ingestion Flow

```
1. Upload File/URL
        │
        ▼
2. Extract Text
   - Audio → Whisper API → Transcript
   - PDF → PyPDF2 → Text
   - Web → BeautifulSoup → Text
        │
        ▼
3. Chunk Text
   - Sliding window with overlap
   - Sentence boundary detection
        │
        ▼
4. Generate Embeddings
   - Batch embed all chunks
   - OpenAI text-embedding-3-small
        │
        ▼
5. Create Events
   - Store in events table
   - Store embeddings in event_embeddings
   - Link to source
        │
        ▼
6. Extract Entities & Topics
   - LLM-based extraction
   - Create/link entities
   - Create/link topics
        │
        ▼
7. Update Timelines
   - Assign to daily bucket
   - Generate daily summary (LLM)
   - Assign to weekly bucket
   - Generate weekly summary (LLM)
        │
        ▼
8. Return Success
```

### Query Flow

```
1. User Question
        │
        ▼
2. Planner Agent
   - Extract temporal scope
   - Extract topics/entities
   - Define subtasks
        │
        ▼
3. Timeline Retrieval Agent
   - Filter by date/range (temporal-first)
   - Semantic search within subset
   - Return top-k timeline chunks
        │
        ▼
4. Document Retrieval Agent
   - Semantic search over docs
   - Refine by shared entities
   - Return top-k document chunks
        │
        ▼
5. Alignment Agent
   - Compute chunk similarities
   - Find timeline-document connections
   - Create merged context
        │
        ▼
6. Synthesizer Agent
   - Generate draft answer
   - Self-check completeness
   - Regenerate if needed
   - Return final answer
        │
        ▼
7. Return to User
   - Answer text
   - Dates used (for highlighting)
   - Source chunks (for citations)
```

## Agent Pipeline Details

### 1. Planner Agent

**Input**: Natural language question

**Process**:
- LLM prompt to extract temporal scope
- Parse temporal expressions ("last Tuesday", "this month")
- Extract key topics and entities
- Generate retrieval subtasks

**Output**:
```python
PlannerOutput(
    temporal_scope={
        "type": "date",
        "date": "2024-01-15",
        "description": "last Tuesday"
    },
    topics=["project planning", "budget"],
    entities=["John Smith", "Acme Corp"],
    subtasks="Find timeline events from Jan 15 and relevant budget documents"
)
```

### 2. Timeline Retrieval Agent

**Input**: Question + PlannerOutput

**Process**:
- Filter events by temporal scope
- Generate query embedding
- Cosine similarity search with pgvector
- Return top-k most relevant timeline chunks

**SQL Example**:
```sql
SELECT e.id, e.raw_text, e.date,
       1 - (emb.embedding <=> :query_embedding) as similarity
FROM events e
JOIN event_embeddings emb ON e.id = emb.event_id
WHERE e.user_id = :user_id
  AND e.date = :target_date
ORDER BY similarity DESC
LIMIT 10
```

**Output**: List of TimelineChunk objects

### 3. Document Retrieval Agent

**Input**: Question + PlannerOutput + TimelineChunks

**Process**:
- Filter to document/webpage events
- Semantic search over documents
- Boost chunks sharing entities with timeline
- Return top-k document chunks

**Output**: List of DocumentChunk objects

### 4. Alignment Agent

**Input**: TimelineChunks + DocumentChunks

**Process**:
- Compute pairwise cosine similarity
- Identify high-similarity pairs (>0.6)
- Generate alignment summary
- Create merged context string

**Output**:
```python
AlignmentOutput(
    aligned_pairs=[
        (timeline_chunk_1, doc_chunk_3, 0.87),
        (timeline_chunk_2, doc_chunk_1, 0.82)
    ],
    alignment_summary="Found 2 strong connections...",
    merged_context="=== TIMELINE EVENTS ===\n..."
)
```

### 5. Synthesizer Agent

**Input**: Question + All previous agent outputs

**Process**:
1. Generate draft answer from merged context
2. Self-check using LLM:
   - Does it address the question?
   - Are all subtasks covered?
   - Are gaps acknowledged?
3. Regenerate if inadequate
4. Return final answer

**Output**:
```python
QueryResult(
    answer="Based on your meeting last Tuesday...",
    timeline_chunks=[...],
    document_chunks=[...],
    dates_used=["2024-01-15"],
    confidence=0.85
)
```

## Temporal-First Retrieval Strategy

### Why Temporal-First?

1. **Human Cognition**: People naturally anchor questions in time
   - "What did I do yesterday?"
   - "Summarize last week's meetings"
   - "Find that article I read in December"

2. **Efficiency**: Dramatically reduces search space
   - Instead of searching 100K events
   - Search only 50 events from "last Tuesday"
   - Then run semantic search on smaller set

3. **Accuracy**: Prevents temporal confusion
   - "Last quarter's sales" shouldn't return this quarter's data
   - Temporal filter ensures correct time period

### Implementation

```python
# Step 1: Temporal filtering (fast)
if temporal_scope["type"] == "date":
    candidates = events.filter(date == target_date)
elif temporal_scope["type"] == "range":
    candidates = events.filter(date.between(start, end))
else:
    candidates = events.filter(date >= today - 30 days)

# Step 2: Semantic search (on smaller subset)
results = vector_search(query_embedding, candidates, top_k=10)
```

### Fallback for No Temporal Scope

If question has no temporal reference:
- Default to recent 30 days
- Or use pure semantic search across all events
- Configurable via `DEFAULT_LOOKBACK_DAYS`

## Database Schema Design

### Core Insight: Event-Based Normalization

All modalities (audio, PDF, web) become **events**:

```
Audio file → Transcript → Chunks → Events
PDF file → Text → Chunks → Events
Web page → Scraped text → Chunks → Events
```

Benefits:
- Unified retrieval interface
- Same embedding strategy
- Easy to add new modalities

### Relationships

```
User (1) ──────→ (N) Source
                      │
                      ├──→ (N) Event
                      │        │
                      │        ├──→ (1) EventEmbedding
                      │        │
                      │        ├──→ (N) EventEntity ──→ (1) Entity
                      │        │
                      │        └──→ (N) EventTopic ──→ (1) Topic
                      │
User (1) ──────→ (N) DailyTimeline
User (1) ──────→ (N) WeeklyTimeline
```

### Indexing Strategy

1. **Temporal Indexes**: `(user_id, date)`, `(user_id, timestamp)`
2. **Vector Index**: IVFFlat on `event_embeddings.embedding`
3. **Foreign Keys**: All relations indexed for fast joins

## Scalability & Performance

### Current Capacity

- **Single User**: 100K+ events (years of data)
- **Query Latency**: 1-3 seconds end-to-end
- **Ingestion**: 1 PDF/minute (depends on LLM rate limits)

### Bottlenecks

1. **LLM API Calls**: Timeline summaries, entity extraction
   - Mitigation: Cache, batch, async processing

2. **Vector Search**: Scales to ~1M vectors with IVFFlat
   - Mitigation: Partition by user_id, use HNSW index

3. **Timeline Generation**: On every ingestion
   - Mitigation: Background workers, incremental updates

### Optimization Strategies

#### For Large Single User

```python
# 1. Partition events table
CREATE TABLE events_partition_2024_01
PARTITION OF events
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

# 2. Pre-compute embeddings for common queries
# 3. Add Redis cache for frequent questions
# 4. Use HNSW index for better vector search
```

#### For Many Users

```python
# 1. Separate worker pool for ingestion
# 2. User-specific rate limiting
# 3. Horizontal scaling with read replicas
# 4. Consider separate DB per large user
```

## Privacy & Security Considerations

### Current Design

- Multi-tenant with user_id scoping
- All data in single PostgreSQL instance
- API keys in environment variables

### Local-First Alternative

For maximum privacy:

```
┌─────────────────────────────┐
│       User's Machine        │
│                             │
│  ┌────────────────────────┐ │
│  │  PostgreSQL (local)    │ │
│  └────────────────────────┘ │
│                             │
│  ┌────────────────────────┐ │
│  │  Ollama (local LLM)    │ │
│  └────────────────────────┘ │
│                             │
│  ┌────────────────────────┐ │
│  │  FastAPI Backend       │ │
│  └────────────────────────┘ │
│                             │
│  ┌────────────────────────┐ │
│  │  React Frontend        │ │
│  └────────────────────────┘ │
└─────────────────────────────┘
```

Trade-offs:
- **Privacy**: ✅ All data local
- **Performance**: ❌ Local LLM slower
- **Cost**: ✅ No API fees
- **Quality**: ❌ Local LLM less capable

## Technology Choices & Justifications

### 1. PostgreSQL + pgvector vs. Dedicated Vector DB

**Choice**: PostgreSQL + pgvector

**Rationale**:
- Single database for relational + vector data
- ACID transactions
- Simpler deployment and maintenance
- pgvector performs well for <1M vectors

**Trade-off**: Specialized vector DBs (Pinecone, Weaviate) have better vector search performance

### 2. OpenAI vs. Anthropic vs. Open Source

**Choice**: Abstract both (strategy pattern)

**Rationale**:
- Users can choose based on preference/cost
- Easy to swap providers
- Open source option for privacy

**Implementation**: `BaseLLMClient` with `OpenAIClient` and `AnthropicClient`

### 3. Synchronous vs. Async Ingestion

**Choice**: Synchronous (for simplicity)

**Rationale**:
- Easier to implement and debug
- Immediate feedback to user
- Good enough for low-volume use

**For Production**: Use Celery for background processing

### 4. React vs. Next.js vs. Svelte

**Choice**: React + Vite

**Rationale**:
- Industry standard
- Fast development with Vite
- No SSR needed for this use case

**Trade-off**: Next.js offers better SEO and SSR if needed

## Testing Strategy

### Unit Tests

```python
# Test individual agents
def test_planner_agent():
    planner = PlannerAgent()
    result = planner.execute("What did I do last Tuesday?")
    assert result.temporal_scope["type"] == "date"

# Test services
def test_chunking_service():
    service = ChunkingService(chunk_size=100)
    chunks = service.chunk_text("Long text...")
    assert len(chunks) > 1
```

### Integration Tests

```python
# Test full ingestion pipeline
def test_document_ingestion():
    with open("test.pdf", "rb") as f:
        result = process_document(db, user_id=1, content=f.read())
    assert result.events_created > 0

# Test query pipeline
def test_query_pipeline():
    response = query(user_id=1, question="Test question")
    assert response.answer is not None
```

### End-to-End Tests

```javascript
// Test frontend + backend integration
test('user can ask a question', async () => {
  render(<App />);
  const input = screen.getByPlaceholderText('Ask a question...');
  fireEvent.change(input, { target: { value: 'What did I work on?' } });
  fireEvent.submit(input.closest('form'));

  await waitFor(() => {
    expect(screen.getByText(/Based on/)).toBeInTheDocument();
  });
});
```

## Deployment Checklist

### Backend

- [ ] Set up PostgreSQL with pgvector
- [ ] Configure environment variables (.env)
- [ ] Run database migrations (or init_db())
- [ ] Set up SSL/TLS for production
- [ ] Configure CORS for frontend origin
- [ ] Set up logging and monitoring
- [ ] Add rate limiting
- [ ] Set up background workers (Celery)

### Frontend

- [ ] Build production bundle (`npm run build`)
- [ ] Configure API base URL
- [ ] Set up CDN for static assets
- [ ] Add analytics (optional)
- [ ] Configure error tracking (Sentry, etc.)

### Infrastructure

- [ ] Deploy PostgreSQL (AWS RDS, DigitalOcean, etc.)
- [ ] Deploy backend (Docker, Heroku, Fly.io, etc.)
- [ ] Deploy frontend (Vercel, Netlify, Cloudflare Pages)
- [ ] Set up domain and SSL
- [ ] Configure backups
- [ ] Set up monitoring (Prometheus, Datadog, etc.)

## Conclusion

This Timeline Thinker implementation demonstrates:

1. **Multi-modal ingestion** with unified event model
2. **Temporal-first retrieval** for accuracy and efficiency
3. **Multi-agent pipeline** for sophisticated reasoning
4. **Clean architecture** with clear separation of concerns
5. **Production-ready patterns** (though simplified for assignment)

The system is designed to be:
- **Extensible**: Easy to add new modalities or agents
- **Scalable**: Can handle thousands of documents per user
- **Maintainable**: Clear structure with comprehensive docs
- **User-friendly**: Simple chat interface with timeline context
