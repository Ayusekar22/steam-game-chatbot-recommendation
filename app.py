import re
import os
import requests
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# =============================
# LOAD ENV & INIT OPENAI CLIENT
# =============================
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-5-nano"

# =============================
# IMPORT PIPELINE MODULES
# =============================
from src.Steam_Data.Scrapping_Reviews import fetch_steam_reviews
from src.Steam_Data.Preprocessing import clean_reviews

from src.RAG.chunking import (
    build_review_chunks,
    build_steam_page_chunks
)
from src.RAG.retrieval import retrieve_chunks

# =============================
# HELPERS
# =============================
def extract_appid(steam_url: str):
    match = re.search(r"/app/(\d+)", steam_url)
    return match.group(1) if match else None


def fetch_steam_game_data(appid: str):
    url = "https://store.steampowered.com/api/appdetails"
    params = {"appids": appid}

    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()

        if data.get(appid, {}).get("success"):
            game = data[appid]["data"]

            genres = [g["description"] for g in game.get("genres", [])]
            categories = game.get("categories", [])

            player_modes = []
            for c in categories:
                desc = c.get("description", "")
                if "Single-player" in desc:
                    player_modes.append("Single-player")
                if "Multi-player" in desc:
                    player_modes.append("Multiplayer")
                if "Co-op" in desc:
                    player_modes.append("Co-op")

            return {
                "title": game.get("name", "Unknown Game"),
                "genres": genres,
                "player_modes": list(set(player_modes)),
                "description": game.get("short_description", "")
            }

    except Exception:
        pass

    return {
        "title": "Unknown Game",
        "genres": [],
        "player_modes": [],
        "description": ""
    }


def llm(prompt: str) -> str:
    res = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You are a Steam game analysis assistant."},
            {"role": "user", "content": prompt}
        ],
    )
    return res.choices[0].message.content.strip()


def llm_rag(chunks, user_question):
    context = "\n\n".join([c["content"] for c in chunks])

    prompt = f"""
You are a friendly and helpful Steam game assistant.

You are answering STRICTLY based on the provided Steam reviews.
You do not know anything about the game except what is written in the reviews.
If the information is not present in the reviews, answer:
"Not enough information from the reviews."

Do NOT use outside knowledge.

Context:
{context}

Question:
{user_question}

Answer:
"""
    return llm(prompt)

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(
    page_title="🎮 Steam Game Chatbot",
    page_icon="🎮",
    layout="centered"
)

st.title("🎮 Steam Game Chatbot")
st.caption("Paste a Steam game link, then ask anything about the game")

# =============================
# SESSION STATE
# =============================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "data" not in st.session_state:
    st.session_state.data = None

# =============================
# DISPLAY CHAT HISTORY
# =============================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =============================
# USER INPUT
# =============================
user_input = st.chat_input("Paste Steam link or ask about the game...")

if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Processing..."):

            reply = ""
            appid = extract_appid(user_input)

            # =============================
            # CASE 1: STEAM LINK
            # =============================
            if appid:
                try:
                    # 1️⃣ Steam page info
                    steam_page_data = fetch_steam_game_data(appid)
                    game_title = steam_page_data["title"]

                    # 2️⃣ Reviews
                    reviews_raw = fetch_steam_reviews(appid, max_reviews=1000)
                    reviews_clean = clean_reviews(reviews_raw)

                    # 3️⃣ Build chunks
                    review_chunks = build_review_chunks(reviews_clean)
                    steam_chunks = build_steam_page_chunks(steam_page_data)
                    all_chunks = review_chunks + steam_chunks

                    # 🚀 4️⃣ EMBEDDING BATCH (FAST)
                    texts = [c["content"] for c in all_chunks]

                    embeddings = client.embeddings.create(
                        model=EMBEDDING_MODEL,
                        input=texts
                    ).data

                    for c, e in zip(all_chunks, embeddings):
                        c["embedding"] = e.embedding

                    # 5️⃣ Save
                    st.session_state.data = {
                        "appid": appid,
                        "game_title": game_title,
                        "rag_chunks": all_chunks
                    }

                    reply = f"""
✅ **{game_title} — Game data loaded successfully**

📄 Raw reviews   : {len(reviews_raw)}
🧹 Clean reviews : {len(reviews_clean)}
📦 RAG chunks    : {len(all_chunks)}

You can now ask:
- Is it relaxing?
- Can I play with friends?
- Are players happy with the gameplay?
"""

                except Exception as e:
                    reply = f"❌ Error during processing:\n\n{e}"

            # =============================
            # CASE 2: USER QUESTION
            # =============================
            elif st.session_state.data:
                chunks = st.session_state.data["rag_chunks"]
                top_chunks = retrieve_chunks(user_input, chunks, top_k=6)
                reply = llm_rag(top_chunks, user_input)

            else:
                reply = "👋 Please paste a valid Steam store link first."

            st.markdown(reply)

    st.session_state.messages.append({
        "role": "assistant",
        "content": reply
    })
