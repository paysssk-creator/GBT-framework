# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""context_brain/run.py — 上下文管理大脑 v1.0
============================================
统一上下文管理管线 — 所有LLM调用的必经前/后处理:
  pre_task:  压力检测→清理→注入上下文→记录开始 (省token)
  post_task: 记录完成→保存教训→清理临时数据
  pressure:  实时token预算检测
  cleanup:   过期清理+冷数据归档
  inject:    任务前注入相关上下文
  record_stuck/decision: 卡点/决策持久化
  auto_maintain: 自动维护(daemon每小时调用)
"""
import sys, json, os, time, re, subprocess
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

EVENT_LOG = Path.home() / ".gbt" / "memory" / "context_events.jsonl"
STUCK_LOG = Path.home() / ".gbt" / "memory" / "stuck_points.jsonl"
EVENT_LOG.parent.mkdir(parents=True, exist_ok=True)

def _log_event(event_type: str, detail: str, metadata: dict = None):
    try:
        entry = {"timestamp": time.time(), "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                 "type": event_type, "detail": detail[:500], "metadata": metadata or {}}
        with open(EVENT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except: pass

def _log_stuck(blocker: str, solution: str, attempts: int):
    try:
        entry = {"timestamp": time.time(), "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                 "blocker": blocker[:300], "solution": solution[:500], "attempts": attempts}
        with open(STUCK_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except: pass

def _estimate_tokens(text: str) -> int:
    if not text: return 0
    cn = len(re.findall(r'[\u4e00-\u9fff]', text))
    return int(cn / 1.5 + (len(text) - cn) / 4)

def _get_context_budget():
    return int(os.environ.get("GBT_CONTEXT_BUDGET", "128000"))

def _measure_pressure() -> dict:
    budget = _get_context_budget()
    mem_tokens = mem_count = 0
    mem_file = ROOT / "memory_store.json"
    if mem_file.exists():
        try:
            data = json.loads(mem_file.read_text(encoding="utf-8"))
            mem_count = len(data)
            mem_tokens = sum(_estimate_tokens(str(v)) for v in data.values())
        except: pass
    disc_tokens = 0
    try:
        from brain.cognition import get_cognition
        for d in (get_cognition().recent(100) or []):
            disc_tokens += _estimate_tokens(json.dumps(d, ensure_ascii=False))
    except: pass
    lesson_tokens = 0
    try:
        from brain.self_evolve import get_evolver
        for l in (get_evolver()._load_lessons() or []):
            lesson_tokens += _estimate_tokens(json.dumps(l, ensure_ascii=False))
    except: pass
    total = mem_tokens + disc_tokens + lesson_tokens
    pct = round(total / max(budget, 1) * 100, 1)
    return {"ok": True, "budget": budget, "memory": {"count": mem_count, "tokens": mem_tokens},
            "cognition": {"tokens": disc_tokens}, "lessons": {"tokens": lesson_tokens},
            "total_used": total, "usage_pct": pct,
            "status": "🟢 safe" if pct < 50 else ("🟡 warning" if pct < 75 else "🔴 critical"),
            "threshold_exceeded": pct > 60}

def _cleanup_memory(aggressive=False) -> dict:
    try:
        from caps.memory.run import _load, _save, _clean_expired
        data = _load(); before = len(data)
        removed = _clean_expired(data)
        if aggressive and len(data) > 200:
            sorted_keys = sorted(data.keys(), key=lambda k: data[k].get("saved_at", ""), reverse=True)
            archive = {k: data.pop(k) for k in sorted_keys[100:]}
            archive_file = Path.home() / ".gbt" / "memory" / f"archive_{datetime.now().strftime('%Y%m%d')}.json"
            archive_file.write_text(json.dumps(archive, ensure_ascii=False, indent=2), encoding="utf-8")
            removed += len(archive)
        _save(data)
        return {"ok": True, "before": before, "after": len(data), "removed": removed}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def _inject_relevant_context(task: str, max_tokens: int = 5000) -> str:
    parts, used = [], 0
    try:
        from caps.memory.run import _load
        data = _load()
        keywords = set(task.lower().split())
        relevant = []
        for k, v in data.items():
            if isinstance(v, dict):
                score = sum(1 for kw in keywords if kw in f"{k} {v.get('value','')}".lower())
                if score > 0: relevant.append((score, k, v))
        relevant.sort(key=lambda x: -x[0])
        for score, k, v in relevant[:5]:
            snippet = f"[记忆:{k}] {str(v.get('value',''))[:300]}"
            tk = _estimate_tokens(snippet)
            if used + tk < max_tokens: parts.append(snippet); used += tk
    except: pass
    if STUCK_LOG.exists():
        try:
            for line in open(STUCK_LOG, encoding="utf-8").readlines()[-10:]:
                e = json.loads(line.strip())
                snippet = f"[卡点] {e.get('blocker','')[:100]} → {e.get('solution','')[:200]}"
                tk = _estimate_tokens(snippet)
                if used + tk < max_tokens: parts.append(snippet); used += tk
        except: pass
    try:
        from brain.cognition import get_cognition
        for d in (get_cognition().recent(5) or []):
            snippet = f"[认知:{d.get('topic','')}] {d.get('description','')[:200]}"
            tk = _estimate_tokens(snippet)
            if used + tk < max_tokens: parts.append(snippet); used += tk
    except: pass
    return "\n".join(parts)

# ═══════════════ 动作处理 ═══════════════

def do_pressure(params=None):
    return _measure_pressure()

def do_cleanup(params=None):
    aggressive = (params or {}).get("aggressive", False)
    mem_result = _cleanup_memory(aggressive)
    if mem_result.get("removed", 0) > 0:
        _log_event("context_cleanup", f"清理{mem_result['removed']}条记忆", mem_result)
    return {"ok": True, "memory_cleanup": mem_result, "pressure_after": _measure_pressure()}

def do_inject(params=None):
    task = (params or {}).get("task", (params or {}).get("query", ""))
    max_tokens = (params or {}).get("max_tokens", 5000)
    context = _inject_relevant_context(task, max_tokens)
    return {"ok": True, "context": context, "tokens": _estimate_tokens(context),
            "pressure": _measure_pressure(), "task": task[:100]}

def do_record_stuck(params):
    blocker = params.get("blocker", params.get("error", ""))
    solution = params.get("solution", params.get("fix", ""))
    attempts = params.get("attempts", 1)
    if not blocker: return {"ok": False, "error": "缺少blocker参数"}
    _log_stuck(blocker, solution, attempts)
    _log_event("stuck", blocker, {"solution": solution[:200], "attempts": attempts})
    if solution: _log_event("recovery", f"卡点已解决: {blocker[:100]} → {solution[:100]}")
    try:
        from brain.self_evolve import get_evolver
        get_evolver().add_lesson(f"卡点: {blocker[:150]} → 解决: {solution[:150]}",
            category="context_recovery", severity="medium", source_task="context_brain.record_stuck")
    except: pass
    return {"ok": True, "recorded": True, "blocker": blocker[:100]}

def do_record_decision(params):
    decision = params.get("decision", ""); reason = params.get("reason", "")
    _log_event("decision", decision, {"reason": reason, "outcome": params.get("outcome","pending")})
    try:
        from brain.self_evolve import get_evolver
        get_evolver().capture(decision, reason, params.get("outcome","pending"))
    except: pass
    return {"ok": True, "recorded": True}

def do_auto_maintain(params=None):
    pressure = _measure_pressure()
    result = {"ok": True, "pressure": pressure}
    if pressure["threshold_exceeded"]:
        cleanup = _cleanup_memory(aggressive=pressure["usage_pct"] > 75)
        result["cleanup"] = cleanup
        _log_event("context_cleanup", f"自动清理{cleanup.get('removed',0)}条")
        result["pressure_after"] = _measure_pressure()
    return result

def do_recent_events(params=None):
    limit = (params or {}).get("limit", 20)
    events = []
    if EVENT_LOG.exists():
        for line in open(EVENT_LOG, encoding="utf-8").readlines()[-limit:]:
            try: events.append(json.loads(line.strip()))
            except: pass
    stuck = []
    if STUCK_LOG.exists():
        for line in open(STUCK_LOG, encoding="utf-8").readlines()[-5:]:
            try: stuck.append(json.loads(line.strip()))
            except: pass
    return {"ok": True, "events": events, "stuck_points": stuck,
            "total_events": sum(1 for _ in open(EVENT_LOG, encoding="utf-8")) if EVENT_LOG.exists() else 0}

def do_pre_task(params=None):
    """任务前全流程 — 每个LLM调用的必经前处理"""
    task = (params or {}).get("task", (params or {}).get("query", ""))
    task_id = str(int(time.time()))
    pressure = _measure_pressure()
    cleanup_result = None
    if pressure["threshold_exceeded"]:
        cleanup_result = _cleanup_memory(aggressive=pressure["usage_pct"] > 75)
        pressure = _measure_pressure()
    max_ctx = (params or {}).get("max_context_tokens", 3000)
    injected = _inject_relevant_context(task, max_ctx)
    if task: _log_event("task_start", task[:200], {"task_id": task_id})
    recent_stuck = []
    if STUCK_LOG.exists():
        try:
            for line in open(STUCK_LOG, encoding="utf-8").readlines()[-3:]:
                recent_stuck.append(json.loads(line.strip()))
        except: pass
    return {"ok": True, "task_id": task_id,
            "pressure": {"status": pressure["status"], "usage_pct": pressure["usage_pct"], "budget": pressure["budget"]},
            "cleanup_done": cleanup_result is not None,
            "injected_context": injected[:1000], "injected_tokens": _estimate_tokens(injected),
            "recent_stuck_points": [{"blocker": s.get("blocker","")[:150], "solution": s.get("solution","")[:150]} for s in recent_stuck],
            "ready": True}

def do_post_task(params=None):
    """任务后清理"""
    task = (params or {}).get("task", "")
    success = (params or {}).get("success", True)
    lessons = (params or {}).get("lessons", [])
    stuck_points = (params or {}).get("stuck_points", [])
    if task: _log_event("task_complete", f"{'✅' if success else '❌'} {task[:200]}", {"success": success})
    for sp in stuck_points:
        _log_stuck(sp.get("blocker",""), sp.get("solution",""), sp.get("attempts",1))
    for lesson in lessons:
        try:
            from brain.self_evolve import get_evolver
            get_evolver().add_lesson(str(lesson)[:300], category="post_task", severity="medium", source_task=task[:100])
        except: pass
    if _measure_pressure()["usage_pct"] > 70: _cleanup_memory(aggressive=False)
    return {"ok": True, "recorded": True, "stuck_saved": len(stuck_points), "lessons_saved": len(lessons)}

HANDLERS = {
    "pressure": do_pressure, "cleanup": do_cleanup, "inject": do_inject,
    "record_stuck": do_record_stuck, "record_decision": do_record_decision,
    "auto_maintain": do_auto_maintain, "recent_events": do_recent_events,
    "pre_task": do_pre_task, "post_task": do_post_task, "run": do_auto_maintain,
}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "auto_maintain"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知:{action}"})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
