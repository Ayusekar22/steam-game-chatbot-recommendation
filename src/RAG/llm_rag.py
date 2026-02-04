from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def llm(prompt: str) -> str:
    res = client.chat.completions.create(
        model="gpt-5-nano",
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
Answer the user's question ONLY based on the following review context.
Do not include any information not present in the context.
Be concise and clear.

Context:
{context}

Question:
{user_question}

Answer:
"""
    return llm(prompt)
