# Frontend and backend API contract

This document describes the endpoints implemented by the FastAPI service. The TypeScript types in `src/api/types.ts` and Pydantic schemas in `backend/app/schemas.py` are the code-level references.

## Submit an analysis

`POST /analyses`

Request body:

```json
{
  "channel": "@youtubehandle",
  "periodA": { "start": "2026-01-01", "end": "2026-02-01" },
  "periodB": { "start": "2026-03-01", "end": "2026-04-01" },
  "groupBy": "videoPublishedAt"
}
```

The endpoint validates date ranges and returns HTTP 202 with an `AnalysisJob`:

```json
{
  "key": "job-id",
  "status": "queued",
  "progress": 0,
  "step": "Queued",
  "error": null,
  "result": null
}
```

Job status is `queued`, `running`, `done`, or `error`. Progress and the current processing step are updated while the job runs. A completed job includes its analysis result.

## Poll a job

`GET /analyses/{key}`

Returns the current `AnalysisJob`. Poll until the status is `done` or `error`.

## Retrieve comment evidence

`GET /analyses/{key}/comments`

Optional query parameters:

| Parameter | Description |
|---|---|
| `period` | Filter to period `A` or `B` |
| `sentiment` | Filter to `praise`, `neutral`, or `criticism` |
| `keyword` | Case-insensitive substring filter |
| `cursor` | Zero-based offset (default 0) |
| `limit` | Page size from 1 to 100 (default 20) |

The response contains `items`, the filtered `total`, and `nextCursor` (null on the last page).

## Health check

`GET /health` returns `{"status":"ok"}` when the API process is available.

## Data and runtime notes

- Dates are inclusive calendar dates.
- The analysis fetches videos in each date range, then retrieves available comments for those videos.
- The current collector caps each period at 20 videos and each video at 100 comments.
- Sentiment labels are `praise`, `neutral`, and `criticism`.
- The backend stores job state and comment evidence in process memory. A backend restart clears them; multiple workers do not share state.
- Error responses and job errors include a stable error code and a user-facing message. Internal exception details are written to the backend terminal, not returned to the client.
