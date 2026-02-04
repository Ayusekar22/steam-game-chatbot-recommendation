import requests
import time


def fetch_steam_reviews(
    appid: int,
    max_reviews: int = 1000,
    language: str = "english"
):
    """
    Fetch RAW Steam reviews using Steam Reviews API
    """

    reviews = []
    cursor = "*"

    while len(reviews) < max_reviews:
        url = f"https://store.steampowered.com/appreviews/{appid}"
        params = {
            "json": 1,
            "filter": "recent",
            "language": language,
            "review_type": "all",
            "purchase_type": "all",
            "num_per_page": 100,
            "cursor": cursor
        }

        response = requests.get(url, params=params)
        data = response.json()

        if "reviews" not in data or len(data["reviews"]) == 0:
            break

        for r in data["reviews"]:
            reviews.append({
                "review": r.get("review"),
                "recommended": r.get("voted_up"),
                "playtime_hours": r.get("author", {}).get("playtime_forever", 0) / 60,
                "votes_up": r.get("votes_up"),
                "votes_funny": r.get("votes_funny"),
                "timestamp": r.get("timestamp_created")
            })

            if len(reviews) >= max_reviews:
                break

        cursor = data.get("cursor")
        time.sleep(0.3)  # biar aman (rate limit friendly)

    return reviews
