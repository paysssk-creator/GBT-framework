# 开发者：自由的风
"""self_evolve/run.py — Pieces式长期记忆 + 6步自进化引擎
==========================================================
吸收Pieces核心能力: 自动捕捉 → 长期记忆 → 智能召回
吸收Claude核心能力: 深度推理 → 多步验证
吸收Cursor核心能力: 跨文件关联 → 上下文感知

数据: ~/.gbt/evolve/memory.jsonl (时间线记忆)
      ~/.gbt/evolve/insights.json (进化洞察)
      ~/.gbt/evolve/metrics.json (性能指标)
"""
import sys, json, os, time, hashlib
from pathlib import Path
from datetime import datetime, timezone

# 添加 sandbox 到 sys.path，以便导入 lessons_db 等模块
_sandbox_dir = Path(__file__).resolve().parent.parent.parent
if str(_sandbox_dir) not in sys.path:
    sys.path.insert(0, str(_sandbox_dir))

EVOLVE_DIR = Path.home() / ".gbt" / "evolve"
EVOLVE_DIR.mkdir(parents=True, exist_ok=True)
INSIGHTS_FILE = EVOLVE_DIR / "insights.json"
METRICS_FILE = EVOLVE_DIR / "metrics.json"
MEMORY_FILE = EVOLVE_DIR / "memory.jsonl"  # Pieces式时间线记忆
SNAPSHOT_DIR = EVOLVE_DIR / "snapshots"
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════ Pieces式 长期记忆 ═══════════════════

def _hash(text):
    return hashlib.md5(text.encode()).hexdigest()[:8]

def _trim_memories(max_lines=500):
    """保留最近 max_lines 条记忆，超出部分截断"""
    if not MEMORY_FILE.exists():
        return
    with open(MEMORY_FILE, encoding="utf-8") as f:
        lines = f.readlines()
    if len(lines) > max_lines:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines[-max_lines:])

def do_capture(params=None):
    """自动捕捉——记录一切操作到记忆时间线"""
    params = params or {}
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": params.get("type", "action"),  # action/decision/file/error/success
        "task": params.get("task", "")[:500],
        "detail": params.get("detail", "")[:2000],
        "result": params.get("result", ""),
        "file": params.get("file", ""),
        "tags": params.get("tags", []),
        "hash": _hash(params.get("task", "") + str(time.time())),
    }
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    # 自动截图（关键事件）
    if params.get("screenshot") and entry["type"] in ("error", "success"):
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            img.save(SNAPSHOT_DIR / f"{entry['hash']}.png")
            entry["snapshot"] = f"{entry['hash']}.png"
        except: pass
    
    # 清理旧记录，保留最近 500 条
    _trim_memories(500)
    
    return {"ok": True, "captured": True, "hash": entry["hash"],
            "total_memories": _count_memories()}

