Cara Menjalankan Backend:
- Backend
  1. Buat Virtual Environment
     - python -m venv venv
     Jalankan Virtual Environment:
     - venv\Scripts\activate
  2. Install Dependencies
     - pip install -r requirements.txt
  3. Ollama (LLM Lokal)
     - Download Ollama (https://ollama.com/download)
     - ollama pull qwen2.5:1.5b
  4. Pindah Cache ke D (optional )
     - buat folder dengan nama "model embedding" di D (D:\model_embeddings)
     - jika tidak ingin di D, komentarkan bagian "os.environ["SENTENCE_TRANSFORMERS_HOME"] = "D:/model embedding"" di file ingest.py
  5. lakukan ingest (embedding)
     - masuk ke folder backend
     - jalankan "python ingest.py"
  6. Jalankan Backend FastAPI
     - uvicorn main:app --reload --port 8000
