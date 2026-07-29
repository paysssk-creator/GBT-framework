# 开发者：自由的风
'''dev_processes/run.py — 进程实时监控'''
import sys, json
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

def do_list(params):
    if not HAS_PSUTIL:
        return {"ok": False, "error": "psutil未安装"}
    limit = params.get("limit", 20)
    sort_by = params.get("sort", "cpu")
    procs = []
    for p in psutil.process_iter(['pid','name','cpu_percent','memory_percent','status']):
        try:
            info = p.info
            if info['name']:
                procs.append(info)
        except Exception:
            pass
    procs.sort(key=lambda x: x.get(sort_by + '_percent', 0) or 0, reverse=True)
    return {
        "ok": True, "cap": "dev_processes", "action": "list", "domain": "设备感知层",
        "total": len(procs), "top": procs[:limit],
    }

def do_detail(params):
    pid = params.get("pid", 0)
    if not pid or not HAS_PSUTIL:
        return {"ok": False, "error": "缺少pid或psutil"}
    try:
        p = psutil.Process(pid)
        return {
            "ok": True, "cap": "dev_processes", "action": "detail",
            "pid": pid, "name": p.name(), "status": p.status(),
            "cpu_percent": p.cpu_percent(interval=0.1),
            "memory_mb": round(p.memory_info().rss/(1024**2), 1),
            "connections": len(p.connections(kind='inet')),
            "open_files": len(p.open_files()),
            "threads": p.num_threads(),
            "create_time": p.create_time(),
            "exe": p.exe(),
            "cmdline": p.cmdline(),
        }
    except psutil.NoSuchProcess:
        return {"ok": False, "error": f"进程{pid}不存在"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}

HANDLERS = {"list": do_list, "detail": do_detail}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "list"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
