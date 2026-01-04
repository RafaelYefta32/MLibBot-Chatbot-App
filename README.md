Cara Menjalankan Backend:
- Backend
  1. Buat Virtual Environment
     - python -m venv venv
     Jalankan Virtual Environment:
     - venv\Scripts\activate
  2. Install Dependencies
     - pip install -r requirements.txt
  # 3. Ollama (LLM Lokal) -> optional untuk Local (karena default pakai groq jadi tidak usah)
     - Download Ollama (https://ollama.com/download)
     - ollama pull qwen2.5:1.5b
  # 4. Pindah Cache ke D (optional)
     - buat folder dengan nama "model embedding" di D (D:\model_embeddings)
     - jika tidak ingin di D, komentarkan bagian "os.environ["SENTENCE_TRANSFORMERS_HOME"] = "D:/model embedding"" di file ingest.py
  5. lakukan ingest (embedding)
     - masuk ke folder backend
     - jalankan "python ingest.py"
  6. Jalankan Backend FastAPI
     - uvicorn main:app --reload --port 8000
  7. Test
     - contoh : jalankan http://localhost:8000/test/ask?q=jam%20operasional%20perpustakaan
     - bisa ganti bagian q=... 

Cara Menjalankan Frontend:
- Frontend
  1. Masuk ke folder frontend
  2. Install Dependencies
     - npm install
  3. Jalankan Frontend
     - npm run dev