# Timeline Thinker

Timeline Thinker is a temporal-first personal knowledge companion. It ingests audio, documents, and webpages, normalizes them into daily "memory" events, and lets you chat with the data through a source-aware multi-agent retrieval pipeline. The UI highlights what you discussed each day, saves per-session notes, and can export those notes as a PDF with one click.

## Why Timeline Thinker?
- **Temporal-first retrieval** – questions are interpreted through time ("yesterday", "last week"), so answers stay anchored to the right moment.
- **Source-centric chat** – pick any upload ("Timeline Focus") and the chat sticks to that source until you clear it.
- **Session memory** – see every source you discussed today, clear the slate, or export the notes.
- **One-click PDFs** – the timeline sidebar has a "Get Notes" button that downloads context + Q/A snippets for that day.
- **Five-agent reasoning** – planner, timeline retriever, document retriever, alignment, synthesizer.

## Architecture Overview
```
Ingestion: Audio / PDF / Webpage -> Chunking -> Events + Embeddings -> Timelines & Sessions
                                                             ↓
      Query: Question (+ optional focused source)
            -> Planner Agent -> Timeline Retrieval -> Document Retrieval
            -> Alignment Agent -> Synthesizer Agent -> Final answer
```

### Agents
1. **Planner** extracts temporal scope, topics, entities.
2. **Timeline Retrieval** narrows by time before semantic search.
3. **Document Retrieval** searches documents/webpages and boosts entity matches.
4. **Alignment** finds relationships between timeline + document chunks.
5. **Synthesizer** builds the answer, self-checks, and emits the final response.

## Tech Stack
- **Backend:** FastAPI, PostgreSQL + pgvector, SQLAlchemy, OpenAI/Anthropic LLMs, Whisper for audio, ReportLab for PDF exports.
- **Frontend:** React + Vite, custom chat + timeline components, Axios client.
- **Infra helpers:** Docker (optional), `.env` configuration, npm scripts.

## Repository Layout
```
TimelineThinker/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routers (ingest, query, timeline, sessions)
│   │   ├── agents/       # Planner, retrieval, alignment, synthesizer
│   │   ├── models/       # SQLAlchemy ORM tables
│   │   ├── pipeline/     # Ingestion flows (audio/document/web)
│   │   ├── schemas/      # Pydantic request/response models
│   │   ├── services/     # LLM, embeddings, timeline updates, sessions
│   │   └── main.py       # FastAPI entrypoint
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/     # Chat UI + input box
│   │   │   ├── Sessions/ # Session panel with Clear All
│   │   │   └── Timeline/ # Timeline sidebar + Get Notes button
│   │   ├── services/     # Axios API client
│   │   └── App.jsx       # Root component combining panels
│   └── package.json
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL 14+ with the `pgvector` extension
- OpenAI (or Anthropic) API key(s)

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # or create backend/.env manually
# edit backend/.env with DATABASE_URL, OPENAI_API_KEY, etc.
uvicorn app.main:app --reload  # http://localhost:8000
```

Ensure your Postgres DB has pgvector enabled:
```sql
CREATE DATABASE timeline_thinker;
\c timeline_thinker
CREATE EXTENSION IF NOT EXISTS vector;
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev   # http://localhost:5173 by default
```
Set `VITE_API_BASE_URL` in `frontend/.env` if the backend is not on localhost:8000.

## Key API Endpoints

### Ingestion
- `POST /api/v1/ingest/audio` – multipart file upload, processes via Whisper.
- `POST /api/v1/ingest/document` – PDFs/Markdown/TXT.
- `POST /api/v1/ingest/webpage` – `{ "url": "https://..." }` payload.

Each endpoint returns `{source_id, title, events_created, message}`.

### Query
```json
POST /api/v1/query
{
  "user_id": 1,
  "question": "What is this article talking about?",
  "source_id": 42          // optional – focuses retrieval on that upload
}
```
Response includes `answer`, `timeline_chunks`, `document_chunks`, and `confidence`.

### Timeline
- `GET /api/v1/timeline/daily?user_id=1&days=30` – summaries for the sidebar.
- `GET /api/v1/timeline/topics?user_id=1` – most-referenced topics.
- `GET /api/v1/timeline/day-notes?user_id=1&target_date=2025-01-15` – downloads a PDF with that day’s sources + Q/A snippets.

### Sessions
- `GET /api/v1/sessions/current?user_id=1` – returns today’s sources, interactions, and auto summary.
- `DELETE /api/v1/sessions/current/source/{source_id}?user_id=1` – remove a single source from today.
- `DELETE /api/v1/sessions/current?user_id=1` – “Clear All” session data for today (mirrors the frontend button).

## Frontend UX Highlights
- **Source Selector:** dropdown + pill row showing every upload; clicking sets the chat focus.
- **Chat Header:** shows which source you’re talking to; system messages log focus changes.
- **Session Panel:** lists today’s sources, includes per-source remove buttons and a “Clear All” CTA.
- **Timeline Sidebar:** displays date + summary + number of events, and each row has a “Get Notes” button that hits the PDF endpoint.

## Deployment Tips
1. **Push to GitHub** – use the .gitignore already provided (`git add . && git commit`).
2. **Backend hosting** – Run FastAPI on Render/Railway/Fly/neon-backed VM. Set environment variables there (DB URL, OpenAI key).
3. **Frontend hosting** – Deploy the Vite build to Vercel/Netlify and point `VITE_API_BASE_URL` at the hosted backend.
4. **Database** – Use a managed Postgres with pgvector (Neon, Supabase, etc.).

## Future Enhancements
- Per-topic timelines and clustering.
- Automatic weekly recap email using the PDF notes.
- Elastic/pgvector hybrid search for larger corpora.

Timeline Thinker already supports the full ingestion → timeline → chat loop, source-specific conversations, session management, and exportable notes. Customize the agents or UI to fit your workflow! 
