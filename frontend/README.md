# Frontend

React dashboard for comparing YouTube channel comment sentiment across two date ranges.

## Features

- Channel handle, channel ID, and URL input.
- Two-period comparison workflow.
- Praise, neutral, and criticism summaries.
- Sentiment trends and keyword breakdowns.
- Paginated comment evidence linked to source videos.
- Live analysis-job progress and error states.
- Deterministic demo mode when no backend URL is configured.

## Requirements

- Node.js 20.19+.
- npm 10+.

## Setup

From `frontend/`:

```bash
npm ci
cp .env.example .env
npm run dev
```

On Windows PowerShell, use:

```powershell
npm ci
Copy-Item .env.example .env
npm run dev
```

Open http://localhost:5173.

## Connect to the backend

The frontend reads `VITE_API_BASE_URL` from `.env`. The provided `.env.example` points to the local FastAPI server:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

When this variable is set, the app uses the real HTTP API. If it is absent, the app uses deterministic demo data. Start the backend before submitting a live YouTube analysis. See [the backend setup guide](../backend/README.md).

## Quality checks

```bash
npm run check
```

This runs ESLint, TypeScript type-checking, Vitest, and the production build.

Individual commands:

- `npm run lint`
- `npm run typecheck`
- `npm test`
- `npm run build`

## Project structure

- `src/api/` — typed API contract, HTTP client, and service selection.
- `src/mock/` — deterministic demo-data service.
- `src/hooks/` — analysis and comment-loading lifecycle.
- `src/lib/` — date, formatting, and validation helpers.
- `src/components/` — reusable interface components.
- `src/dashboard/` — analysis form, status, charts, summaries, and comment evidence.
- `src/styles/` — design tokens and application styles.

## Notes

- The real API requires a configured YouTube Data API key in the backend.
- Demo mode does not call YouTube and is useful for checking the UI without backend credentials.
- The backend currently keeps jobs and comments in memory; it is intended for local prototype evaluation, not production deployment.
