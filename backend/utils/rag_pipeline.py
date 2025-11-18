# utils/rag_pipeline.py

import subprocess

def build_prompt(question: str, contexts: list) -> str:
    """Menyusun prompt untuk RAG."""
    context_texts = "\n\n".join(
        [f"- {c['text']}\n(Sumber: {c['source']} / {c['source_id']})"
         for c in contexts]
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


def call_ollama(prompt: str, model: str = "qwen2.5:0.5b") -> str:
    """Memanggil Ollama model ringan qwen2.5:0.5b."""
    cmd = ["ollama", "run", model]

    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    out, err = process.communicate(prompt)

    if err and "error" in err.lower():
        print("OLLAMA ERROR:", err)

    return out.strip()
