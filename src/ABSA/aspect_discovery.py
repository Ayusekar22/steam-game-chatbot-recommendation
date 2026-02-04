from collections import Counter
import re


def extract_candidate_aspects(reviews_clean, top_k=10):
    """
    Discover aspect candidates dynamically from reviews
    """

    noun_candidates = []

    for r in reviews_clean:
        text = r["text"]

        # simple noun heuristic: words after 'the', 'this', 'game'
        tokens = re.findall(r"\b[a-z]{3,}\b", text)

        noun_candidates.extend(tokens)

    counter = Counter(noun_candidates)

    # remove very generic words
    stop_aspects = {
        "game", "games", "play", "playing", "time", "one",
        "really", "good", "bad", "great", "fun"
    }

    aspects = [
        word for word, _ in counter.most_common(top_k * 2)
        if word not in stop_aspects
    ]

    return aspects[:top_k]
