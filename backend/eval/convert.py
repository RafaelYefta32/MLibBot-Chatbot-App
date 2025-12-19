import json
import pandas as pd
from pathlib import Path
mapping = {
    "bm25": "bm25",
    "faiss_indobert": "faiss",
    "hybrid": "hybrid",
}
inp = "hasil_retrive_eval_fix.json"
out = "hasil_retrive_eval_fix.xlsx"
query_objs = json.loads(Path(inp).read_text(encoding="utf-8"))

rows = []
for qid, qobj in enumerate(query_objs, start = 1):
    query_text = qobj.get("query", "")
    for key, method_name in mapping.items():
        for rank, hit in enumerate(qobj.get(key, []), start=1):
            text_val = hit.get("text", "") or ""
            rows.append({
                "qid": qid,
                "query": query_text,
                "type": hit.get("source", ""),
                "method": method_name,
                "rank": rank,
                "source_id": hit.get("source_id", ""),
                "text": text_val,
                "label": "",
            })

pd.DataFrame(rows).to_excel(out, index=False)
print(f"rows={len(rows)}")