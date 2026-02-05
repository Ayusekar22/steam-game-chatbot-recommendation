def build_aspect_chunks(absa_results, max_chars=300):
    """
    Build RAG-ready chunks from ABSA results
    """

    chunks = []

    for item in absa_results:
        text = item["text"]
        sentiment = item["sentiment"]

        for aspect in item["aspects"]:
            chunk_text = f"""
Aspect: {aspect}
Sentiment: {sentiment}
Review: {text}
""".strip()

            if len(chunk_text) > max_chars:
                chunk_text = chunk_text[:max_chars]

            chunks.append({
                "aspect": aspect,
                "sentiment": sentiment,
                "content": chunk_text
            })

    return chunks

def build_steam_page_chunks(steam_page_data):
    """
    Build RAG chunks from Steam page info (factual knowledge)
    """

    chunk_text = f"""
[STEAM PAGE INFO]
Title: {steam_page_data.get("title")}

Genres:
{", ".join(steam_page_data.get("genres", []))}

Tags:
{", ".join(steam_page_data.get("tags", []))}

Player Modes:
{", ".join(steam_page_data.get("player_modes", []))}

Description:
{steam_page_data.get("description")}
""".strip()

    return [{
        "aspect": "steam_page",
        "sentiment": "neutral",
        "content": chunk_text
    }]


def build_review_chunks(reviews, max_chars=300):
    """
    Build RAG-ready chunks from cleaned Steam reviews
    Works with:
    - list[str]
    - list[dict] with unknown keys
    """

    chunks = []

    for r in reviews:
        # 1️⃣ Jika string (PALING AMAN)
        if isinstance(r, str):
            text = r

        # 2️⃣ Jika dict, ambil SEMUA value string
        elif isinstance(r, dict):
            text = " ".join(
                str(v) for v in r.values() if isinstance(v, str)
            )

        else:
            continue

        text = text.strip()
        if not text:
            continue

        chunk_text = f"[STEAM REVIEW]\n{text}"

        if len(chunk_text) > max_chars:
            chunk_text = chunk_text[:max_chars]

        chunks.append({
            "content": chunk_text
        })

    return chunks
