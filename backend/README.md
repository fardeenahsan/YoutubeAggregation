# Backend

FastAPI service for fetching YouTube channel comments and analyzing sentiment and keywords.

## Local setup

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
# Install the CPU build of PyTorch (recommended for local development)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# Download the sentiment model once. The application loads it from the
# local Hugging Face cache and does not download model files at runtime.
python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; m='cardiffnlp/twitter-roberta-base-sentiment-latest'; AutoTokenizer.from_pretrained(m); AutoModelForSequenceClassification.from_pretrained(m)"

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

Analysis requests run as background tasks and the frontend polls the job endpoint until completion. Jobs and comments are currently held in process memory, so they are lost when the backend restarts and are not shared across multiple workers. Use a persistent queue and database before production deployment.

## Data and quota notes

The service fetches videos published in each requested date range, then reads their available comment threads. YouTube may disable comments, omit replies from a page, or reject requests when quota is exhausted. The API key must remain in the backend environment and must never be placed in frontend code or committed to Git.
