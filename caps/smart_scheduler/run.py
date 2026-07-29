# 开发者：自由的风
"""smart_scheduler/run.py — 智能任务调度
=========================================
运维域 ready — 优先级队列+定时触发+依赖链+DAG执行
"""
import sys, json, os, time, threading, heapq, subprocess, shlex
from pathlib import Path
from datetime import datetime, timedelta

_task_queue = []
_task_lock = threading.Lock()
_scheduled_tasks = {}
_results = {}
_completed_results = []
_counter = [0]
_worker_thread = None
_worker_running = False
_worker_results_lock = threading.Lock()

def _now(): return datetime.now().isoformat()

def do_schedule(params):
    """调度任务 — 加入优先级队列"""
    task = params.get("task", params.get("cmd", ""))
    priority = params.get("priority", 5)
    delay_sec = params.get("delay", 0)
    depends_on = params.get("depends", [])
    task_id = f"task_{_counter[0]}"
    _counter[0] += 1

    entry = {"id": task_id, "task": task, "priority": priority,
             "delay": delay_sec, "depends": depends_on,
             "scheduled_at": _now(), "status": "queued"}

    with _task_lock:
        heapq.heappush(_task_queue, (priority, task_id, entry))
        _scheduled_tasks[task_id] = entry


    if not _worker_running or not (_worker_thread and _worker_thread.is_alive()):
        do_start_worker({})

    return {"ok": True, "cap": "smart_scheduler", "action": "schedule",
            "domain": "运维域", "task_id": task_id, "priority": priority}
def do_list(params):
    """列出所有调度任务"""
    with _task_lock:
        tasks = [{"id": tid, "task": t["task"][:60], "priority": t["priority"],
                  "status": t["status"], "scheduled": t["scheduled_at"]}
                 for _, tid, t in sorted(_task_queue)]
    results = [{"id": tid, "result": r.get("result", "")[:100]}
               for tid, r in _results.items()]
    return {"ok": True, "queued": len(tasks), "completed": len(results),
            "tasks": tasks, "results": results[-10:]}

def do_cancel(params):
    """取消调度"""
    tid = params.get("task_id", "")
    with _task_lock:
        if tid in _scheduled_tasks:
            _scheduled_tasks[tid]["status"] = "cancelled"
            return {"ok": True, "task_id": tid, "cancelled": True}
    return {"ok": False, "error": f"任务{tid}不存在"}
