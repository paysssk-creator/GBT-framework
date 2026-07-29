# 开发者：自由的风
'''dev_cpu/run.py — CPU实时状态传感器'''
import sys, json, os
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

def do_status(params):
    if not HAS_PSUTIL:
        return {"ok": False, "error": "psutil未安装"}
    cpu_percent = psutil.cpu_percent(interval=0.5, percpu=True)
    freq = psutil.cpu_freq()
    return {
        "ok": True, "cap": "dev_cpu", "action": "status", "domain": "设备感知层",
        "cores": psutil.cpu_count(logical=False),
        "threads": psutil.cpu_count(logical=True),
        "percent_per_core": cpu_percent,
        "total_percent": psutil.cpu_percent(interval=0.1),
        "frequency_mhz": {"current": freq.current if freq else 0, "max": freq.max if freq else 0},
        "load_avg_1_5_15": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [],
    }

HANDLERS = {"status": do_status}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "status"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
