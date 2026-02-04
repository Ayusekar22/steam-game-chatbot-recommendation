POSITIVE_WORDS = {
    "good", "great", "fun", "excellent", "smooth",
    "amazing", "love", "enjoy"
}

NEGATIVE_WORDS = {
    "bad", "bug", "lag", "crash", "boring",
    "slow", "problem", "issue", "terrible"
}


def detect_sentiment(text):
    pos = sum(word in text for word in POSITIVE_WORDS)
    neg = sum(word in text for word in NEGATIVE_WORDS)

    if pos > neg:
        return "positive"
    elif neg > pos:
        return "negative"
    else:
        return "neutral"


def assign_aspects(reviews_clean, aspects):
    """
    Assign aspects & sentiment per review
    """

    results = []

    for r in reviews_clean:
        text = r["text"]

        matched_aspects = [
            a for a in aspects if a in text
        ]

        if not matched_aspects:
            continue

        sentiment = detect_sentiment(text)

        results.append({
            "text": text,
            "aspects": matched_aspects,
            "sentiment": sentiment
        })

    return results
