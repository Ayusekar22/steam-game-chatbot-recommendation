
import re


def clean_text(text: str) -> str:
    if not text:
        return ""

    # lowercase
    text = text.lower()

    # remove urls
    text = re.sub(r"http\S+|www\S+", "", text)

    # remove html tags
    text = re.sub(r"<.*?>", "", text)

    # remove non-ascii (emoji, symbols)
    text = re.sub(r"[^\x00-\x7F]+", " ", text)

    # keep only letters, numbers, basic punctuation
    text = re.sub(r"[^a-z0-9\s.,!?']", " ", text)

    # normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def clean_reviews(reviews_raw, min_length: int = 5):
    """
    Input  : list of raw review dicts
    Output : list of cleaned review dicts
    """

    cleaned = []

    for r in reviews_raw:
        cleaned_text = clean_text(r.get("review", ""))

        if len(cleaned_text.split()) < min_length:
            continue

        cleaned.append({
            "text": cleaned_text,
            "recommended": r.get("recommended"),
            "playtime_hours": r.get("playtime_hours"),
            "votes_up": r.get("votes_up"),
            "timestamp": r.get("timestamp")
        })

    return cleaned
