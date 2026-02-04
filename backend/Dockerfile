# Gunakan image Python yang ringan
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (jika ada library yang butuh build tools)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements dan install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh code ke container
COPY . .

# Buat user non-root (syarat keamanan Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Expose port (Hugging Face biasanya listen di 7860, tapi kita bisa setting)
# CMD akan dijalankan oleh HF
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
