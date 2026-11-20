from collections import Counter

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, CountVectorizer


def extract_keywords(comments: list[dict], limit: int = 10) -> list[dict]:
    """Count comments containing each useful unigram/bigram, split by existing sentiment."""
    valid_comments = [
        item for item in comments
        if item.get("text", "").strip()
    ]
    texts = [item["text"] for item in valid_comments]
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
    ranked = sorted(
        zip(terms, totals),
        key=lambda pair: (-int(pair[1]), pair[0]),
    )[:limit]

    output = []
    term_indices = {term: index for index, term in enumerate(terms)}

    for term, count in ranked:
        sentiment_counts = Counter()
        column = matrix[:, term_indices[term]].toarray().ravel()
        for index in column.nonzero()[0]:
            sentiment = valid_comments[index].get("sentiment", "neutral")
            sentiment_counts[sentiment] += 1

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
