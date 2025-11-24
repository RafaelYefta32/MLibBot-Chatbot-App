import os
import requests
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("groq_api")

def build_prompt(question: str, contexts: list) -> str:
    context_texts = "\n\n".join(
        [
            f"- {c['text']}\n(Sumber: {c['source']} / {c['source_id']})"
            for c in contexts
        ]
    )

    prompt = f"""
Anda adalah chatbot perpustakaan yang memberi jawaban berdasarkan dokumen yang tersedia.

Gunakan INFORMASI berikut untuk menjawab pertanyaan:

{context_texts}

Pertanyaan:
{question}

Jika informasi tidak ada di konteks, jawab bahwa informasinya tidak tersedia.
"""
    return prompt.strip()

def call_groq(prompt: str, model: str = "llama-3.1-8b-instant") -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("APi nya woy belumd dibikin")

    url = "https://api.groq.com/openai/v1/chat/completions"

    system_content = (
        "Kamu adalah MLibBot, chatbot perpustakaan Universitas Kristen Maranatha. "
        "Jawab dalam bahasa Indonesia yang singkat, jelas, dan langsung ke inti. "
        "Untuk pertanyaan faktual (misalnya jam buka, lokasi, nomor kontak, jumlah hari keterlambatan, dll.), "
        "langsung berikan jawabannya di kalimat pertama. "
        "Jika perlu, tambahkan maksimal satu kalimat penjelasan tambahan. "
        "JANGAN menyebut-nyebut 'dokumen', 'bagian dokumen', 'informasi dapat ditemukan pada', "
        "atau mengutip teks panjang apa adanya. "
        "Jawab hanya berdasarkan konteks yang diberikan. "
        "Jika informasi yang diminta tidak ada dalam konteks, jawab dengan sopan bahwa informasi tersebut tidak tersedia."
    )

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_content,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.2,
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()
