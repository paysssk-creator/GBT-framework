# 开发者：自由的风
'''cradle_task/run.py — 持续任务托管执行'''
import sys, json, os, subprocess, time, threading, shlex

_tasks = {}

def do_start(params):
    import uuid
    tid = str(uuid.uuid4())[:8]
    cmd = params.get("cmd", "")
    interval = params.get("interval", 0)
    if not cmd:
        return {"ok": False, "error": "缺少cmd"}
    def _run():
        while _tasks.get(tid, {}).get("running"):
            subprocess.run(shlex.split(cmd), capture_output=True, timeout=30)
            if interval:
                time.sleep(interval)
            else:
                break
    _tasks[tid] = {"cmd": cmd, "interval": interval, "running": True, "started": time.time()}
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    _tasks[tid]["thread"] = t
    return {"ok": True, "cap": "cradle_task", "action": "start", "task_id": tid}

def do_stop(params):
    tid = params.get("task_id", "")
    if tid in _tasks:
        _tasks[tid]["running"] = False
        return {"ok": True, "task_id": tid, "stopped": True}
    return {"ok": False, "error": f"任务{tid}不存在"}

def do_list(params):
    return {"ok": True, "tasks": {k: {"cmd": v["cmd"], "running": v["running"], "elapsed": round(time.time()-v.get("started",0),1)} for k,v in _tasks.items()}}

HANDLERS = {"start": do_start, "stop": do_stop, "list": do_list}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "list"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
