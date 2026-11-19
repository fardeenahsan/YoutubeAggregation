import re
from datetime import date, datetime, time, timezone
from urllib.parse import urlparse

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..config import settings


class YouTubeServiceError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _youtube():
    if not settings.youtube_api_key or settings.youtube_api_key == "replace_me":
        raise YouTubeServiceError("CONFIGURATION_ERROR", "Set YOUTUBE_API_KEY in backend/.env.", 503)
    return build("youtube", "v3", developerKey=settings.youtube_api_key, cache_discovery=False)


def normalize_channel_input(value: str) -> tuple[str | None, str | None]:
    value = value.strip()
    if re.fullmatch(r"UC[a-zA-Z0-9_-]{22}", value):
        return value, None
    if value.startswith("@"):
        return None, value
    if "youtube.com" in value:
        parsed = urlparse(value if "://" in value else f"https://{value}")
        parts = [part for part in parsed.path.split("/") if part]
        if parts and parts[0].startswith("@"):
            return None, parts[0]
        if len(parts) >= 2 and parts[0] == "channel":
            return parts[1], None
    raise YouTubeServiceError("INVALID_CHANNEL", "Enter a YouTube @handle, channel ID, or channel URL.", 422)


def resolve_channel(value: str) -> dict:
    channel_id, handle = normalize_channel_input(value)
    api = _youtube()
    if handle:
        response = api.channels().list(part="snippet, id", forHandle=handle.lstrip("@")).execute()
    else:
        response = api.channels().list(part="snippet, id", id=channel_id).execute()
    items = response.get("items", [])
    if not items:
        raise YouTubeServiceError("INVALID_CHANNEL", "We couldn't find that YouTube channel.", 404)
    item = items[0]
    snippet = item["snippet"]
    custom = snippet.get("customUrl") or handle
    return {
        "id": item["id"],
        "handle": custom if custom and custom.startswith("@") else (f"@{custom}" if custom else None),
        "title": snippet["title"],
        "url": f"https://www.youtube.com/channel/{item['id']}",
    }


def _iso_utc(day: date, end: bool = False) -> str:
    stamp = datetime.combine(day, time.max if end else time.min, tzinfo=timezone.utc)
    return stamp.isoformat().replace("+00:00", "Z")


def fetch_period(channel_id: str, period: dict, group_by: str) -> tuple[list[dict], list[dict], int]:
    """Fetch channel uploads in the date range, then comments for each video."""
    api = _youtube()
    search_response = api.search().list(
        part="id,snippet",
        channelId=channel_id,
        type="video",
        order="date",
        publishedAfter=_iso_utc(period["start"]),
        publishedBefore=_iso_utc(period["end"], True),
        maxResults=min(50, settings.max_videos_per_period),
    ).execute()
    videos = search_response.get("items", [])
    comments: list[dict] = []
    skipped = 0

    for video in videos:
        video_id = video["id"]["videoId"]
        video_snippet = video["snippet"]
        video_info = {
            "id": video_id,
            "title": video_snippet["title"],
            "publishedAt": video_snippet["publishedAt"],
            "url": f"https://www.youtube.com/watch?v={video_id}",
        }
        token = None
        collected = 0
        while collected < settings.max_comments_per_video:
            batch = api.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=min(100, settings.max_comments_per_video - collected),
                pageToken=token,
                textFormat="plainText",
                order="time",
            ).execute()
            for thread in batch.get("items", []):
                top = thread["snippet"]["topLevelComment"]
                top_snippet = top["snippet"]
                comments.append(_comment_record(top, top_snippet, video_info, False))
                collected += 1
                for reply in thread.get("replies", {}).get("comments", []):
                    if collected >= settings.max_comments_per_video:
                        break
                    comments.append(_comment_record(reply, reply["snippet"], video_info, True))
                    collected += 1
            token = batch.get("nextPageToken")
            if not token:
                break
        # A disabled comments endpoint is reported per-video, without aborting the job.
    return videos, comments, skipped


def _comment_record(comment: dict, snippet: dict, video: dict, is_reply: bool) -> dict:
    comment_id = comment["id"]
    return {
        "id": comment_id,
        "text": snippet.get("textOriginal") or snippet.get("textDisplay") or "",
        "authorName": snippet.get("authorDisplayName", "YouTube user"),
        "likeCount": int(snippet.get("likeCount", 0)),
        "publishedAt": snippet["publishedAt"],
        "isReply": is_reply,
        "video": video,
        "url": f"{video['url']}&lc={comment_id}",
    }
