# Quick Setup Guide for Timeline Thinker

## Database Setup (PostgreSQL with pgvector)

### Option 1: Install PostgreSQL Locally (Recommended for Development)

#### For macOS:

```bash
# Install PostgreSQL using Homebrew
brew install REDACTEDql@14

# Start PostgreSQL service
brew services start REDACTEDql@14

# Add PostgreSQL to PATH (add to ~/.zshrc or ~/.bash_profile)
echo 'export PATH="/opt/homebrew/opt/REDACTEDql@14/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Verify PostgreSQL is running
psql --version
```

#### Install pgvector extension:

```bash
# Clone and build pgvector
cd ~
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
make install

# Or install via Homebrew (easier)
brew install pgvector
```

#### Create database:

```bash
# Create the database
createdb secondbrain

# Connect and enable pgvector
psql secondbrain -c "CREATE EXTENSION vector;"

# Verify pgvector is installed
psql secondbrain -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

### Option 2: Use Docker (Easiest)

If you prefer Docker, use this instead:

```bash
# Run PostgreSQL with pgvector in Docker
docker run -d \
  --name secondbrain-db \
  -e POSTGRES_PASSWORD=REDACTED \
  -e POSTGRES_DB=secondbrain \
  -p 5432:5432 \
  ankane/pgvector

# The database is ready to use immediately!
```

### Option 3: Use SQLite (Simplest - No Vector Search)

For quick testing without PostgreSQL:

1. Update `backend/app/config.py`:
```python
database_url: str = "sqlite:///./secondbrain.db"
```

2. Update `backend/requirements.txt` - remove `psycopg2-binary` and `pgvector`

3. Comment out vector-related code in models

**Note**: This won't support semantic search, only basic functionality.

## Backend Setup

### 1. Install Python Dependencies

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use any text editor
```

**Required variables in .env:**
```env
DATABASE_URL=REDACTEDql://localhost:5432/secondbrain
OPENAI_API_KEY=sk-your-openai-key-here
LLM_PROVIDER=openai
```

**If using Docker PostgreSQL:**
```env
DATABASE_URL=REDACTEDql://REDACTED:REDACTED@localhost:5432/secondbrain
```

### 3. Initialize Database

```bash
# Run the FastAPI app - it will create tables automatically
python -m app.main
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 4. Test Backend

Open a new terminal and test:

```bash
# Health check
curl http://localhost:8000/health

# Should return: {"status":"healthy"}
```

## Frontend Setup

### 1. Install Node.js Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

You should see:
```
VITE v5.0.11  ready in 500 ms

➜  Local:   http://localhost:3000/
```

### 3. Test Frontend

Open your browser to http://localhost:3000

You should see the Timeline Thinker interface!

## Troubleshooting

### PostgreSQL Issues

**Error: "connection to server on socket failed"**
- PostgreSQL is not running
- Solution: `brew services start REDACTEDql@14`

**Error: "database does not exist"**
- Database not created
- Solution: `createdb secondbrain`

**Error: "extension vector does not exist"**
- pgvector not installed
- Solution: `brew install pgvector` then `psql secondbrain -c "CREATE EXTENSION vector;"`

**Error: "psql: command not found"**
- PostgreSQL not in PATH
- Solution: Add to PATH or use full path: `/opt/homebrew/opt/REDACTEDql@14/bin/psql`

### Backend Issues

**Error: "ModuleNotFoundError"**
- Dependencies not installed
- Solution: `pip install -r requirements.txt`

**Error: "No such file or directory: '.env'"**
- Environment file missing
- Solution: `cp .env.example .env` and configure

**Error: "Invalid API key"**
- OpenAI API key not set or invalid
- Solution: Add valid key to `.env` file

**Error: "Could not import pgvector"**
- pgvector Python package missing
- Solution: `pip install pgvector`

### Frontend Issues

**Error: "Cannot GET /"**
- Frontend not running
- Solution: `cd frontend && npm run dev`

**Error: "Network Error"**
- Backend not running or wrong URL
- Solution: Start backend, check API_BASE_URL in `src/services/api.js`

## Quick Test

Once everything is running, test the full flow:

### 1. Ingest a webpage:

```bash
curl -X POST "http://localhost:8000/api/v1/ingest/webpage" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "user_id": 1
  }'
```

### 2. Ask a question:

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "question": "What is artificial intelligence?"
  }'
```

### 3. Or use the UI:

1. Open http://localhost:3000
2. Type a question in the chat
3. See the AI response!

## Recommended: Use Docker Compose (All-in-One)

For the easiest setup, I can create a `docker-compose.yml` that starts everything:

```yaml
version: '3.8'

services:
  db:
    image: ankane/pgvector
    environment:
      POSTGRES_DB: secondbrain
      POSTGRES_PASSWORD: REDACTED
    ports:
      - "5432:5432"
    volumes:
      - REDACTED_data:/var/lib/REDACTEDql/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      DATABASE_URL: REDACTEDql://REDACTED:REDACTED@db:5432/secondbrain
      OPENAI_API_KEY: ${OPENAI_API_KEY}

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  REDACTED_data:
```

Then just run:
```bash
export OPENAI_API_KEY=your-key-here
docker-compose up
```

Everything starts automatically! 🚀
