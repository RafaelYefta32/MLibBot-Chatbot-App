import json, requests
from pathlib import Path
import pandas as pd

url = "http://127.0.0.1:8000/test/compare"
# query = ["Carikan Buku Natural Language Processing",
#          "Jam Layanan Perpustakaan",
#          "Bisa Carikan buku yang terbit tahun 2020?",
#          "Apa saja layanan yang disediakan di Perpustakaan?",
#          "Aku mau nanya aturan perpustakaan dong",
#          "Perpustakaan maranatha itu letaknya dimana?",
#          "Alamat lengkap perpustakaan uk maranatha dimana ya?", 
#          "Email perpustakaan maranatha apa ya?",
#          "Kalau mau tanya pustakawan, kontaknya yang paling cepat apa?",
#          "Perpus buka jam berapa hari ini?",
#          "Jam layanan senin sampai jumat sampai jam berapa?",
# ]
df = pd.read_excel("eval.xlsx")
query = (df["query"])
s = requests.Session()
results = []
for i, q in enumerate(query, 1):
    print(i, q)
    results.append(s.post(url, json={"message": q, "top_k": 4, "method": "hybrid"}).json())

Path("hasil_retrive_eval_fix.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"items={len(results)}")