from functools import lru_cache

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


@lru_cache(maxsize=1)
def _analyzer() -> SentimentIntensityAnalyzer:
    return SentimentIntensityAnalyzer()


def classify_sentiment(text: str) -> str:
    """Return the UI's three labels using VADER's compound score."""
    score = _analyzer().polarity_scores(text or "")["compound"]
    if score >= 0.05:
        return "praise"
    if score <= -0.05:
        return "criticism"
    return "neutral"
