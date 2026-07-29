# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""remote_control/run.py — GBT远程操控接入点
用户端: agent.py (暴露服务)
GBT端: connect.py (接入操控)
本文件: CLI统一入口
"""
import sys, json, os, subprocess
from pathlib import Path

SANDBOX = Path(__file__).parent

def do_scan_services(params=None):
    r = subprocess.run([sys.executable, str(SANDBOX / "agent.py"), "scan"], capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace")
    try: return json.loads(r.stdout)
    except: return {"ok": True, "raw": r.stdout[:2000]}

def do_expose_port(params):
    port = params.get("port", 8080) if params else 8080
    r = subprocess.run([sys.executable, str(SANDBOX / "agent.py"), "expose", str(port)], capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
    try: return json.loads(r.stdout)
    except: return {"ok": True, "raw": r.stdout[:2000]}

def do_connect(params):
    url = params.get("url", "") if params else ""
    r = subprocess.run([sys.executable, str(SANDBOX / "connect.py"), url], capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
    try: return json.loads(r.stdout)
    except: return {"ok": True, "raw": r.stdout[:2000]}

def do_status(params=None):
    files = list(SANDBOX.glob("*.py"))
    return {"ok": True, "cap": "remote_control", "files": [f.name for f in files], "ready": all(f.exists() for f in [SANDBOX/"agent.py", SANDBOX/"connect.py"])}

HANDLERS = {"scan": do_scan_services, "expose": do_expose_port, "connect": do_connect, "status": do_status, "run": do_status}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "status"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知:{action}"})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
