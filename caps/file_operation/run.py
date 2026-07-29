# 开发者：自由的风
"""file_operation/run.py — 文件系统操作
=======================================
AI编程 ready — 读/写/复制/移动/删除/搜索/加密文件。
"""
import sys, json, os, shutil, fnmatch, hashlib, base64
from pathlib import Path
from datetime import datetime

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def do_read(params):
    path = params.get("path", params.get("file", ""))
    if not path: return {"ok": False, "error": "缺少path"}
    try:
        p = Path(path)
        if p.is_dir():
            items = [{"name": i.name, "type": "dir" if i.is_dir() else "file", "size": i.stat().st_size if i.is_file() else 0} for i in sorted(p.iterdir())[:50]]
            return {"ok": True, "cap": "file_operation", "action": "read", "is_dir": True, "items": items, "count": len(items)}
        content = p.read_text(encoding="utf-8", errors="replace")
        return {"ok": True, "is_dir": False, "path": str(p), "size": len(content), "content": content[:5000], "lines": content.count(chr(10))}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def do_write(params):
    path, content = params.get("path",""), params.get("content","")
    if not path: return {"ok": False, "error": "缺少path"}
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content, encoding="utf-8")
        return {"ok": True, "cap": "file_operation", "action": "write", "path": path, "size": len(content)}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def do_copy(params):
    src, dst = params.get("src",""), params.get("dst","")
    if not src or not dst: return {"ok": False, "error": "缺少src或dst"}
    try:
        if Path(src).is_dir(): shutil.copytree(src, dst, dirs_exist_ok=True)
        else: shutil.copy2(src, dst)
        return {"ok": True, "copied": str(dst)}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def do_delete(params):
    path = params.get("path","")
    if not path: return {"ok": False, "error": "缺少path"}
    try:
        p = Path(path)
        if p.is_dir(): shutil.rmtree(p)
        else: p.unlink()
        return {"ok": True, "deleted": str(p)}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def do_search(params):
    root = params.get("root", ".")
    pattern = params.get("pattern", "*")
    max_results = params.get("limit", 50)
    results = []
    try:
        for p in Path(root).rglob(pattern):
            if p.is_file() and not any(x in str(p) for x in [".git","__pycache__","node_modules"]):
                results.append({"path": str(p), "size": p.stat().st_size, "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat()})
            if len(results) >= max_results: break
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
    return {"ok": True, "found": len(results), "results": results}

def do_encrypt(params):
    path, key = params.get("path",""), params.get("key","gbt-default")
    if not path: return {"ok": False, "error": "缺少path"}
    try:
        data = Path(path).read_bytes()
        key_hash = hashlib.sha256(key.encode()).digest()
        encrypted = bytes([data[i] ^ key_hash[i % len(key_hash)] for i in range(len(data))])
        out = path + ".gbtenc"
        Path(out).write_bytes(encrypted)
        return {"ok": True, "encrypted": out, "size": len(encrypted)}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

HANDLERS = {"read": do_read, "write": do_write, "copy": do_copy, "delete": do_delete, "search": do_search, "encrypt": do_encrypt}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "read"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
