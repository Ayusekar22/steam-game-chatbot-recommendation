import re
import streamlit as st
import os
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
# IMPORT FUNCTIONALITY
# =============================

from src.Steam_Data.Scrapping_Reviews import fetch_steam_reviews
from src.Steam_Data.Preprocessing import clean_reviews, clean_text
from src.ABSA.aspect_discovery import extract_candidate_aspects
from src.ABSA.aspect_sentiment import assign_aspects
from src.RAG.chunking import build_aspect_chunks
from src.RAG.embedding import embed_chunks
from src.RAG.retrieval import retrieve_chunks

# =============================
# HELPER
# =============================
def extract_appid(steam_url: str):
    match = re.search(r"/app/(\d+)", steam_url)
    return match.group(1) if match else None

def llm(prompt: str) -> str:
    res = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You are a Steam game review analysis assistant."},
            {"role": "user", "content": prompt}
        ],
    )
    return res.choices[0].message.content.strip()

def llm_rag(chunks, user_question):
    context = "\n\n".join([c["content"] for c in chunks])
    prompt = f"""
You are a Steam game review assistant.
Answer the user's question ONLY based on the given review context.
Do not add information not present in the context.
Be concise and clear.

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
st.set_page_config(page_title="🎮 Steam Game Chatbot", page_icon="🎮", layout="centered")
st.title("🎮 Steam Game Chatbot")
st.caption("Paste a Steam link to start, then ask anything about the game")

# =============================
# SESSION STATE
# =============================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "data" not in st.session_state:
    st.session_state.data = None

# =============================
# DISPLAY CHAT
# =============================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =============================
# USER INPUT
# =============================
user_input = st.chat_input("Paste Steam link or ask about the game...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

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
                    # 1️⃣ fetch reviews
                    reviews_raw = fetch_steam_reviews(appid, max_reviews=500)

                    # 2️⃣ clean reviews
                    reviews_clean = clean_reviews(reviews_raw)

                    # 3️⃣ dynamic ABSA
                    candidate_aspects = extract_candidate_aspects(reviews_clean)
                    absa_results = assign_aspects(reviews_clean, candidate_aspects)

                    # 4️⃣ build chunks
                    chunks = build_aspect_chunks(absa_results)

                    # 5️⃣ embed chunks
                    chunks = embed_chunks(chunks)

                    # save to session
                    st.session_state.data = {
                        "appid": appid,
                        "reviews_raw": reviews_raw,
                        "reviews_clean": reviews_clean,
                        "absa_results": absa_results,
                        "rag_chunks": chunks
                    }

                    reply = f"""
✅ **Game data and reviews loaded!**

📄 Raw reviews   : {len(reviews_raw)}
🧹 Clean reviews : {len(reviews_clean)}
🔍 Aspects found : {len(candidate_aspects)}
💾 Chunks created : {len(chunks)}

You can now ask questions about the game, e.g.:
- How is performance?
- Are there bugs?
- Is it relaxing?
"""
                except Exception as e:
                    reply = f"❌ Failed to fetch or process reviews: {e}"

            # =============================
            # CASE 2: USER QUERY
            # =============================
            elif st.session_state.data and "rag_chunks" in st.session_state.data:
                chunks = st.session_state.data["rag_chunks"]
                top_chunks = retrieve_chunks(user_input, chunks, top_k=5)
                answer = llm_rag(top_chunks, user_input)
                reply = answer

            else:
                reply = "👋 Please paste a valid Steam store link first."

            st.markdown(reply)

    # =============================
    # SAVE BOT MESSAGE
    # =============================
    st.session_state.messages.append({"role": "assistant", "content": reply})