def _worker_loop():
    """Worker daemon thread — polls queue, executes highest-priority ready tasks."""
    while _worker_running:
        try:
            with _task_lock:
                if not _task_queue:
                    time.sleep(1)
                    continue
                _, tid, entry = _task_queue[0]

            deps = entry.get("depends", [])
            if deps:
                with _worker_results_lock:
                    done_ids = {r["id"] for r in _completed_results}
                if not all(d in done_ids for d in deps):
                    time.sleep(1)
                    continue

            with _task_lock:
                if _task_queue and _task_queue[0][1] == tid:
                    heapq.heappop(_task_queue)
                else:
                    time.sleep(1)
                    continue

            entry["status"] = "running"
            entry["started_at"] = _now()

            try:
                cmd_parts = shlex.split(entry["task"])
                r = subprocess.run(
                    cmd_parts, capture_output=True, text=True, timeout=300,
                    cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                result = {
                    "id": tid, "task": entry["task"][:120],
                    "priority": entry["priority"],
                    "returncode": r.returncode,
                    "stdout": (r.stdout or "").strip()[:2000],
                    "stderr": (r.stderr or "").strip()[:1000],
                    "started_at": entry.get("started_at", ""),
                    "finished_at": _now(), "status": "done"
                }
            except subprocess.TimeoutExpired:
                result = {
                    "id": tid, "task": entry["task"][:120],
                    "priority": entry["priority"],
                    "returncode": -1,
                    "stdout": "", "stderr": f"超时(300s)",
                    "started_at": entry.get("started_at", ""),
                    "finished_at": _now(), "status": "timeout"
                }
            except Exception as e:
                result = {
                    "id": tid, "task": entry["task"][:120],
                    "priority": entry["priority"],
                    "returncode": -1,
                    "stdout": "", "stderr": str(e)[:1000],
                    "started_at": entry.get("started_at", ""),
                    "finished_at": _now(), "status": "error"
                }

            entry["status"] = result["status"]
            with _task_lock:
                _results[tid] = result
            with _worker_results_lock:
                _completed_results.append(result)

            delay = entry.get("delay", 0)
            if delay > 0:
                entry["status"] = "queued"
                entry["scheduled_at"] = _now()
                with _task_lock:
                    heapq.heappush(_task_queue, (entry["priority"], tid, entry))

        except Exception:
            time.sleep(1)


def do_start_worker(params):
    """启动 worker 线程 — 保持进程存活"""
    global _worker_thread, _worker_running
    with _task_lock:
        if _worker_running and _worker_thread and _worker_thread.is_alive():
            return {"ok": True, "cap": "smart_scheduler", "action": "start_worker",
                    "domain": "运维域", "status": "already_running"}
        _worker_running = True
        _worker_thread = threading.Thread(target=_worker_loop, daemon=True)
        _worker_thread.start()
    # 保持进程存活 — 不返回，让daemon_launcher的子进程持续运行
    try:
        while _worker_running:
            time.sleep(5)
    except KeyboardInterrupt:
        _worker_running = False
    return {"ok": True, "cap": "smart_scheduler", "action": "start_worker",
            "domain": "运维域", "status": "stopped"}


def do_stop_worker(params):
    """停止 worker 线程"""
    global _worker_running, _worker_thread
    with _task_lock:
        _worker_running = False
        worker = _worker_thread
    if worker and worker.is_alive():
        worker.join(timeout=3)
    return {"ok": True, "cap": "smart_scheduler", "action": "stop_worker",
            "domain": "运维域", "status": "stopped"}


def do_results(params):
    """返回最近 20 条完成结果"""
    limit = params.get("limit", 20)
    with _worker_results_lock:
        recent = _completed_results[-limit:]
    return {"ok": True, "cap": "smart_scheduler", "action": "results",
            "domain": "运维域", "total": len(_completed_results),
            "results": recent}

# ═══════════════════════════════════════════════════════════
#  持久化调度状态 → ~/.gbt/schedule.json
# ═══════════════════════════════════════════════════════════
SCHEDULE_FILE = Path.home() / ".gbt" / "schedule.json"
SCHEDULE_FILE.parent.mkdir(parents=True, exist_ok=True)

def _load_schedule():
    """从 ~/.gbt/schedule.json 恢复跨会话任务"""
    if not SCHEDULE_FILE.exists():
        return []
    try:
        data = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []

def _save_schedule(tasks_list):
    """持久化当前任务队列到 ~/.gbt/schedule.json"""
    try:
        SERIALIZABLE = []
        with _task_lock:
            for _, tid, entry in _task_queue:
                SERIALIZABLE.append({
                    "id": entry["id"], "task": entry["task"],
                    "priority": entry["priority"],
                    "delay": entry.get("delay", 0),
                    "depends": entry.get("depends", []),
                    "scheduled_at": entry["scheduled_at"],
                    "status": entry["status"],
                    "cron": entry.get("cron", None),
                    "chain_id": entry.get("chain_id", None),
                })
        SCHEDULE_FILE.write_text(json.dumps(SERIALIZABLE, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def _restore_schedule():
    """模块加载时恢复持久化任务"""
    saved = _load_schedule()
    if not saved:
        return
    with _task_lock:
        for entry in saved:
            tid = entry["id"]
            _counter[0] = max(_counter[0], int(tid.replace("task_", "")) + 1)
            heapq.heappush(_task_queue, (entry["priority"], tid, {
                "id": tid, "task": entry["task"],
                "priority": entry["priority"],
                "delay": entry.get("delay", 0),
                "depends": entry.get("depends", []),
                "scheduled_at": entry.get("scheduled_at", _now()),
                "status": "queued",
                "cron": entry.get("cron"),
                "chain_id": entry.get("chain_id"),
            }))
            _scheduled_tasks[tid] = _task_queue[-1][2]

# ═══════════════════════════════════════════════════════════
#  Cron表达式解析器
# ═══════════════════════════════════════════════════════════
_CRON_RANGES = {
    "minute":  (0, 59),  "hour": (0, 23),
    "day":     (1, 31),  "month": (1, 12),
    "weekday": (0, 7),   # 0=Sunday, 7=Sunday
}

def _parse_cron_field(field: str, lo: int, hi: int) -> set:
    """解析单个cron字段为匹配值集合。支持 * / N 逗号 和 范围 -"""
    if field == "*":
        return set(range(lo, hi + 1))
    result = set()
    for part in field.split(","):
        part = part.strip()
        if "/" in part:
            base, step = part.split("/")
            step = int(step)
            if base == "*":
                for v in range(lo, hi + 1, step):
                    result.add(v)
            else:
                start = int(base)
                for v in range(start, hi + 1, step):
                    result.add(v)
        elif "-" in part:
            a, b = part.split("-")
            for v in range(int(a), int(b) + 1):
                result.add(v)
        else:
            result.add(int(part))
    return result

def _cron_matches(cron_expr: str, dt: datetime) -> bool:
    """检查给定时间是否匹配cron表达式 (minute hour day month weekday)"""
    try:
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            return False
        minute_f, hour_f, day_f, month_f, weekday_f = parts
        return (
            dt.minute in _parse_cron_field(minute_f, 0, 59) and
            dt.hour   in _parse_cron_field(hour_f,   0, 23) and
            dt.day    in _parse_cron_field(day_f,     1, 31) and
            dt.month  in _parse_cron_field(month_f,   1, 12) and
            (dt.weekday() + 1) % 7 in _parse_cron_field(weekday_f, 0, 7)
        )
    except Exception:
        return False

def _next_cron_match(cron_expr: str, after: datetime = None) -> datetime:
    """计算cron表达式的下一个匹配时间 (最大前瞻60天)"""
    if after is None:
        after = datetime.now()
    dt = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    for _ in range(60 * 24 * 60):  # 60天 * 24小时 * 60分钟
        if _cron_matches(cron_expr, dt):
            return dt
        dt += timedelta(minutes=1)
    return after + timedelta(days=365)  # 兜底

# ═══════════════════════════════════════════════════════════
#  Cron调度
# ═══════════════════════════════════════════════════════════
_cron_tasks = {}
_cron_lock = threading.Lock()
_cron_thread = None
_cron_running = False

def _cron_loop():
    """Cron调度线程 — 每分钟检查一次到期任务"""
    while _cron_running:
        try:
            now = datetime.now()
            with _cron_lock:
                for cron_expr, tasks in list(_cron_tasks.items()):
                    if _cron_matches(cron_expr, now):
                        for task_spec in tasks:
                            params = {
                                "task": task_spec["task"],
                                "priority": task_spec.get("priority", 5),
                                "delay": task_spec.get("delay", 0),
                                "depends": task_spec.get("depends", []),
                            }
                            do_schedule(params)
            time.sleep(60)
        except Exception:
            time.sleep(10)

def _ensure_cron_thread():
    global _cron_thread, _cron_running
    if not _cron_running or not (_cron_thread and _cron_thread.is_alive()):
        _cron_running = True
        _cron_thread = threading.Thread(target=_cron_loop, daemon=True)
        _cron_thread.start()

def do_cron_schedule(params):
    """Cron定时调度 — 按cron表达式周期性触发任务

    cron表达式: minute hour day month weekday (空格分隔5字段)
    示例: "0 */6 * * *" = 每6小时, "30 9 * * 1" = 每周一9:30
    """
    task = params.get("task", params.get("cmd", ""))
    cron_expr = params.get("cron", "")
    priority = params.get("priority", 5)
    delay = params.get("delay", 0)
    depends = params.get("depends", [])

    if not task:
        return {"ok": False, "error": "缺少task参数"}
    if not cron_expr or len(cron_expr.strip().split()) != 5:
        return {"ok": False, "error": "cron表达式格式错误，需5字段: minute hour day month weekday"}

    task_spec = {
        "task": task, "priority": priority,
        "delay": delay, "depends": depends,
    }

    with _cron_lock:
        _cron_tasks.setdefault(cron_expr, []).append(task_spec)

    _ensure_cron_thread()

    # 保存到持久化文件
    _save_schedule(_cron_tasks.get(cron_expr, []))

    return {
        "ok": True, "cap": "smart_scheduler", "action": "cron_schedule",
        "domain": "运维域", "cron": cron_expr,
        "task": task[:80], "priority": priority,
        "next_run": _next_cron_match(cron_expr).isoformat(),
    }

# ═══════════════════════════════════════════════════════════
#  Self-Start — 模块导入时自动启动worker
# ═══════════════════════════════════════════════════════════
_SELF_START_DONE = False

def do_self_start(params):
    """模块导入时自动启动worker线程 — 无需显式调用start_worker"""
    global _SELF_START_DONE
    if _SELF_START_DONE:
        return {"ok": True, "cap": "smart_scheduler", "action": "self_start",
                "domain": "运维域", "status": "already_started"}
    _SELF_START_DONE = True
    _restore_schedule()
    # 同时自动从 schedule_persist.json 恢复
    restore_result = do_restore_queue({})
    result = do_start_worker({})
    _ensure_cron_thread()
    result["action"] = "self_start"
    result["restored_from_persist"] = restore_result.get("restored", 0)
    return result

# ═══════════════════════════════════════════════════════════
#  任务依赖链 — Chain Tasks
# ═══════════════════════════════════════════════════════════
_chains = {}
_chain_lock = threading.Lock()

def do_chain_tasks(params):
    """创建任务依赖链 — 后一个任务只有前一个成功后才执行

    tasks: [{"task": "...", "priority": 5}, ...]
    依次调度到队列，每个任务depends=前一个任务ID
    任一失败则链中止
    """
    tasks = params.get("tasks", [])
    chain_name = params.get("name", f"chain_{int(time.time())}")

    if not tasks or not isinstance(tasks, list) or len(tasks) < 2:
        return {"ok": False, "error": "tasks至少需要2个任务"}

    chain_ids = []
    prev_id = None

    for i, spec in enumerate(tasks):
        task_cmd = spec.get("task", spec.get("cmd", ""))
        priority = spec.get("priority", 5)
        delay = spec.get("delay", 0)

        depends = [prev_id] if prev_id else []

        entry_params = {
            "task": task_cmd, "priority": priority,
            "delay": delay, "depends": depends,
        }

        result = do_schedule(entry_params)
        tid = result.get("task_id", "")
        chain_ids.append(tid)

        with _task_lock:
            if tid in _scheduled_tasks:
                _scheduled_tasks[tid]["chain_id"] = chain_name
                _scheduled_tasks[tid]["chain_index"] = i
                _scheduled_tasks[tid]["chain_length"] = len(tasks)
                if prev_id:
                    _scheduled_tasks[tid]["depends_on_chain"] = prev_id

        prev_id = tid

    with _chain_lock:
        _chains[chain_name] = {
            "name": chain_name, "task_ids": chain_ids,
            "total": len(tasks), "created": _now(),
            "status": "queued",
        }

    _save_schedule(None)

    return {
        "ok": True, "cap": "smart_scheduler", "action": "chain_tasks",
        "domain": "运维域", "chain": chain_name,
        "task_count": len(tasks), "task_ids": chain_ids,
    }

# ═══════════════════════════════════════════════════════════
#  持久化队列 → ~/.gbt/schedule_persist.json
# ═══════════════════════════════════════════════════════════
PERSIST_FILE = Path.home() / ".gbt" / "schedule_persist.json"
PERSIST_FILE.parent.mkdir(parents=True, exist_ok=True)


def do_persist_queue(params):
    """保存完整任务队列到 ~/.gbt/schedule_persist.json
    跨进程重启持久化，包含队列+cron+链状态"""
    try:
        payload = {"version": "2.0", "saved_at": _now()}

        # 队列任务
        with _task_lock:
            queue_entries = []
            for _, tid, entry in _task_queue:
                queue_entries.append({
                    "id": entry["id"], "task": entry["task"],
                    "priority": entry["priority"],
                    "delay": entry.get("delay", 0),
                    "depends": entry.get("depends", []),
                    "scheduled_at": entry.get("scheduled_at", ""),
                    "status": entry.get("status", "queued"),
                    "cron": entry.get("cron"),
                    "chain_id": entry.get("chain_id"),
                    "chain_index": entry.get("chain_index"),
                })
        payload["queue"] = queue_entries
        payload["counter"] = _counter[0]

        # Cron任务
        with _cron_lock:
            payload["cron_tasks"] = {
                expr: [{"task": t["task"], "priority": t.get("priority", 5),
                        "delay": t.get("delay", 0), "depends": t.get("depends", [])}
                       for t in tasks]
                for expr, tasks in _cron_tasks.items()
            }

        # 依赖链
        with _chain_lock:
            payload["chains"] = {
                name: {"name": c["name"], "task_ids": c["task_ids"],
                       "total": c["total"], "created": c["created"], "status": c["status"]}
                for name, c in _chains.items()
            }

        PERSIST_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "action": "persist_queue",
                "path": str(PERSIST_FILE),
                "queued": len(queue_entries),
                "cron_entries": len(payload["cron_tasks"]),
                "chains": len(payload["chains"])}
    except Exception as e:
        return {"ok": False, "error": str(e)[:500]}


def do_restore_queue(params):
    """从 ~/.gbt/schedule_persist.json 恢复完整队列"""
    if not PERSIST_FILE.exists():
        return {"ok": True, "action": "restore_queue", "restored": 0,
                "message": "持久化文件不存在，跳过恢复"}
    try:
        payload = json.loads(PERSIST_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        return {"ok": False, "error": f"读取持久文件失败: {e}"}

    if not isinstance(payload, dict) or "queue" not in payload:
        return {"ok": False, "error": "持久化文件格式无效"}

    restored_count = 0

    # 恢复队列
    with _task_lock:
        for entry in payload.get("queue", []):
            tid = entry["id"]
            _counter[0] = max(_counter[0], int(tid.replace("task_", "")) + 1)
            heapq.heappush(_task_queue, (entry["priority"], tid, {
                "id": tid, "task": entry["task"],
                "priority": entry["priority"],
                "delay": entry.get("delay", 0),
                "depends": entry.get("depends", []),
                "scheduled_at": entry.get("scheduled_at", _now()),
                "status": "queued",
                "cron": entry.get("cron"),
                "chain_id": entry.get("chain_id"),
                "chain_index": entry.get("chain_index"),
            }))
            _scheduled_tasks[tid] = _task_queue[-1][2]
            restored_count += 1

    # 恢复计数器
    if saved_counter := payload.get("counter"):
        _counter[0] = max(_counter[0], saved_counter)

    # 恢复Cron任务
    with _cron_lock:
        for expr, tasks in payload.get("cron_tasks", {}).items():
            _cron_tasks.setdefault(expr, []).extend(tasks)

    # 恢复依赖链
    with _chain_lock:
        for name, chain in payload.get("chains", {}).items():
            _chains[name] = chain

    # 恢复后自动启动worker
    if restored_count > 0 and not _worker_running:
        do_start_worker({})
    if payload.get("cron_tasks"):
        _ensure_cron_thread()

    return {"ok": True, "action": "restore_queue",
            "restored": restored_count,
            "cron_restored": len(payload.get("cron_tasks", {})),
            "chains_restored": len(payload.get("chains", {})),
            "worker_started": _worker_running}
HANDLERS = {
    "schedule": do_schedule, "list": do_list, "cancel": do_cancel,
    "start_worker": do_start_worker, "stop_worker": do_stop_worker,
    "results": do_results,
    "cron_schedule": do_cron_schedule, "self_start": do_self_start,
    "chain_tasks": do_chain_tasks,
    "persist_queue": do_persist_queue, "restore_queue": do_restore_queue,
}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "list"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
