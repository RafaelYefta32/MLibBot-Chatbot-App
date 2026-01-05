## Cara Menjalankan Backend

### Backend
#### Masuk ke folder backend
1. Buat environment (Conda)
   	conda create -n mlibbot2 python=3.10 -y

2. Activate environment
	conda activate mlibbot2

3. Install dependency dasar via conda
	conda install -n mlibbot2 -c conda-forge "spacy>=3.7,<3.8" "numpy>=1.23,<2.0" pandas scipy scikit-learn -y

4. Upgrade pip
	python -m pip install --upgrade pip

5. Install dependencies dari requirements
	pip install -r requirements.txt	

6. Install FAISS (CPU)
	conda install -n mlibbot2 -c pytorch faiss-cpu -y

7. Install PyTorch versi CPU
	pip install torch --index-url https://download.pytorch.org/whl/cpu

8. Install dependency tambahan
	pip install motor passlib[bcrypt] python-jose python-multipart 'pydantic[email]' 'bcrypt==4.0.1'

9. Buat file .env
	Jangan lupa buat file .env (lihat contoh di .env.example)

#### Run backend
	python ingest.py
	uvicorn main:app --reload --port 8000

### Frontend
#### Masuk ke folder frontend
1. Install dependency
	npm install 

#### Run frontend
	npm run dev