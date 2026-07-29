# 开发者：自由的风
"""project_state/run.py — 项目状态追踪
=======================================
持久化项目工作状态: 目标/进度/日志/快照/跑偏检测。
数据存储: ~/.gbt/state/<project>/state.json
"""
import sys, json, os, time, hashlib
from pathlib import Path
from datetime import datetime, timezone

STATE_DIR = Path.home() / ".gbt" / "state"
PROJECT_NAME = Path.cwd().name
STATE_FILE = STATE_DIR / PROJECT_NAME / "state.json"
CHECKPOINT_DIR = STATE_DIR / PROJECT_NAME / "checkpoints"

def _load():
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return _default_state()

def _default_state():
    return {
        "project": PROJECT_NAME,
        "created": datetime.now(timezone.utc).isoformat(),
        "goals": [],           # [{id, title, status, parent, created, completed}]
        "tasks": [],           # [{id, title, status, goal_id, created, completed}]
        "decisions": [],       # [{ts, text, context}]
        "log": [],             # [{ts, action, detail}]
        "checkpoints": [],     # [{ts, id, summary}]
        "stats": {"total_tasks": 0, "completed_tasks": 0, "total_decisions": 0,
                  "sessions": 0, "last_active": None},
    }

def _save(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

def _now():
    return datetime.now(timezone.utc).isoformat()

def do_goal(params):
    action = params.get("action", "list")
    title = params.get("title", "")
    goal_id = params.get("id", "")
    parent = params.get("parent", "")
    state = _load()
    if action == "set" and title:
        gid = hashlib.md5(title.encode()).hexdigest()[:8]
        goal = {"id": gid, "title": title, "status": "active",
                "parent": parent, "created": _now(), "completed": None}
        state["goals"].append(goal)
        _save(state)
        return {"ok": True, "goal": goal}
    elif action == "complete" and goal_id:
        for g in state["goals"]:
            if g["id"] == goal_id:
                g["status"] = "completed"; g["completed"] = _now()
                break
        _save(state)
        return {"ok": True, "completed": goal_id}
    elif action == "cancel" and goal_id:
        for g in state["goals"]:
            if g["id"] == goal_id:
                g["status"] = "cancelled"; g["completed"] = _now()
                break
        _save(state)
        return {"ok": True, "cancelled": goal_id}
    # list
    active = [g for g in state["goals"] if g["status"] == "active"]
    completed = [g for g in state["goals"] if g["status"] == "completed"]
    return {"ok": True, "active": active, "completed": completed,
            "total": len(state["goals"])}

def do_progress(params=None):
    state = _load()
    goals_active = [g for g in state["goals"] if g["status"] == "active"]
    goals_done = [g for g in state["goals"] if g["status"] == "completed"]
    tasks_active = [t for t in state["tasks"] if t["status"] == "in_progress"]
    tasks_done = [t for t in state["tasks"] if t["status"] == "done"]
    recent_logs = state["log"][-5:]
    recent_decisions = state["decisions"][-3:]
    last_checkpoint = state["checkpoints"][-1] if state["checkpoints"] else None
    return {
        "ok": True,
        "project": PROJECT_NAME,
        "goals": {"total": len(state["goals"]), "active": len(goals_active),
                  "done": len(goals_done), "current": goals_active[0]["title"] if goals_active else None},
        "tasks": {"total": len(state["tasks"]), "in_progress": len(tasks_active),
                  "done": len(tasks_done), "current": tasks_active[0]["title"] if tasks_active else None},
        "recent_logs": recent_logs,
        "recent_decisions": recent_decisions,
        "last_checkpoint": last_checkpoint,
        "sessions": state["stats"]["sessions"],
        "last_active": state["stats"]["last_active"],
    }

def do_log(params):
    action = params.get("action_type", params.get("type", "action"))
    detail = params.get("detail", params.get("message", ""))
    if not detail: return {"ok": False, "error": "缺少 detail/message 参数"}
    state = _load()
    entry = {"ts": _now(), "action": action, "detail": detail}
    state["log"].append(entry)
    # 决策类单独记录
    if action in ("decision", "decided", "choice"):
        state["decisions"].append({"ts": _now(), "text": detail})
        state["stats"]["total_decisions"] += 1
    state["stats"]["last_active"] = _now()
    # 限制日志数量
    if len(state["log"]) > 500:
        state["log"] = state["log"][-300:]
    _save(state)
    return {"ok": True, "logged": True, "total_entries": len(state["log"])}

def do_checkpoint(params=None):
    label = (params or {}).get("label", "")
    state = _load()
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    cp_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    cp_file = CHECKPOINT_DIR / f"{cp_id}.json"
    cp_file.write_text(json.dumps(state, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    cp_info = {"ts": _now(), "id": cp_id, "label": label,
               "goals_active": len([g for g in state["goals"] if g["status"] == "active"]),
               "tasks_done": len([t for t in state["tasks"] if t["status"] == "done"])}
    state["checkpoints"].append(cp_info)
    state["stats"]["sessions"] += 1
    # 清理旧快照 (保留最近20个)
    cps = sorted(CHECKPOINT_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in cps[20:]:
        old.unlink(missing_ok=True)
    _save(state)
    return {"ok": True, "checkpoint": cp_info}

def do_resume(params=None):
    state = _load()
    cps = sorted(CHECKPOINT_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not cps:
        return {"ok": True, "resumed": False, "message": "没有快照，从头开始"}
    last_cp = json.loads(cps[0].read_text(encoding="utf-8"))
    return {
        "ok": True, "resumed": True,
        "last_active": last_cp["stats"]["last_active"],
        "active_goals": [g["title"] for g in last_cp["goals"] if g["status"] == "active"],
        "recent_logs": last_cp["log"][-5:],
        "sessions": last_cp["stats"]["sessions"],
    }

def do_drift_check(params):
    """跑偏检测: 最近工作是否偏离当前目标"""
    state = _load()
    current_goal = params.get("goal", "")
    recent_work = params.get("recent_work", "")
    if not current_goal:
        goals_active = [g for g in state["goals"] if g["status"] == "active"]
        current_goal = goals_active[0]["title"] if goals_active else ""
    if not current_goal:
        return {"ok": True, "drifting": False, "message": "无当前目标，无法检测"}
    if not recent_work:
        recent_work = " ".join([l["detail"] for l in state["log"][-10:]])
    # 简单关键词匹配
    goal_keywords = set(current_goal.lower().split())
    work_keywords = set(recent_work.lower().split())
    overlap = goal_keywords & work_keywords
    drift_score = len(overlap) / max(len(goal_keywords), 1)
    if drift_score < 0.1:
        return {"ok": True, "drifting": True, "score": round(drift_score, 2),
                "warning": f"⚠️ 当前工作似乎偏离了目标「{current_goal}」",
                "goal": current_goal, "recent": recent_work[:200]}
    return {"ok": True, "drifting": False, "score": round(drift_score, 2),
            "message": f"✅ 聚焦目标「{current_goal}」，重合度 {drift_score:.0%}"}

def do_auto_snapshot(params=None):
    """自动快照 — 创建包含活跃任务、修改文件、当前阶段的完整快照"""
    import subprocess
    state = _load()
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    cp_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 收集修改文件 (git status)
    modified_files = []
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=10, cwd=Path.cwd()
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                if len(line) >= 3:
                    status_code = line[:2].strip()
                    file_path = line[3:].strip()
                    modified_files.append({"status": status_code, "file": file_path})
    except Exception:
        pass

    # 当前阶段
    phase = (params or {}).get("phase", "")
    if not phase:
        active_goals = [g["title"] for g in state["goals"] if g["status"] == "active"]
        active_tasks = [t["title"] for t in state["tasks"] if t["status"] == "in_progress"]
        phase = active_tasks[0] if active_tasks else (active_goals[0] if active_goals else "unknown")

    snapshot = {
        "id": cp_id,
        "timestamp": _now(),
        "project": PROJECT_NAME,
        "phase": phase,
        "active_goals": [g for g in state["goals"] if g["status"] == "active"],
        "active_tasks": [t for t in state["tasks"] if t["status"] == "in_progress"],
        "recent_logs": state["log"][-10:],
        "recent_decisions": state["decisions"][-5:],
        "modified_files": modified_files,
        "stats_snapshot": dict(state["stats"]),
    }

    # 写入快照文件
    cp_file = CHECKPOINT_DIR / f"snapshot_{cp_id}.json"
    cp_file.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    # 注册到状态
    cp_info = {"ts": _now(), "id": cp_id, "type": "auto_snapshot",
               "phase": phase, "files_changed": len(modified_files)}
    state["checkpoints"].append(cp_info)
    state["stats"]["sessions"] += 1
    state["stats"]["last_active"] = _now()

    # 清理旧快照 (保留最近30个)
    snaps = sorted(CHECKPOINT_DIR.glob("snapshot_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in snaps[30:]:
        old.unlink(missing_ok=True)
    _save(state)

    return {
        "ok": True,
        "snapshot_id": cp_id,
        "phase": phase,
        "active_goals_count": len(snapshot["active_goals"]),
        "active_tasks_count": len(snapshot["active_tasks"]),
        "modified_files_count": len(modified_files),
        "modified_files": modified_files[:20],
        "snapshot_file": str(cp_file),
    }


def do_restore_latest(params=None):
    """恢复最近快照 — 将最近一次 auto_snapshot 恢复为当前状态"""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    snaps = sorted(CHECKPOINT_DIR.glob("snapshot_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not snaps:
        return {"ok": False, "error": "没有可恢复的快照", "restored": False}

    latest_snap = json.loads(snaps[0].read_text(encoding="utf-8"))
    snap_id = latest_snap.get("id", snaps[0].stem.replace("snapshot_", ""))

    # 重建当前状态
    state = _load()
    state["goals"] = latest_snap.get("active_goals", [])
    state["tasks"] = latest_snap.get("active_tasks", [])
    state["stats"] = latest_snap.get("stats_snapshot", state["stats"])
    state["stats"]["last_active"] = _now()
    state["stats"]["sessions"] += 1

    # 追加恢复记录
    state["log"].append({"ts": _now(), "action": "restore",
                         "detail": f"恢复快照 {snap_id} — 阶段: {latest_snap.get('phase', 'unknown')}"})
    if len(state["log"]) > 500:
        state["log"] = state["log"][-300:]
    _save(state)

    return {
        "ok": True,
        "restored": True,
        "snapshot_id": snap_id,
        "snapshot_timestamp": latest_snap.get("timestamp", ""),
        "phase": latest_snap.get("phase", ""),
        "restored_goals": len(latest_snap.get("active_goals", [])),
        "restored_tasks": len(latest_snap.get("active_tasks", [])),
        "modified_files_at_snapshot": latest_snap.get("modified_files", []),
    }


def do_diff_snapshots(params):
    """对比两个快照之间的变化"""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    snap_a_id = params.get("snap_a", params.get("from", ""))
    snap_b_id = params.get("snap_b", params.get("to", ""))

    def _find_snap(snap_id):
        candidates = list(CHECKPOINT_DIR.glob(f"snapshot_{snap_id}.json"))
        if not candidates:
            candidates = list(CHECKPOINT_DIR.glob(f"snapshot_*.json"))
            candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            for c in candidates:
                try:
                    data = json.loads(c.read_text(encoding="utf-8"))
                    if data.get("id") == snap_id:
                        return data
                except Exception:
                    pass
            return None
        return json.loads(candidates[0].read_text(encoding="utf-8"))

    # 未指定 ID 时使用最近两个
    if not snap_a_id or not snap_b_id:
        all_snaps = sorted(CHECKPOINT_DIR.glob("snapshot_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if len(all_snaps) < 2:
            return {"ok": False, "error": "需要至少两个快照才能对比", "available": len(all_snaps)}
        snap_b = json.loads(all_snaps[0].read_text(encoding="utf-8"))
        snap_a = json.loads(all_snaps[1].read_text(encoding="utf-8"))
    else:
        snap_a = _find_snap(snap_a_id)
        snap_b = _find_snap(snap_b_id)

    if not snap_a:
        return {"ok": False, "error": f"快照 A 未找到: {snap_a_id}"}
    if not snap_b:
        return {"ok": False, "error": f"快照 B 未找到: {snap_b_id}"}

    # 对比目标变化
    goals_a = {g["id"]: g for g in snap_a.get("active_goals", [])}
    goals_b = {g["id"]: g for g in snap_b.get("active_goals", [])}
    goals_added = [g for gid, g in goals_b.items() if gid not in goals_a]
    goals_removed = [g for gid, g in goals_a.items() if gid not in goals_b]

    # 对比任务变化
    tasks_a = {t["id"]: t for t in snap_a.get("active_tasks", [])}
    tasks_b = {t["id"]: t for t in snap_b.get("active_tasks", [])}
    tasks_added = [t for tid, t in tasks_b.items() if tid not in tasks_a]
    tasks_removed = [t for tid, t in tasks_a.items() if tid not in tasks_b]

    # 对比文件变化
    files_a = {f["file"]: f["status"] for f in snap_a.get("modified_files", [])}
    files_b = {f["file"]: f["status"] for f in snap_b.get("modified_files", [])}
    files_new = [f for f in files_b if f not in files_a]
    files_gone = [f for f in files_a if f not in files_b]
    files_changed = [f for f in files_b if f in files_a and files_b[f] != files_a[f]]
    files_unchanged = [f for f in files_b if f in files_a and files_b[f] == files_a[f]]

    # 阶段变化
    phase_a = snap_a.get("phase", "")
    phase_b = snap_b.get("phase", "")
    phase_changed = phase_a != phase_b

    return {
        "ok": True,
        "snap_a": {"id": snap_a.get("id", ""), "timestamp": snap_a.get("timestamp", ""),
                   "phase": phase_a, "goals": len(goals_a), "tasks": len(tasks_a)},
        "snap_b": {"id": snap_b.get("id", ""), "timestamp": snap_b.get("timestamp", ""),
                   "phase": phase_b, "goals": len(goals_b), "tasks": len(tasks_b)},
        "changes": {
            "phase": {"from": phase_a, "to": phase_b, "changed": phase_changed},
            "goals": {"added": len(goals_added), "removed": len(goals_removed),
                      "added_list": goals_added, "removed_list": goals_removed},
            "tasks": {"added": len(tasks_added), "removed": len(tasks_removed),
                      "added_list": tasks_added, "removed_list": tasks_removed},
            "files": {"new": len(files_new), "gone": len(files_gone),
                      "changed": len(files_changed), "unchanged": len(files_unchanged),
                      "new_list": files_new[:20], "changed_list": files_changed[:20]},
        },
    }

HANDLERS = {"goal": do_goal, "progress": do_progress, "log": do_log,
            "checkpoint": do_checkpoint, "resume": do_resume, "drift_check": do_drift_check,
            "auto_snapshot": do_auto_snapshot, "restore_latest": do_restore_latest,
            "diff_snapshots": do_diff_snapshots}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "progress"
    params = {}
    # 优先从 stdin 读取 JSON 参数（CapabilityEngine 标准协议）
    if not sys.stdin.isatty():
        try:
            stdin_raw = sys.stdin.read().strip()
            if stdin_raw:
                params = json.loads(stdin_raw)
        except (json.JSONDecodeError, Exception):
            pass
    # 回退：从命令行参数读取
    if not params and len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except (json.JSONDecodeError, Exception):
            params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知动作: {action}", "available": list(HANDLERS.keys())})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
