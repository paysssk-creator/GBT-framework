# 开发者：自由的风
'''dev_network/run.py — 网络实时状态传感器'''
import sys, json
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

def do_status(params):
    if not HAS_PSUTIL:
        return {"ok": False, "error": "psutil未安装"}
    interfaces = {}
    for name, addrs in psutil.net_if_addrs().items():
        iface = {"name": name, "addresses": []}
        for addr in addrs:
            iface["addresses"].append({"family": str(addr.family), "address": addr.address, "netmask": addr.netmask or ""})
        interfaces[name] = iface
    net_io = psutil.net_io_counters()
    connections = len(psutil.net_connections(kind='inet'))
    return {
        "ok": True, "cap": "dev_network", "action": "status", "domain": "设备感知层",
        "interfaces": list(interfaces.keys()),
        "bytes_sent": net_io.bytes_sent, "bytes_recv": net_io.bytes_recv,
        "packets_sent": net_io.packets_sent, "packets_recv": net_io.packets_recv,
        "active_connections": connections,
    }

def do_speed(params):
    if not HAS_PSUTIL:
        return {"ok": False, "error": "psutil未安装"}
    import time
    t1 = psutil.net_io_counters()
    time.sleep(1)
    t2 = psutil.net_io_counters()
    return {
        "ok": True, "cap": "dev_network", "action": "speed",
        "upload_bps": t2.bytes_sent - t1.bytes_sent,
        "download_bps": t2.bytes_recv - t1.bytes_recv,
    }

HANDLERS = {"status": do_status, "speed": do_speed}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "status"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
