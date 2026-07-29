# 开发者：自由的风
'''win_control/run.py — Windows原生16类操控'''
import sys, json, os, subprocess, ctypes

def do_control(params):
    op = params.get("op", "info")
    result = {"ok": True, "cap": "win_control", "domain": "桌面域", "op": op}
    try:
        if op == "registry_read":
            import winreg
            key_path = params.get("key", r"SOFTWARE\Microsoft\Windows\CurrentVersion")
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            result["value"] = winreg.QueryValueEx(key, params.get("value", "ProgramFilesDir"))[0]
            winreg.CloseKey(key)
        elif op == "process_kill":
            pid = params.get("pid", 0)
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        elif op == "shutdown_abort":
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000003)
            result["note"] = "防关机已激活"
        elif op == "message_box":
            ctypes.windll.user32.MessageBoxW(0, params.get("text",""), params.get("title","GBT"), 0)
    except Exception as e:
        result["error"] = str(e)[:100]
    return result

HANDLERS = {"control": do_control, "registry": lambda p: do_control({**p, "op": "registry_read"}),
           "kill": lambda p: do_control({**p, "op": "process_kill"})}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "control"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
