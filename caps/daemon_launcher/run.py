# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""daemon_launcher/run.py — 守护进程启动器
============================================
管理 heartbeat + smart_scheduler worker 的启停与存活监控。
PID 持久化到 ~/.gbt/daemon_launcher/pids.json。
"""
import sys, json, os, subprocess, signal, time
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
PID_FILE = Path.home() / ".gbt" / "daemon_launcher" / "pids.json"


def _load_pids() -> dict:
    if PID_FILE.exists():
        try:
            return json.loads(PID_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_pids(data: dict):
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _is_alive(pid: int) -> bool:
    """检查 PID 是否存活 (Windows)"""
    try:
        import ctypes
        import ctypes.wintypes
        SYNCHRONIZE = 0x00100000
        PROCESS_QUERY_INFORMATION = 0x0400
        handle = ctypes.windll.kernel32.OpenProcess(
            SYNCHRONIZE | PROCESS_QUERY_INFORMATION, False, pid
        )
        if handle:
            exit_code = ctypes.wintypes.DWORD()
            ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            ctypes.windll.kernel32.CloseHandle(handle)
            return exit_code.value == 259  # STILL_ACTIVE
    except Exception:
        pass
    return False


def _start_one(label: str, cmd: list, cwd: str = "") -> dict:
    try:
        proc = subprocess.Popen(
            cmd, cwd=cwd or str(ROOT),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        return {"label": label, "pid": proc.pid, "cmd": " ".join(cmd), "started": True}
    except Exception as e:
        return {"label": label, "cmd": " ".join(cmd), "started": False, "error": str(e)}


# ── Actions ──────────────────────────────────────────────────────

def do_start_all(params: dict) -> dict:
    """启动 heartbeat + smart_scheduler worker（已存活则跳过）"""
    started = []
    existing = _load_pids()

    # 心跳守护
    if existing.get("heartbeat") and _is_alive(existing["heartbeat"]):
        started.append({"label": "heartbeat", "pid": existing["heartbeat"], "started": False, "status": "already_running"})
    else:
        heartbeat_cmd = [sys.executable, str(ROOT / "brain" / "heartbeat.py")]
        r = _start_one("heartbeat", heartbeat_cmd)
        started.append(r)

    # 调度器 worker
    if existing.get("scheduler_worker") and _is_alive(existing["scheduler_worker"]):
        started.append({"label": "scheduler_worker", "pid": existing["scheduler_worker"], "started": False, "status": "already_running"})
    else:
        scheduler_cmd = [sys.executable, str(ROOT / "caps" / "smart_scheduler" / "run.py"), "start_worker"]
        r = _start_one("scheduler_worker", scheduler_cmd)
        started.append(r)

    # 持久化 PID
    pids = {}
    for item in started:
        pid = item.get("pid")
        if pid:
            pids[item["label"]] = pid
    _save_pids(pids)

    ok = all(item.get("started") or item.get("status") == "already_running" for item in started)
    return {
        "ok": ok,
        "action": "start_all",
        "cap": "daemon_launcher",
        "domain": "运维域",
        "daemons": started,
    }


def do_stop_all(params: dict) -> dict:
    """终止所有管理的子进程"""
    pids = _load_pids()
    results = []

    for label, pid in pids.items():
        result = {"label": label, "pid": pid}
        try:
            if _is_alive(pid):
                proc = subprocess.run(
                    ["taskkill", "/PID", str(pid), "/F"],
                    capture_output=True, text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                result["terminated"] = proc.returncode == 0
                result["detail"] = proc.stdout.strip() or proc.stderr.strip()
            else:
                result["terminated"] = False
                result["detail"] = "already dead"
        except Exception as e:
            result["terminated"] = False
            result["error"] = str(e)
        results.append(result)

    _save_pids({})
    all_stopped = all(r.get("terminated") for r in results)
    return {
        "ok": all_stopped,
        "action": "stop_all",
        "cap": "daemon_launcher",
        "domain": "运维域",
        "results": results,
    }


def do_status(params: dict) -> dict:
    """报告守护进程存活状态"""
    pids = _load_pids()
    daemons = []
    alive_count = 0

    for label, pid in pids.items():
        alive = _is_alive(pid)
        daemons.append({"label": label, "pid": pid, "alive": alive})
        if alive:
            alive_count += 1

    return {
        "ok": True,
        "action": "status",
        "cap": "daemon_launcher",
        "domain": "运维域",
        "total": len(daemons),
        "alive": alive_count,
        "daemons": daemons,
    }


def do_install_service(params: dict) -> dict:
    """创建 Windows 计划任务 — 用户登录时启动 daemon_launcher start_all"""
    task_name = params.get("task_name", "GBT_DaemonLauncher")
    run_py = str(Path(__file__).resolve())
    command = f'cmd /c "{sys.executable}" "{run_py}" start_all'
    task_cmd = [
        "schtasks", "/Create", "/SC", "ONLOGON",
        "/TN", task_name, "/TR", command,
        "/F", "/RL", "HIGHEST", "/DELAY", "0000:30",
    ]

    try:
        proc = subprocess.run(
            task_cmd, capture_output=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        success = proc.returncode == 0
        return {
            "ok": success,
            "action": "install_service",
            "cap": "daemon_launcher",
            "domain": "运维域",
            "task_name": task_name,
            "command": command,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as e:
        return {
            "ok": False,
            "action": "install_service",
            "cap": "daemon_launcher",
            "domain": "运维域",
            "error": str(e),
        }


HANDLERS = {
    "start_all": do_start_all,
    "stop_all": do_stop_all,
    "status": do_status,
    "install_service": do_install_service,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except json.JSONDecodeError:
            params = {"query": sys.argv[2]}
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知动作: {action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