def do_search(params=None):
    """搜索记忆——关键词/语义查找历史经验"""
    params = params or {}
    query = (params.get("q") or params.get("query") or "").lower()
    tags = params.get("tags", [])
    limit = params.get("limit", 10)
    results = []
    
    if not MEMORY_FILE.exists():
        return {"ok": True, "found": 0, "results": [], "total": 0}
    
    with open(MEMORY_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                score = 0
                if query and query in (entry.get("task","") + entry.get("detail","")).lower():
                    score += 10
                if tags:
                    score += sum(1 for t in tags if t in entry.get("tags", [])) * 5
                if score > 0:
                    entry["score"] = score
                    results.append(entry)
            except: pass
    
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return {"ok": True, "found": len(results[:limit]), "results": results[:limit],
            "total": _count_memories()}

def do_timeline(params=None):
    """时间线——按时间查看记忆"""
    params = params or {}
    limit = params.get("limit", 20)
    mem_type = params.get("type", "")  # action/error/success/file
    
    results = []
    if not MEMORY_FILE.exists():
        return {"ok": True, "entries": [], "total": 0}
    
    with open(MEMORY_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if not mem_type or entry.get("type") == mem_type:
                    results.append(entry)
            except: pass
    
    results.reverse()  # 最新在前
    return {"ok": True, "entries": results[-limit:], "total": len(results)}

def do_recall(params=None):
    """智能召回——遇到相似问题时推荐历史解决方案（集成 lessons_db）"""
    params = params or {}
    task = (params.get("task") or params.get("q") or "").lower()
    if not task:
        return {"ok": False, "error": "缺少 task 参数"}

    # 搜索相似任务
    r = do_search({"q": task, "limit": 5})
    results = r.get("results", [])

    # 分析模式
    successes = [e for e in results if e.get("result") == "success"]
    failures = [e for e in results if e.get("result") == "failure"]

    recall = {
        "similar_tasks": len(results),
        "similar_successes": len(successes),
        "similar_failures": len(failures),
        "recommendation": "",
        "top_matches": results[:3],
        "lessons_db": [],
        "open_weaknesses": [],
    }

    # ── 集成 lessons_db ──
    try:
        from lessons_db import recall_lessons, get_open_weaknesses
        lessons = recall_lessons(limit=5)
        recall["lessons_db"] = [
            {"id": l.get("id","?"), "category": l.get("category",""),
             "lesson": l.get("lesson","")[:120], "applied": l.get("applied", False)}
            for l in lessons
        ]
        # 检查弱点
        weaknesses = get_open_weaknesses()
        recall["open_weaknesses"] = [
            {"id": w.get("id","?"), "weakness": w.get("weakness","")[:100],
             "severity": w.get("severity","medium")}
            for w in weaknesses[:5]
        ]
    except Exception:
        pass

    if successes:
        recall["recommendation"] = f"历史有{len(successes)}次成功经验，可参考: {successes[0].get('task','')[:100]}"
    elif failures:
        recall["recommendation"] = f"历史有{len(failures)}次失败记录，注意避免: {failures[0].get('task','')[:100]}"
    else:
        recall["recommendation"] = "无历史记录，这是新领域，建议先搜索学习"

    # 追加 lessons_db 建议
    if recall["lessons_db"]:
        recall["recommendation"] += f" | lessons_db有{len(recall['lessons_db'])}条相关教训"
    if recall["open_weaknesses"]:
        recall["recommendation"] += f" | {len(recall['open_weaknesses'])}个待改进弱点"

    return {"ok": True, "recall": recall}

def _count_memories():
    if not MEMORY_FILE.exists(): return 0
    return sum(1 for _ in open(MEMORY_FILE, encoding="utf-8"))

# ═══════════════ 原有: 6步自进化 ═══════════════

def _load_insights():
    if INSIGHTS_FILE.exists():
        return json.loads(INSIGHTS_FILE.read_text(encoding="utf-8"))
    return {"patterns": [], "lessons": [], "improvements": [], "total_evolutions": 0}

def _save_insights(data):
    INSIGHTS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def _load_metrics():
    if METRICS_FILE.exists():
        return json.loads(METRICS_FILE.read_text(encoding="utf-8"))
    return {"tasks": 0, "successes": 0, "failures": 0, "avg_duration_ms": 0, "skills_gained": []}

def _save_metrics(data):
    METRICS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def do_evolve(params=None):
    """6步自进化: 感知→分析→规划→执行→验证→吸收"""
    steps = []
    task = (params or {}).get("task", "未指定任务")
    result = (params or {}).get("result", "unknown")
    t0 = time.time()
    
    steps.append({"step": 1, "name": "感知", "status": "ok", "detail": f"任务: {task[:100]}"})
    
    insights = _load_insights()
    is_success = result in ("success", "ok", "pass", "done", True)
    analysis = {"task": task[:200], "result": "success" if is_success else "failure",
                "ts": datetime.now(timezone.utc).isoformat()}
    steps.append({"step": 2, "name": "分析", "status": "ok",
                  "detail": f"结果: {'成功' if is_success else '需改进'}"})
    
    improvement = ""
    if is_success:
        improvement = f"固化成功模式: {task[:60]}"
        insights["patterns"].append({"type": "success", "task": task[:100], "ts": analysis["ts"]})
    else:
        improvement = f"分析失败原因: {task[:60]}"
        insights["lessons"].append({"type": "failure", "task": task[:100], "ts": analysis["ts"]})
    steps.append({"step": 3, "name": "规划", "status": "ok", "detail": improvement})
    
    insights["total_evolutions"] += 1
    insights["improvements"].append({"task": task[:100], "improvement": improvement, "ts": analysis["ts"]})
    for key in ["patterns", "lessons", "improvements"]:
        if len(insights.get(key, [])) > 200:
            insights[key] = insights[key][-100:]
    _save_insights(insights)
    steps.append({"step": 4, "name": "执行", "status": "ok", "detail": "进化数据已更新"})
    
    metrics = _load_metrics()
    metrics["tasks"] += 1
    if is_success: metrics["successes"] += 1
    else: metrics["failures"] += 1
    success_rate = round(metrics["successes"] / max(metrics["tasks"], 1) * 100, 1)
    _save_metrics(metrics)
    steps.append({"step": 5, "name": "验证", "status": "ok",
                  "detail": f"成功率: {success_rate}% ({metrics['successes']}/{metrics['tasks']})"})
    
    evolution_summary = f"第{insights['total_evolutions']}次进化: {improvement}"
    steps.append({"step": 6, "name": "吸收", "status": "ok", "detail": evolution_summary})
    
    # 同时捕捉到长期记忆
    do_capture({"type": "success" if is_success else "error",
                "task": task, "result": result, "tags": ["evolve"]})
    
    return {"ok": True, "evolution": insights["total_evolutions"],
            "success_rate": success_rate, "steps": steps,
            "duration_ms": round((time.time() - t0) * 1000)}

def do_auto_evolve_cycle(params=None):
    """全自动6步自进化循环 — 无需人工输入
    1.感知: 读取最近记忆
    2.分析: 识别模式、频率、趋势
    3.规划: 生成改进建议
    4.执行: 写入 insights
    5.验证: 检查一致性
    6.吸收: 写入长期记忆
    """
    params = params or {}
    limit = params.get("limit", 50)
    t0 = time.time()
    steps = []

    # ── 步1: 感知 —— 读取最近记忆 ──
    memories = []
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, encoding="utf-8") as f:
            for line in f:
                try:
                    memories.append(json.loads(line.strip()))
                except: pass
    recent = memories[-limit:] if len(memories) > limit else memories
    steps.append({"step": 1, "name": "感知", "status": "ok",
                  "detail": f"读取{len(recent)}条最近记忆 (共{len(memories)}条)"})

    # ── 步2: 分析 —— 识别模式 ──
    analysis = {"total": len(recent), "successes": 0, "failures": 0,
                "actions": 0, "top_tasks": {}, "top_tags": {}, "top_types": {}}
    for m in recent:
        t = m.get("result", "")
        if t in ("success", "ok", "pass", "done"):
            analysis["successes"] += 1
        elif t in ("error", "failure", "fail"):
            analysis["failures"] += 1
        else:
            analysis["actions"] += 1
        task = m.get("task", "")[:80]
        if task:
            analysis["top_tasks"][task] = analysis["top_tasks"].get(task, 0) + 1
        for tag in m.get("tags", []):
            analysis["top_tags"][tag] = analysis["top_tags"].get(tag, 0) + 1
        mtype = m.get("type", "unknown")
        analysis["top_types"][mtype] = analysis["top_types"].get(mtype, 0) + 1

    # 排序取top
    analysis["top_tasks"] = dict(sorted(analysis["top_tasks"].items(),
                                        key=lambda x: x[1], reverse=True)[:10])
    analysis["top_tags"] = dict(sorted(analysis["top_tags"].items(),
                                       key=lambda x: x[1], reverse=True)[:10])
    success_rate = round(analysis["successes"] / max(analysis["total"], 1) * 100, 1)
    analysis["success_rate"] = success_rate
    steps.append({"step": 2, "name": "分析", "status": "ok",
                  "detail": f"成功率{success_rate}%, {len(analysis['top_tasks'])}类高频任务"})

    # ── 步3: 规划 —— 生成改进建议 ──
    suggestions = []
    if analysis["failures"] > 0:
        suggestions.append(f"关注{analysis['failures']}次失败，建议加强错误处理")
    if analysis["successes"] > analysis["failures"] * 3 and analysis["successes"] > 5:
        suggestions.append("高频成功模式可固化为自动化流程")
    if len(analysis["top_tasks"]) > 5:
        suggestions.append("任务分散度高，建议按领域分组优化")
    if not suggestions:
        suggestions.append("当前运行平稳，维持现有策略")
    steps.append({"step": 3, "name": "规划", "status": "ok",
                  "detail": "; ".join(suggestions)})

    # ── 步4: 执行 —— 写入 insights ──
    insights = _load_insights()
    cycle_id = f"auto_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    insights["total_evolutions"] += 1
    insights["improvements"].append({
        "cycle": cycle_id,
        "suggestions": suggestions,
        "analysis_summary": {
            "total_memories": analysis["total"],
            "success_rate": success_rate,
            "top_tasks": list(analysis["top_tasks"].keys())[:5],
            "top_tags": list(analysis["top_tags"].keys())[:5],
        },
        "ts": datetime.now(timezone.utc).isoformat(),
    })
    # 限定大小
    for key in ["patterns", "lessons", "improvements"]:
        if len(insights.get(key, [])) > 200:
            insights[key] = insights[key][-100:]
    _save_insights(insights)
    steps.append({"step": 4, "name": "执行", "status": "ok",
                  "detail": f"进化#{insights['total_evolutions']}已写入insights"})

    # ── 步5: 验证 —— 检查数据一致性 ──
    metrics = _load_metrics()
    consistency_checks = []
    if insights["total_evolutions"] > 0:
        consistency_checks.append(f"insights记录{insights['total_evolutions']}次进化")
    if _count_memories() > 0:
        consistency_checks.append(f"记忆库{_count_memories()}条记录")
    metrics["tasks"] += 1
    if analysis["successes"] >= analysis["failures"]:
        metrics["successes"] += 1
    else:
        metrics["failures"] += 1
    _save_metrics(metrics)
    steps.append({"step": 5, "name": "验证", "status": "ok",
                  "detail": "; ".join(consistency_checks) if consistency_checks else "数据一致"})

    # ── 步6: 吸收 —— 写入长期记忆 ──
    do_capture({"type": "success", "task": "auto_evolve_cycle",
                "detail": f"自动进化完成: {'; '.join(suggestions)}",
                "result": "success", "tags": ["evolve", "auto"]})
    steps.append({"step": 6, "name": "吸收", "status": "ok",
                  "detail": f"第{insights['total_evolutions']}次自动进化完成"})

    return {"ok": True, "evolution": insights["total_evolutions"],
            "success_rate": success_rate, "suggestions": suggestions,
            "steps": steps, "cycle_id": cycle_id,
            "duration_ms": round((time.time() - t0) * 1000)}


def do_cross_session_merge(params=None):
    """跨会话合并——将多次会话的碎片化学习合并为连贯的长期模式

    算法:
    1. 按时间窗口(默认12h间隔)将会话分组
    2. 每组内提取关键模式
    3. 跨组比对相同任务的成功/失败模式
    4. 合并为长期规律写入 insights
    """
    params = params or {}
    gap_hours = params.get("gap_hours", 12)  # 会话间隔阈值(小时)
    min_sessions = params.get("min_sessions", 2)  # 最少会话数才合并
    t0 = time.time()

    # 读取所有记忆
    all_memories = []
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, encoding="utf-8") as f:
            for line in f:
                try:
                    all_memories.append(json.loads(line.strip()))
                except: pass

    if len(all_memories) < 2:
        return {"ok": True, "merged": False, "reason": "记忆不足，无法合并",
                "total_memories": len(all_memories)}

    # 按时间戳排序
    all_memories.sort(key=lambda m: m.get("ts", ""))

    # 按时间间隔分会话
    sessions = []
    current_session = []
    last_ts = None
    gap_seconds = gap_hours * 3600

    for m in all_memories:
        ts = m.get("ts", "")
        if not ts:
            current_session.append(m)
            continue
        try:
            dt = datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            current_session.append(m)
            continue

        if last_ts is None:
            current_session.append(m)
            last_ts = dt
        else:
            if (dt - last_ts).total_seconds() > gap_seconds:
                if current_session:
                    sessions.append(current_session)
                current_session = [m]
            else:
                current_session.append(m)
            last_ts = dt

    if current_session:
        sessions.append(current_session)

    if len(sessions) < min_sessions:
        return {"ok": True, "merged": False,
                "reason": f"仅{len(sessions)}个会话(<{min_sessions})，无需合并",
                "session_count": len(sessions), "total_memories": len(all_memories)}

    # 从每个会话提取摘要
    session_summaries = []
    for i, sess in enumerate(sessions):
        tasks_in_session = {}
        results_in_session = {"success": 0, "failure": 0, "action": 0}
        tags_in_session = {}
        for m in sess:
            r = m.get("result", "")
            if r in ("success", "ok", "pass", "done"):
                results_in_session["success"] += 1
            elif r in ("error", "failure", "fail"):
                results_in_session["failure"] += 1
            else:
                results_in_session["action"] += 1
            task = m.get("task", "")[:80]
            if task:
                tasks_in_session[task] = tasks_in_session.get(task, 0) + 1
            for tag in m.get("tags", []):
                tags_in_session[tag] = tags_in_session.get(tag, 0) + 1
        session_summaries.append({
            "session_index": i + 1,
            "start_ts": sess[0].get("ts", ""),
            "end_ts": sess[-1].get("ts", ""),
            "total_events": len(sess),
            "successes": results_in_session["success"],
            "failures": results_in_session["failure"],
            "top_tasks": dict(sorted(tasks_in_session.items(),
                                     key=lambda x: x[1], reverse=True)[:5]),
            "top_tags": dict(sorted(tags_in_session.items(),
                                    key=lambda x: x[1], reverse=True)[:5]),
        })

    # 跨会话分析: 找重复出现的任务模式
    cross_patterns = {}
    for s in session_summaries:
        for task in s["top_tasks"]:
            if task not in cross_patterns:
                cross_patterns[task] = {"appearances": 0, "sessions": []}
            cross_patterns[task]["appearances"] += 1
            cross_patterns[task]["sessions"].append(s["session_index"])

    # 筛选跨会话重复出现的模式 (>=2个会话)
    merged_patterns = []
    for task, info in cross_patterns.items():
        if info["appearances"] >= 2:
            # 检查成功/失败偏向
            task_successes = 0
            task_failures = 0
            for m in all_memories:
                if m.get("task", "")[:80] == task:
                    r = m.get("result", "")
                    if r in ("success", "ok", "pass", "done"):
                        task_successes += 1
                    elif r in ("error", "failure", "fail"):
                        task_failures += 1
            merged_patterns.append({
                "task": task,
                "cross_session_count": info["appearances"],
                "sessions": info["sessions"],
                "success_count": task_successes,
                "failure_count": task_failures,
                "verdict": "固化成功模式" if task_successes > task_failures
                           else ("需改进" if task_failures > 0 else "新领域"),
            })

    merged_patterns.sort(key=lambda x: x["cross_session_count"], reverse=True)

    # 写入 insights
    insights = _load_insights()
    for mp in merged_patterns[:20]:
        if mp["verdict"] == "固化成功模式":
            insights["patterns"].append({
                "type": "merged_success",
                "task": mp["task"],
                "cross_sessions": mp["cross_session_count"],
                "ts": datetime.now(timezone.utc).isoformat(),
            })
        else:
            insights["lessons"].append({
                "type": "merged_lesson",
                "task": mp["task"],
                "verdict": mp["verdict"],
                "cross_sessions": mp["cross_session_count"],
                "ts": datetime.now(timezone.utc).isoformat(),
            })

    for key in ["patterns", "lessons", "improvements"]:
        if len(insights.get(key, [])) > 200:
            insights[key] = insights[key][-100:]
    _save_insights(insights)

    # 记录合并事件
    do_capture({"type": "success", "task": "cross_session_merge",
                "detail": f"合并{len(sessions)}个会话, 发现{len(merged_patterns)}个跨会话模式",
                "result": "success", "tags": ["evolve", "merge"]})

    return {"ok": True, "merged": True,
            "session_count": len(sessions),
            "merged_patterns": merged_patterns[:20],
            "pattern_count": len(merged_patterns),
            "sessions": session_summaries,
            "duration_ms": round((time.time() - t0) * 1000)}

