from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class DateRange(BaseModel):
    start: date
    end: date


class AnalysisRequest(BaseModel):
    channel: str = Field(min_length=2, max_length=200)
    periodA: DateRange
    periodB: DateRange
    groupBy: Literal["videoPublishedAt", "commentPublishedAt"] = "videoPublishedAt"


class SentimentCounts(BaseModel):
    praise: int = 0
    neutral: int = 0
    criticism: int = 0


class ChannelInfo(BaseModel):
    id: str
    handle: str | None = None
    title: str
    url: str


class KeywordItem(BaseModel):
    term: str
    count: int
    sentiment: SentimentCounts


class PeriodResult(BaseModel):
    period: Literal["A", "B"]
    range: DateRange
    videoCount: int
    videosSkipped: int
    commentCount: int
    sentiment: SentimentCounts


class TrendBucket(BaseModel):
    period: Literal["A", "B"]
    index: int
    start: date
    end: date
    videoCount: int
    commentCount: int
    sentiment: SentimentCounts


class AnalysisResult(BaseModel):
    source: Literal["youtube"] = "youtube"
    channel: ChannelInfo
    groupBy: Literal["videoPublishedAt", "commentPublishedAt"]
    generatedAt: datetime
    granularity: Literal["week", "month"]
    periods: dict[str, PeriodResult]
    trend: list[TrendBucket]
    keywords: dict[str, list[KeywordItem]]
    sampled: bool = False


class CommentVideo(BaseModel):
    id: str
    title: str
    publishedAt: datetime
    url: str


class CommentEvidence(BaseModel):
    id: str
    text: str
    authorName: str
    likeCount: int
    publishedAt: datetime
    sentiment: Literal["praise", "neutral", "criticism"]
    period: Literal["A", "B"]
    isReply: bool
    video: CommentVideo
    url: str


class CommentPage(BaseModel):
    items: list[CommentEvidence]
    total: int
    nextCursor: str | None = None


class AnalysisJob(BaseModel):
    key: str
    status: Literal["queued", "running", "done", "error"]
    progress: int = 0
    step: str = "Queued"
    error: dict | None = None
    result: AnalysisResult | None = None
