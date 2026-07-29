# 开发者：自由的风
'''dev_ports/run.py — 端口监听状态'''
import sys, json
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

def do_list(params):
    if not HAS_PSUTIL:
        return {"ok": False, "error": "psutil未安装"}
    conns = []
    for c in psutil.net_connections(kind='inet'):
        conns.append({
            "fd": c.fd, "family": str(c.family),
            "type": "TCP" if c.type == 1 else "UDP",
            "local": f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "",
            "remote": f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "",
            "status": c.status,
            "pid": c.pid,
            "process": psutil.Process(c.pid).name() if c.pid else "",
        })
    listening = [c for c in conns if c["status"] == "LISTEN"]
    return {
        "ok": True, "cap": "dev_ports", "action": "list", "domain": "设备感知层",
        "total_connections": len(conns), "listening_ports": len(listening),
        "listening": listening,
        "all": conns[:50],
    }

def do_check(params):
    port = params.get("port", 0)
    if not port or not HAS_PSUTIL:
        return {"ok": False, "error": "缺少port或psutil"}
    for c in psutil.net_connections(kind='inet'):
        if c.laddr and c.laddr.port == port:
            return {"ok": True, "port": port, "in_use": True, "process": psutil.Process(c.pid).name() if c.pid else "", "pid": c.pid}
    return {"ok": True, "port": port, "in_use": False}

HANDLERS = {"list": do_list, "check": do_check}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "list"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
