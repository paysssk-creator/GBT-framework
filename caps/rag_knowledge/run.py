# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""rag_knowledge — 本地轻量知识库"""
import sys, json, os, hashlib, re, sqlite3
from pathlib import Path
from datetime import datetime, timezone

KB_DIR = Path.home() / ".gbt" / "knowledge"
KB_DIR.mkdir(parents=True, exist_ok=True)
DB = str(KB_DIR / "kb.db")

def _db():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS docs (id TEXT PRIMARY KEY, source TEXT, title TEXT, content TEXT, chunk_idx INTEGER, created TEXT)")
    c.execute("CREATE INDEX IF NOT EXISTS i_src ON docs(source)")
    return c

def _h(t): return hashlib.md5(t.encode()).hexdigest()[:12]

def _chunk(text, n=800):
    ss = re.split(r'(?<=[。.!！?？\n])\s*', text)
    chunks, cur = [], ""
    for s in ss:
        if len(cur)+len(s)>n and cur: chunks.append(cur.strip()); cur=s
        else: cur+=s
    if cur.strip(): chunks.append(cur.strip())
    return chunks or [text]

def do_ingest(p):
    path = p.get("path","")
    if not path: return {"ok":False,"error":"need path"}
    src = Path(path)
    if not src.exists(): return {"ok":False,"error":f"not found: {path}"}
    db = _db(); n = 0
    fs = list(src.rglob("*.py"))+list(src.rglob("*.md"))+list(src.rglob("*.txt"))
    for f in fs[:200]:
        try:
            txt = f.read_text(encoding="utf-8",errors="ignore")
            if len(txt)<10: continue
            for i,c in enumerate(_chunk(txt)):
                db.execute("INSERT OR REPLACE INTO docs VALUES(?,?,?,?,?,?)",
                    (_h(f"{f}_{i}"), str(src), f.name, c, i, datetime.now(timezone.utc).isoformat()))
                n+=1
        except Exception as e:
            pass
    db.commit(); db.close()
    return {"ok":True,"ingested":n,"source":str(src)}

def do_search(p):
    q = p.get("q","")
    if not q: return {"ok":False,"error":"need q"}
    db = _db(); ws = q.lower().split(); rs = []
    for r in db.execute("SELECT id,source,title,content FROM docs"):
        sc = sum(1 for w in ws if w in r[3].lower())
        if sc>0: rs.append({"id":r[0],"source":r[1],"title":r[2],"snippet":r[3][:300],"score":sc})
    rs.sort(key=lambda x:-x["score"]); db.close()
    return {"ok":True,"query":q,"found":len(rs),"results":rs[:5]}

def do_ask(p):
    q = p.get("q","")
    if not q: return {"ok":False,"error":"need q"}
    sr = do_search({"q":q})
    if not sr["results"]: return {"ok":True,"answer":"No matches in knowledge base","sources":[]}
    ctx = "\n\n".join(r["snippet"] for r in sr["results"])
    prompt = f"Answer based on this knowledge:\n{ctx[:3000]}\n\nQuestion: {q}\nAnswer in Chinese:"
    try:
        from intent_broker import _call_llm
        ans = _call_llm([{"role":"user","content":prompt}], max_tokens=500)
    except:
        ans = f"Found {sr['found']} docs (LLM unavailable)"
    return {"ok":True,"answer":(ans or "").strip(),"sources":[{"t":r["title"],"s":r["snippet"][:100]} for r in sr["results"]]}

def do_learn(p):
    return do_ingest({"path": p.get("project", str(Path.home()/"GBT-JXDWD"/"sandbox"))})

def do_status(p=None):
    db = _db(); n = db.execute("SELECT COUNT(*) FROM docs").fetchone()[0]; db.close()
    return {"ok":True,"total":n,"db":DB}

HANDLERS = {"ingest":do_ingest,"search":do_search,"ask":do_ask,"learn":do_learn,"status":do_status}

if __name__=="__main__":
    a = sys.argv[-1].lstrip("-") if len(sys.argv)>1 and sys.argv[-1]!="run.py" else "status"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = HANDLERS.get(a, lambda p:{"ok":False,"error":f"unknown:{a}"})
    print(json.dumps(h(params), ensure_ascii=False, default=str))

