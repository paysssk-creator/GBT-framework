# 开发者：自由的风
"""screenpipe_monitor/run.py — 持续屏幕变化感知
==============================================
感知域 ready — 轮询截图+OCR，检测屏幕内容变化。
作为守护进程运行，持续感知。
"""
import sys, json, os, time, threading
from pathlib import Path

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPS_DIR = Path(SANDBOX) / "caps"
STATE_FILE = Path.home() / ".gbt" / "screenpipe_state.json"

_global_monitor = {"running": False, "thread": None, "changes": [], "last_text": ""}


def _call_cap(cap_id, action, params, timeout=15):
    import subprocess
    run_py = CAPS_DIR / cap_id / "run.py"
    if not run_py.exists():
        return {}
    try:
        r = subprocess.run(
            [sys.executable, str(run_py), action, json.dumps(params, ensure_ascii=False)],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(SANDBOX), encoding="utf-8", errors="replace"
        )
        return json.loads((r.stdout or "{}").strip())
    except Exception:
        return {}


def _monitor_loop(interval, region):
    """监控循环 — 在独立线程中运行"""
    while _global_monitor["running"]:
        try:
            result = _call_cap("screen_ocr", "read", {
                "left": region.get("left", 0),
                "top": region.get("top", 0),
                "width": region.get("width", 1920),
                "height": region.get("height", 1080),
                "lang": "chi_sim+eng",
            })

            if result.get("ok"):
                current_text = result.get("text", "")
                if current_text != _global_monitor["last_text"]:
                    _global_monitor["changes"].append({
                        "timestamp": time.time(),
                        "text": current_text[:500],
                        "line_count": result.get("line_count", 0),
                    })
                    _global_monitor["last_text"] = current_text
                    # 只保留最近100条变化
                    if len(_global_monitor["changes"]) > 100:
                        _global_monitor["changes"] = _global_monitor["changes"][-100:]

        except Exception:
            pass

        time.sleep(interval)


def do_start(params):
    """启动持续监控"""
    global _global_monitor
    if _global_monitor["running"]:
        return {"ok": True, "cap": "screenpipe_monitor", "action": "start",
                "status": "already_running", "changes_count": len(_global_monitor["changes"])}

    interval = params.get("interval", 2.0)  # 默认2秒轮询
    region = {
        "left": params.get("left", 0),
        "top": params.get("top", 0),
        "width": params.get("width", 1920),
        "height": params.get("height", 1080),
    }

    _global_monitor["running"] = True
    _global_monitor["changes"] = []
    _global_monitor["last_text"] = ""

    thread = threading.Thread(target=_monitor_loop, args=(interval, region), daemon=True)
    thread.start()
    _global_monitor["thread"] = thread

    return {
        "ok": True,
        "cap": "screenpipe_monitor",
        "action": "start",
        "domain": "感知域",
        "status": "started",
        "interval_sec": interval,
        "region": region,
    }


def do_stop(params):
    """停止监控"""
    global _global_monitor
    _global_monitor["running"] = False

    changes = list(_global_monitor["changes"])
    _global_monitor["changes"] = []

    return {
        "ok": True,
        "cap": "screenpipe_monitor",
        "action": "stop",
        "domain": "感知域",
        "status": "stopped",
        "total_changes": len(changes),
        "changes": changes[-20:],  # 返回最近20条
    }


def do_status(params):
    """查看监控状态"""
    return {
        "ok": True,
        "cap": "screenpipe_monitor",
        "action": "status",
        "domain": "感知域",
        "running": _global_monitor["running"],
        "changes_count": len(_global_monitor["changes"]),
        "last_change": _global_monitor["changes"][-1] if _global_monitor["changes"] else None,
    }


HANDLERS = {"start": do_start, "stop": do_stop, "status": do_status}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "status"
    params_str = sys.argv[2] if len(sys.argv) > 2 else "{}"
    try:
        params = json.loads(params_str)
    except Exception:
        params = {}
    handler = HANDLERS.get(action)
    if handler:
        result = handler(params)
        print(json.dumps(result, ensure_ascii=False, default=str))
    else:
        print(json.dumps({"ok": False, "error": f"未知动作: {action}", "available": list(HANDLERS.keys())}, ensure_ascii=False))
