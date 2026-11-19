from collections import Counter, defaultdict

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, CountVectorizer

from .sentiment import classify_sentiment


def extract_keywords(comments: list[dict], limit: int = 10) -> list[dict]:
    """Count comments containing each useful unigram/bigram, split by sentiment."""
    texts = [item["text"] for item in comments if item.get("text", "").strip()]
    if not texts:
        return []

    vectorizer = CountVectorizer(
        stop_words=list(ENGLISH_STOP_WORDS),
        ngram_range=(1, 2),
        binary=True,
        token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z']{2,}\b",
        max_features=5000,
    )
    try:
        matrix = vectorizer.fit_transform(texts)
    except ValueError:
        return []

    terms = vectorizer.get_feature_names_out()
    totals = matrix.sum(axis=0).A1
    ranked = sorted(zip(terms, totals), key=lambda pair: (-int(pair[1]), pair[0]))[:limit]
    output = []
    for term, count in ranked:
        sentiment_counts = Counter()
        column = matrix[:, list(terms).index(term)].toarray().ravel()
        for index in column.nonzero()[0]:
            sentiment_counts[classify_sentiment(texts[index])] += 1
        output.append({
            "term": str(term),
            "count": int(count),
            "sentiment": {
                "praise": sentiment_counts["praise"],
                "neutral": sentiment_counts["neutral"],
                "criticism": sentiment_counts["criticism"],
            },
        })
    return output
