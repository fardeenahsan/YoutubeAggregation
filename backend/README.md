# Backend

FastAPI service for retrieving YouTube channel comments and analyzing sentiment and keywords.

## Requirements

- Python 3.12 recommended.
- A YouTube Data API v3 key.
- Internet access for package installation and the initial model download.

## Windows setup (PowerShell)

Run from the repository root:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set `YOUTUBE_API_KEY` to a YouTube Data API v3 key.

## macOS / Linux setup

Run from the repository root:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set `YOUTUBE_API_KEY`.

## Download the sentiment model

The first setup requires downloading the Cardiff NLP RoBERTa model (approximately 500 MB). Run this once while the virtual environment is active:

```bash
python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; m='cardiffnlp/twitter-roberta-base-sentiment-latest'; AutoTokenizer.from_pretrained(m); AutoModelForSequenceClassification.from_pretrained(m)"
```

The application loads the model from the local Hugging Face cache with `local_files_only=True`; it does not download model files during analysis.

## Run

From `backend/`, with the virtual environment active:

```bash
uvicorn app.main:app --reload
```

- Health: http://localhost:8000/health
- Interactive API docs: http://localhost:8000/docs

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/analyses` | Submit an analysis and receive a job key |
| GET | `/analyses/{key}` | Poll status and retrieve the result |
| GET | `/analyses/{key}/comments` | Retrieve filtered, paginated comment evidence |

Analysis runs as a background task. The frontend polls the job endpoint and receives progress updates while sentiment is classified in batches.

## Current prototype limitations

- Jobs and comments are stored in process memory. They disappear when the backend restarts and are not shared between multiple backend workers.
- Run a single backend process for local evaluation.
- This is not yet configured for production traffic. A persistent database, durable job queue, caching, authentication, rate limiting, and deployment configuration are still needed.
- YouTube API quota limits and disabled comments can affect the data returned.
- Collection is capped at 20 videos per period and 100 comments per video.
- The sentiment model runs on CPU by default.

Keep the API key in `.env`. Never commit it or expose it in frontend configuration.
