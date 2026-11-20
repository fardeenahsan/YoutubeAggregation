from datetime import date, datetime, timezone
from uuid import uuid4
from collections import Counter

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .schemas import AnalysisJob, AnalysisRequest
from .services.keywords import extract_keywords
from .services.sentiment import classify_sentiments
from .services.youtube import YouTubeServiceError, fetch_period, resolve_channel

app = FastAPI(title="YouTube Comment Analyzer API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Jobs and comments are held in process memory for this first milestone.
# Use a persistent queue/database before deploying multiple workers or production traffic.
JOBS: dict[str, dict] = {}
COMMENTS: dict[str, list[dict]] = {}


def _sentiment_counts(items: list[dict]) -> dict:
    counts = Counter(item["sentiment"] for item in items)
    return {"praise": counts["praise"], "neutral": counts["neutral"], "criticism": counts["criticism"]}


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _analyze_period(label: str, date_range, channel_id: str, group_by: str, job: dict):
    videos, raw_comments, skipped = fetch_period(
        channel_id,
        date_range.model_dump(),
        group_by,
    )

    job.update(
        progress=35 if label == "A" else 70,
        step=f"Analyzing sentiment for period {label} ({len(raw_comments):,} comments)",
    )
    texts = [comment["text"] for comment in raw_comments]
    start_progress, end_progress = (35, 44) if label == "A" else (70, 79)
    def report_sentiment_progress(done: int, total: int) -> None:
        fraction = done / total if total else 1
        job.update(
            progress=round(start_progress + (end_progress - start_progress) * fraction),
            step=f"Sentiment analysis period {label}: {done:,}/{total:,} comments",
        )
    job.update(step=f"Loading sentiment model for period {label}")
    sentiments = classify_sentiments(texts, progress_callback=report_sentiment_progress)

    analyzed = []
    for comment, sentiment in zip(raw_comments, sentiments):
        comment["sentiment"] = sentiment
        comment["period"] = label
        analyzed.append(comment)

    return videos, analyzed, skipped


def _make_buckets(label: str, date_range, videos: list[dict], comments: list[dict], granularity: str):
    from datetime import timedelta
    span = 7 if granularity == "week" else 30
    buckets = []
    cursor = date_range.start
    index = 0
    while cursor <= date_range.end:
        end = min(cursor + timedelta(days=span - 1), date_range.end)
        bucket_comments = [
            item for item in comments
            if cursor <= _parse_dt(item["video"]["publishedAt"]).date() <= end
        ]
        bucket_videos = [
            item for item in videos
            if cursor <= date.fromisoformat(item["snippet"]["publishedAt"][:10]) <= end
        ]
        buckets.append({
            "period": label, "index": index, "start": cursor, "end": end,
            "videoCount": len(bucket_videos), "commentCount": len(bucket_comments),
            "sentiment": _sentiment_counts(bucket_comments),
        })
        cursor = end + timedelta(days=1)
        index += 1
    return buckets


def _run_analysis(request: AnalysisRequest, key: str) -> tuple[dict, list[dict]]:
    channel = resolve_channel(request.channel)
    job = JOBS[key]
    job.update(progress=20, step="Fetching comments for period A")

    results = {}
    all_comments = []
    all_trend = []
    max_days = max((request.periodA.end - request.periodA.start).days + 1,
                   (request.periodB.end - request.periodB.start).days + 1)
    granularity = "week" if max_days <= 120 else "month"

    for index, (label, date_range) in enumerate((("A", request.periodA), ("B", request.periodB))):
        if index == 1:
            job.update(progress=55, step="Fetching comments for period B")
        videos, comments, skipped = _analyze_period(label, date_range, channel["id"], request.groupBy, job)
        all_comments.extend(comments)
        results[label] = {
            "period": label, "range": date_range.model_dump(),
            "videoCount": len(videos), "videosSkipped": skipped,
            "commentCount": len(comments), "sentiment": _sentiment_counts(comments),
        }
        job.update(progress=45 if label == "A" else 80, step=f"Extracting keywords for period {label}")
        all_trend.extend(_make_buckets(label, date_range, videos, comments, granularity))
        results.setdefault("_keywords", {})[label] = extract_keywords(comments)

    result = {
        "source": "youtube", "channel": channel, "groupBy": request.groupBy,
        "generatedAt": datetime.now(timezone.utc), "granularity": granularity,
        "periods": {key: results[key] for key in ("A", "B")},
        "trend": all_trend, "keywords": results["_keywords"],
    }
    return result, all_comments


def _process_analysis(key: str, request: AnalysisRequest) -> None:
    """Run a submitted analysis after returning the job key to the browser."""
    job = JOBS[key]
    job.update(status="running", progress=10, step="Resolving YouTube channel")
    try:
        result, comments = _run_analysis(request, key)
        COMMENTS[key] = comments
        job.update(status="done", progress=100, step="Analysis complete", result=result)
    except YouTubeServiceError as exc:
        job.update(
            status="error",
            progress=100,
            step="Analysis failed",
            error={"code": exc.code, "message": exc.message},
        )
    except Exception:
        # Keep internal exception details out of the public API response.
        job.update(
            status="error",
            progress=100,
            step="Analysis failed",
            error={"code": "ANALYSIS_FAILED", "message": "The analysis failed. Check the backend terminal for details."},
        )
        import traceback
        traceback.print_exc()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyses", response_model=AnalysisJob, status_code=202)
def create_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    today = datetime.now(timezone.utc).date()
    for label, period in (("A", request.periodA), ("B", request.periodB)):
        if period.start > period.end or period.end > today or (period.end - period.start).days > 365:
            raise HTTPException(422, detail={"error": {"code": "INVALID_DATE_RANGE", "message": f"Period {label} must be valid, non-future, and at most 366 days."}})
    if not (request.periodA.end < request.periodB.start or request.periodB.end < request.periodA.start):
        raise HTTPException(422, detail={"error": {"code": "OVERLAPPING_PERIODS", "message": "Periods A and B must not overlap."}})

    key = uuid4().hex
    JOBS[key] = {
        "key": key, "status": "queued", "progress": 0,
        "step": "Queued", "error": None, "result": None,
    }
    background_tasks.add_task(_process_analysis, key, request)
    return JOBS[key]


@app.get("/analyses/{key}", response_model=AnalysisJob)
def get_analysis(key: str):
    if key not in JOBS:
        raise HTTPException(404, detail={"error": {"code": "ANALYSIS_NOT_FOUND", "message": "Analysis not found."}})
    return JOBS[key]


@app.get("/analyses/{key}/comments")
def get_comments(
    key: str,
    period: str | None = None,
    sentiment: str | None = None,
    keyword: str | None = None,
    cursor: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    if key not in JOBS or JOBS[key]["status"] != "done":
        raise HTTPException(404, detail={"error": {"code": "ANALYSIS_NOT_FOUND", "message": "Completed analysis not found."}})
    items = COMMENTS.get(key, [])
    if period:
        items = [item for item in items if item["period"] == period]
    if sentiment:
        items = [item for item in items if item["sentiment"] == sentiment]
    if keyword:
        items = [item for item in items if keyword.casefold() in item["text"].casefold()]
    items = sorted(items, key=lambda item: (-item["likeCount"], item["publishedAt"], item["id"]))
    page = items[cursor:cursor + limit]
    return {"items": page, "total": len(items), "nextCursor": str(cursor + limit) if cursor + limit < len(items) else None}
