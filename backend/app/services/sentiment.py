import logging
import re
from functools import lru_cache
from collections.abc import Callable
from time import perf_counter

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    pipeline,
)

logger = logging.getLogger(__name__)

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


def _inference_device() -> int:
    """Prefer CUDA when the installed PyTorch build and hardware support it."""
    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        logger.info("Sentiment inference device: CUDA (0) - %s", device_name)
        return 0

    logger.info("Sentiment inference device: CPU (CUDA unavailable)")
    return -1


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
    device = _inference_device()
    return pipeline(
        "sentiment-analysis",
        model=model,
        tokenizer=tokenizer,
        device=device,
    )


def classify_sentiments(
    texts: list[str],
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[str]:
    """Classify comments in visible batches using RoBERTa."""
    if not texts:
        return []

    cleaned = [text.strip() if text else "" for text in texts]
    results = ["neutral"] * len(cleaned)
    valid_indices = [
        index for index, text in enumerate(cleaned)
        if text and not _is_contextually_neutral(text)
    ]

    if not valid_indices:
        if progress_callback:
            progress_callback(len(cleaned), len(cleaned))
        return results

    classifier = _sentiment_pipeline()
    batch_size = 64
    total = len(valid_indices)

    for start in range(0, total, batch_size):
        batch_indices = valid_indices[start:start + batch_size]
        batch_texts = [cleaned[index] for index in batch_indices]
        batch_started = perf_counter()
        predictions = classifier(
            batch_texts,
            batch_size=batch_size,
            truncation=True,
            max_length=128,
        )
        elapsed = perf_counter() - batch_started
        logger.info(
            "Sentiment batch: %d/%d comments in %.2f seconds (%.1f comments/sec)",
            min(start + len(batch_indices), total),
            total,
            elapsed,
            len(batch_indices) / elapsed if elapsed > 0 else 0,
        )
        for index, prediction in zip(batch_indices, predictions):
            label = prediction["label"].lower()
            results[index] = LABEL_MAP.get(label, "neutral")

        if progress_callback:
            progress_callback(min(start + len(batch_indices), total), total)

    return results


def classify_sentiment(text: str) -> str:
    """Classify one comment while preserving the existing API."""
    return classify_sentiments([text])[0]