def do_learn(params=None):
    insights = _load_insights()
    lesson = (params or {}).get("lesson", (params or {}).get("task", ""))
    if lesson:
        insights["lessons"].append({"type": "manual", "lesson": lesson,
                                     "ts": datetime.now(timezone.utc).isoformat()})
        _save_insights(insights)
    return {"ok": True, "learned": True, "total_lessons": len(insights["lessons"])}

def do_insights(params=None):
    insights = _load_insights()
    memories = _count_memories()
    return {"ok": True, "total_evolutions": insights["total_evolutions"],
            "patterns": insights["patterns"][-10:],
            "lessons": insights["lessons"][-10:],
            "improvements": len(insights.get("improvements", [])),
            "memories": memories,
            "summary": f'{insights["total_evolutions"]}次进化, {memories}条记忆, {len(insights["patterns"])}成功模式, {len(insights["lessons"])}教训'}

def do_metrics(params=None):
    m = _load_metrics()
    insights = _load_insights()
    success_rate = round(m["successes"] / max(m["tasks"], 1) * 100, 1)
    return {"ok": True, "tasks": m["tasks"], "successes": m["successes"],
            "failures": m["failures"], "success_rate": success_rate,
            "memories": _count_memories(), "evolutions": insights["total_evolutions"]}

HANDLERS = {
    "evolve": do_evolve, "learn": do_learn, "insights": do_insights, "metrics": do_metrics,
    "capture": do_capture, "search": do_search, "timeline": do_timeline, "recall": do_recall,
    "auto_evolve_cycle": do_auto_evolve_cycle, "cross_session_merge": do_cross_session_merge,
}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 else "search"
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
