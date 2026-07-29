# 开发者：自由的风
'''dev_ram/run.py — 内存实时状态传感器'''
import sys, json
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

def do_status(params):
    if not HAS_PSUTIL:
        return {"ok": False, "error": "psutil未安装"}
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "ok": True, "cap": "dev_ram", "action": "status", "domain": "设备感知层",
        "total_gb": round(mem.total / (1024**3), 1),
        "available_gb": round(mem.available / (1024**3), 1),
        "used_gb": round(mem.used / (1024**3), 1),
        "percent": mem.percent,
        "swap_total_gb": round(swap.total / (1024**3), 1) if swap.total > 0 else 0,
        "swap_used_gb": round(swap.used / (1024**3), 1) if swap.total > 0 else 0,
        "swap_percent": swap.percent,
        "status": "critical" if mem.percent > 90 else "warning" if mem.percent > 75 else "normal",
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
