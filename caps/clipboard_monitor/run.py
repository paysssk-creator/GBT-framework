# 开发者：自由的风
"""clipboard_monitor/run.py — 剪贴板监控
========================================
桌面域 ready — 持续监控剪贴板变化,捕获复制的密码/密钥/文本。
"""
import sys, json, os, time, threading
from pathlib import Path

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = Path.home() / ".gbt" / "clipboard"
LOG_DIR.mkdir(parents=True, exist_ok=True)
_monitor = {"active": False, "thread": None, "last": "", "history": []}

def do_start(params):
    global _monitor
    if _monitor["active"]:
        return {"ok": True, "status": "already_running"}
    interval = params.get("interval", 1)
    def _poll():
        while _monitor["active"]:
            try:
                import pyperclip
                txt = pyperclip.paste()
                if txt and txt != _monitor["last"] and len(txt) < 10000:
                    _monitor["last"] = txt
                    _monitor["history"].append({"text": txt[:500], "time": time.time(), "len": len(txt)})
                time.sleep(interval)
            except: time.sleep(interval)
    try: import pyperclip
    except ImportError: return {"ok": False, "error": "pyperclip未安装"}
    _monitor["active"] = True
    t = threading.Thread(target=_poll, daemon=True); t.start()
    _monitor["thread"] = t
    return {"ok": True, "cap": "clipboard_monitor", "action": "start", "domain": "桌面域"}

def do_stop(params):
    _monitor["active"] = False
    return {"ok": True, "history": len(_monitor["history"]), "recent": _monitor["history"][-5:]}

def do_dump(params):
    return {"ok": True, "active": _monitor["active"], "total": len(_monitor["history"]),
            "history": _monitor["history"][-20:]}

HANDLERS = {"start": do_start, "stop": do_stop, "dump": do_dump}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "dump"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
