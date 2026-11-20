import re
from functools import lru_cache

from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    pipeline,
)

MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"

LABEL_MAP = {
    "positive": "praise",
    "neutral": "neutral",
    "negative": "criticism",
}

# Personal circumstances should not automatically count as criticism.
PERSONAL_CONTEXT_PATTERNS = [
    r"\bmy family is struggling\b",
    r"\bi lost my job\b",
    r"\bmy father is sick\b",
    r"\bmy mother is sick\b",
    r"\bplease pray for (me|him|her|us|my family)\b",
    r"\bi live in a poor country\b",
    r"\bi don't know what to do\b",
]

# Clearly conversational comments without an opinion about the creator.
NEUTRAL_DISCUSSION_PATTERNS = [
    r"\bwhat is happening here\b",
    r"\bhappy and sad at the same time\b",
]


def _is_contextually_neutral(text: str) -> bool:
    """Identify a small set of clearly unrelated personal discussions."""
    normalized = text.lower()
    patterns = PERSONAL_CONTEXT_PATTERNS + NEUTRAL_DISCUSSION_PATTERNS
    return any(re.search(pattern, normalized) for pattern in patterns)


@lru_cache(maxsize=1)
def _sentiment_pipeline():
    """Load the downloaded RoBERTa model once, without internet access."""
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        local_files_only=True,
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        local_files_only=True,
    )
    return pipeline(
        "sentiment-analysis",
        model=model,
        tokenizer=tokenizer,
        device=-1,
    )


def classify_sentiments(texts: list[str]) -> list[str]:
    """Classify comments using RoBERTa with contextual corrections."""
    if not texts:
        return []

    cleaned = [text.strip() if text else "" for text in texts]
    results = ["neutral"] * len(cleaned)
    valid_indices = []

    for index, text in enumerate(cleaned):
        if not text or _is_contextually_neutral(text):
            continue
        valid_indices.append(index)

    if not valid_indices:
        return results

    valid_texts = [cleaned[index] for index in valid_indices]
    predictions = _sentiment_pipeline()(
        valid_texts,
        batch_size=64,
        truncation=True,
        max_length=128,
    )

    for index, prediction in zip(valid_indices, predictions):
        label = prediction["label"].lower()
        results[index] = LABEL_MAP.get(label, "neutral")

    return results


def classify_sentiment(text: str) -> str:
    """Classify one comment while preserving the existing API."""
    return classify_sentiments([text])[0]
