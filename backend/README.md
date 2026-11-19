# Backend

FastAPI service for fetching YouTube channel comments and analyzing sentiment and keywords.

## Local setup

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your YouTube Data API v3 key to .env
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## Endpoints

- `GET /health`
- `POST /analyses`
- `GET /analyses/{key}`
- `GET /analyses/{key}/comments`

The first implementation runs an analysis synchronously and keeps jobs/comments in process memory. This is a development milestone, not production persistence; the next milestone adds background execution, durable storage, quota-aware caching, and integration tests.

## Data and quota notes

The service fetches videos published in each requested date range, then reads their available comment threads. YouTube may disable comments, omit replies from a page, or reject requests when quota is exhausted. The API key must remain in the backend environment and must never be placed in frontend code or committed to Git.
