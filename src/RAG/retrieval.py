import os
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBEDDING_MODEL = "text-embedding-3-small"


def retrieve_chunks(query, chunks, top_k=5):
    """
    query  : str (user question)
    chunks : list of dict, each has 'content' and 'embedding'
    """

    # 1️⃣ embed query
    query_embedding = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query
    ).data[0].embedding

    # 2️⃣ ambil embedding chunks
    chunk_embeddings = np.array([c["embedding"] for c in chunks])

    # 3️⃣ cosine similarity
    similarities = cosine_similarity(
        [query_embedding],
        chunk_embeddings
    )[0]

    # 4️⃣ ambil top-k
    top_indices = similarities.argsort()[-top_k:][::-1]

    return [chunks[i] for i in top_indices]
