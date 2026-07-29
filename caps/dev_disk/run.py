# 开发者：自由的风
'''dev_disk/run.py — 磁盘实时状态传感器'''
import sys, json
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

def do_status(params):
    if not HAS_PSUTIL:
        return {"ok": False, "error": "psutil未安装"}
    partitions = []
    for p in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(p.mountpoint)
            partitions.append({
                "device": p.device, "mount": p.mountpoint,
                "fs": p.fstype, "total_gb": round(usage.total/(1024**3),1),
                "used_gb": round(usage.used/(1024**3),1), "free_gb": round(usage.free/(1024**3),1),
                "percent": usage.percent,
            })
        except Exception:
            pass
    io = psutil.disk_io_counters()
    return {
        "ok": True, "cap": "dev_disk", "action": "status", "domain": "设备感知层",
        "partitions": partitions, "partition_count": len(partitions),
        "io": {"read_bytes": io.read_bytes, "write_bytes": io.write_bytes,
               "read_count": io.read_count, "write_count": io.write_count} if io else {},
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
