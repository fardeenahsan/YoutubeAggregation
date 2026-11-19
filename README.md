# YouTube Channel Comment Analyzer

Analyze comments from a YouTube channel across two date ranges. The dashboard is designed to show sentiment distribution, keyword themes, trends, and linked comment evidence.

## Project structure

- `frontend/` — React + TypeScript + Vite dashboard.
- `backend/` — FastAPI service, YouTube Data API integration, sentiment classification, and keyword extraction.

## Backend quick start

See [backend/README.md](backend/README.md).

## Security

Never commit API keys. Keep `YOUTUBE_API_KEY` in `backend/.env`, which is ignored by Git.
