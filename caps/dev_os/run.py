# 开发者：自由的风
'''dev_os/run.py — 操作系统信息感知'''
import sys, json, os, platform, socket, subprocess, datetime

def do_info(params):
    boot_time = None
    try:
        import psutil
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time()).isoformat()
    except ImportError:
        pass
    users = []
    try:
        for line in subprocess.run(["who"], capture_output=True, text=True).stdout.strip().split("\n"):
            if line.strip():
                users.append(line.strip())
    except Exception:
        try:
            users = [os.environ.get("USERNAME", os.environ.get("USER", "unknown"))]
        except Exception:
            pass
    return {
        "ok": True, "cap": "dev_os", "action": "info", "domain": "设备感知层",
        "system": platform.system(), "release": platform.release(),
        "version": platform.version(), "machine": platform.machine(),
        "processor": platform.processor(), "hostname": socket.gethostname(),
        "python_version": sys.version, "boot_time": boot_time,
        "current_user": os.environ.get("USERNAME", os.environ.get("USER", "")),
        "logged_users": users, "env_keys": list(os.environ.keys())[:20],
    }

def do_uptime(params):
    try:
        import psutil
        uptime_sec = time.time() - psutil.boot_time()
        days = int(uptime_sec // 86400)
        hours = int((uptime_sec % 86400) // 3600)
        minutes = int((uptime_sec % 3600) // 60)
        return {"ok": True, "uptime": f"{days}d {hours}h {minutes}m", "uptime_seconds": int(uptime_sec)}
    except ImportError:
        return {"ok": False, "error": "psutil未安装"}

import time
HANDLERS = {"info": do_info, "uptime": do_uptime, "users": lambda p: do_info(p)}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "info"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
