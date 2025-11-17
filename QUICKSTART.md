# Quick Start Guide

## ✅ Database Setup (DONE!)

PostgreSQL with pgvector is now running in Docker! 🎉

```bash
# Check database status
docker ps

# You should see:
# secondbrain-db running on port 5432
```

## Next Steps

### 1. Add Your OpenAI API Key

Edit `backend/.env` and add your OpenAI API key:

```bash
cd backend
nano .env  # or use any text editor
```

Replace this line:
```
OPENAI_API_KEY=your-openai-api-key-here
```

With your actual key:
```
OPENAI_API_KEY=sk-proj-...your-actual-key...
```

Save and close the file.

### 2. Install Backend Dependencies

```bash
# Still in backend directory
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Start the Backend

```bash
python -m app.main
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

The backend will automatically create all database tables on first run!

### 4. Test the Backend

Open a new terminal and test:

```bash
# Health check
curl http://localhost:8000/health

# Should return: {"status":"healthy"}
```

### 5. Install Frontend Dependencies

```bash
cd ../frontend
npm install
```

### 6. Start the Frontend

```bash
npm run dev
```

You should see:
```
VITE v5.0.11  ready in 500 ms
➜  Local:   http://localhost:3000/
```

### 7. Open the App

Open your browser to: **http://localhost:3000**

You should see the Timeline Thinker interface! 🧠

## Quick Test

### Option 1: Use the UI

1. Open http://localhost:3000
2. Type a question like "Hello, can you help me?"
3. See the AI respond!

### Option 2: Ingest a Webpage

```bash
curl -X POST "http://localhost:8000/api/v1/ingest/webpage" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "user_id": 1
  }'
```

Wait for it to finish (takes 10-30 seconds), then ask:

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "question": "What is artificial intelligence?"
  }'
```

Or ask in the UI! The timeline will update automatically.

## Managing the Database

### Stop PostgreSQL

```bash
docker-compose down
```

### Start PostgreSQL (if stopped)

```bash
docker-compose up -d
```

### Reset Everything (delete all data)

```bash
docker-compose down -v
docker-compose up -d
# Re-enable vector extension
docker exec secondbrain-db psql -U REDACTED -d secondbrain -c "CREATE EXTENSION vector;"
```

### View Logs

```bash
docker logs secondbrain-db
```

## Troubleshooting

### Backend won't start

**Error: "ModuleNotFoundError"**
- Make sure you activated the virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

**Error: "connection refused"**
- Make sure Docker container is running: `docker ps`
- Start it if needed: `docker-compose up -d`

**Error: "Invalid API key"**
- Make sure you added your OpenAI API key to `backend/.env`

### Frontend won't start

**Error: "Cannot find module"**
- Install dependencies: `cd frontend && npm install`

**Error: "Network Error"**
- Make sure backend is running on http://localhost:8000
- Check backend logs for errors

## What's Next?

1. **Ingest your data**: Upload PDFs, audio files, or save webpages
2. **Ask questions**: Use natural language to query your knowledge base
3. **Explore the code**: Check out the architecture in [ARCHITECTURE.md](ARCHITECTURE.md:1)
4. **Read the docs**: Full documentation in [README.md](README.md:1)

## Summary

You now have:
- ✅ PostgreSQL with pgvector running in Docker
- ✅ `.env` file configured (just add your API key)
- ✅ Ready to start backend and frontend

Just add your OpenAI API key and you're good to go! 🚀
