# YouTube Channel Comment Analyzer

A full-stack application that analyzes comments on a YouTube channel across two date ranges. It fetches public YouTube comments, classifies sentiment with Cardiff NLP's RoBERTa model, extracts recurring keywords, and presents comparisons in a React dashboard.

## Features

- Accepts YouTube channel handles, channel IDs, and channel URLs.
- Compares comments across two non-overlapping date ranges.
- Classifies comments as **praise**, **neutral**, or **criticism** using `cardiffnlp/twitter-roberta-base-sentiment-latest`.
- Extracts frequently discussed keywords and groups them by sentiment.
- Displays sentiment trends and paginated comment evidence.
- Reports asynchronous analysis status and batch-level sentiment progress.

## Architecture

- **Frontend:** React 19, TypeScript, Vite, Recharts.
- **Backend:** FastAPI, Pydantic, YouTube Data API v3.
- **NLP:** Hugging Face Transformers and PyTorch (RoBERTa).
- **Keyword extraction:** scikit-learn.

The frontend communicates with the backend through the typed HTTP service in `frontend/src/api/`. The backend exposes the endpoints documented in [backend/README.md](backend/README.md).

## Quick start

You need:
- Python 3.12 recommended.
- Node.js 20.19+ and npm 10+.
- A YouTube Data API v3 key.
- Internet access for dependency installation and the one-time model download.

### 1. Configure the backend

Open a terminal:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `backend/.env` and replace `replace_me` with your YouTube Data API v3 key.

Download the sentiment model once (approximately 500 MB):

```powershell
python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; m='cardiffnlp/twitter-roberta-base-sentiment-latest'; AutoTokenizer.from_pretrained(m); AutoModelForSequenceClassification.from_pretrained(m)"
```

Start the API:

```powershell
uvicorn app.main:app --reload
```

The API health check is [http://localhost:8000/health](http://localhost:8000/health), and interactive API documentation is at [http://localhost:8000/docs](http://localhost:8000/docs).

### 2. Start the frontend

Open a second terminal from the repository root:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

For macOS/Linux, use `python3.12 -m venv .venv`, `source .venv/bin/activate`, and `cp .env.example .env` in the backend; use `cp .env.example .env` in the frontend. The remaining commands are the same.

## Verification

From `frontend/`:

```bash
npm run check
```

This runs linting, TypeScript checks, the frontend test suite, and a production build.

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/analyses` | Submit an analysis; returns a job |
| GET | `/analyses/{key}` | Poll job status and retrieve the completed result |
| GET | `/analyses/{key}/comments` | Retrieve paginated comment evidence |

## Important implementation notes

- The RoBERTa model is downloaded once and loaded from the local Hugging Face cache. The first model download is large; subsequent starts reuse the cache.
- The current backend stores jobs and comment evidence in process memory. Restarting the backend clears them. Run a single backend process for this prototype.
- The current implementation is intended for local evaluation, not production deployment or concurrent public traffic. Persistent job storage, a durable queue, database-backed caching, authentication, rate limiting, and deployment hardening remain future engineering work.
- YouTube API quota and comment availability affect which videos and comments can be analyzed. Current collection limits are capped at 20 videos per period and 100 comments per video.
- The sentiment classifier runs on CPU by default. GPU acceleration is not required to run the project.

## Repository layout

```
backend/    FastAPI application and analysis services
frontend/   React + TypeScript dashboard
```

## Security

- Never commit `backend/.env` or paste API keys into source code.
- Keep the YouTube API key on the backend; it is not needed by the frontend.
- Before sharing a local clone, check that no real credentials or personal data have been added to tracked files.
