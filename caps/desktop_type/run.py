# 开发者：自由的风
'''desktop_type/run.py — 桌面输入自动化'''
import sys, json

def do_type(params):
    text = params.get("text", "")
    interval = params.get("interval", 0.03)
    try:
        import pyautogui
        pyautogui.typewrite(text, interval=interval)
        return {"ok": True, "cap": "desktop_type", "action": "type", "text_len": len(text), "interval": interval}
    except ImportError:
        return {"ok": False, "error": "pyautogui未安装"}

def do_fill(params):
    fields = params.get("fields", {})
    try:
        import pyautogui
        for selector, value in fields.items():
            pyautogui.typewrite(str(value), interval=0.03)
            pyautogui.press("tab")
        return {"ok": True, "cap": "desktop_type", "action": "fill", "fields": len(fields)}
    except ImportError:
        return {"ok": False, "error": "pyautogui未安装"}

HANDLERS = {"type": do_type, "fill": do_fill}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "type"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
