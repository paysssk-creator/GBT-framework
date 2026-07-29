# 开发者：自由的风
'''sys_control/run.py — 16类跨平台系统操控'''
import sys, json, os, subprocess, ctypes

def do_control(params):
    action = params.get("op", params.get("action", "info"))
    result = {"ok": True, "cap": "sys_control", "domain": "桌面域"}
    try:
        if action == "keyboard":
            import pyautogui
            pyautogui.hotkey(*params.get("keys", ["ctrl", "c"]))
            result["keys"] = params.get("keys")
        elif action == "mouse_move":
            import pyautogui
            pyautogui.moveTo(params.get("x", 0), params.get("y", 0))
        elif action == "window_list":
            if sys.platform == "win32":
                r = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True)
                result["windows"] = r.stdout[:1000]
        elif action == "lock":
            if sys.platform == "win32":
                ctypes.windll.user32.LockWorkStation()
        elif action == "volume":
            import pyautogui
            for _ in range(params.get("delta", 0)):
                pyautogui.press("volumeup" if params.get("up", True) else "volumedown")
        result["action"] = action
    except ImportError:
        result["error"] = "pyautogui未安装"
    except Exception as e:
        result["error"] = str(e)[:100]
    return result

HANDLERS = {"control": do_control, "keyboard": lambda p: do_control({**p, "op": "keyboard"}),
           "mouse": lambda p: do_control({**p, "op": "mouse_move"}),
           "window": lambda p: do_control({**p, "op": "window_list"})}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "control"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
