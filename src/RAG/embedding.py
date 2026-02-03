import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBEDDING_MODEL = "text-embedding-3-small"

def embed_chunks(chunks):
    """
    Input: list of dict, tiap dict = {aspect, sentiment, content}
    Output: chunks + embeddings
    """
    texts = [c["content"] for c in chunks]  # ambil text tiap chunk
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    embeddings = [item.embedding for item in response.data]

    for c, e in zip(chunks, embeddings):
        c["embedding"] = e  # attach embedding ke chunk

    return chunks
