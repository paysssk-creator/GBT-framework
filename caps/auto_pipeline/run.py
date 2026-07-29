# 开发者：自由的风
"""auto_pipeline/run.py — 多步骤任务自动编排
============================================
运维域 core — 定义流水线步骤，自动按序执行，失败重试，产出证据链。
"""
import sys, json, os, subprocess, time, threading
from pathlib import Path
from datetime import datetime

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPS_DIR = Path(SANDBOX) / "caps"
PIPELINE_DIR = Path.home() / ".gbt" / "pipelines"
PIPELINE_DIR.mkdir(parents=True, exist_ok=True)

_pipelines = {}
_pipeline_lock = threading.Lock()


def _call_cap(cap_id, action, params, timeout=60):
    run_py = CAPS_DIR / cap_id / "run.py"
    if not run_py.exists():
        return {"ok": False, "error": f"cap {cap_id} 不存在"}
    try:
        r = subprocess.run(
            [sys.executable, str(run_py), action, json.dumps(params, ensure_ascii=False)],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(SANDBOX), encoding="utf-8", errors="replace"
        )
        return json.loads((r.stdout or "{}").strip())
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"超时({timeout}s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}


def _breaker_call(cap_id, action, params, timeout=60):
    """带熔断保护的cap调用 — 调用前检查熔断器，调用后报告结果"""
    if cap_id == "circuit_breaker":
        return _call_cap(cap_id, action, params, timeout)
    breaker = _call_cap("circuit_breaker", "check", {"cap": cap_id})
    if breaker.get("state") == "open":
        print(f"[auto_pipeline] 熔断器已断开，跳过: {cap_id}.{action}", file=sys.stderr)
        return {"ok": False, "error": f"熔断器已断开: {cap_id}", "breaker": "open"}
    result = _call_cap(cap_id, action, params, timeout)
    if result.get("ok"):
        _call_cap("circuit_breaker", "reset", {"cap": cap_id})
    else:
        _call_cap("circuit_breaker", "fail", {"cap": cap_id})
    return result

def do_define(params):
    """定义流水线"""
    name = params.get("name", f"pipeline_{int(time.time())}")
    steps = params.get("steps", [])

    if not steps:
        return {"ok": False, "error": "缺少 steps 参数"}

    pipeline = {
        "name": name,
        "steps": steps,
        "created": datetime.now().isoformat(),
        "status": "defined",
    }

    with _pipeline_lock:
        _pipelines[name] = pipeline

    return {
        "ok": True,
        "cap": "auto_pipeline",
        "action": "define",
        "pipeline": name,
        "step_count": len(steps),
        "steps": [{"cap": s.get("cap", "?"), "action": s.get("action", "?")} for s in steps],
    }


def do_run(params):
    """运行流水线"""
    name = params.get("name", params.get("pipeline", ""))
    if not name:
        # 直接用steps参数构建即时流水线
        steps = params.get("steps", [])
        if not steps:
            return {"ok": False, "error": "缺少 name 或 steps 参数"}
        pipe = {"name": "ad_hoc", "steps": steps}
    else:
        with _pipeline_lock:
            pipe = _pipelines.get(name)
        if not pipe:
            # 尝试从文件加载
            fpath = PIPELINE_DIR / f"{name}.json"
            if fpath.exists():
                pipe = json.loads(fpath.read_text(encoding="utf-8"))
            else:
                return {"ok": False, "error": f"流水线 {name} 不存在"}

    max_retries = params.get("retries", 2)
    continue_on_error = params.get("continue_on_error", False)

    results = []
    start_time = time.time()

    for i, step in enumerate(pipe["steps"]):
        cap_id = step.get("cap", "")
        action = step.get("action", "")
        step_params = step.get("params", {})

        step_result = None
        for attempt in range(max_retries + 1):
            step_result = _breaker_call(cap_id, action, step_params)
            if step_result.get("ok"):
                break
            if attempt < max_retries:
                backoff = min(2 ** attempt, 60)
                time.sleep(backoff)

        results.append({
            "step": i + 1,
            "cap": cap_id,
            "action": action,
            "ok": step_result.get("ok", False) if step_result else False,
            "attempts": min(attempt + 1, max_retries + 1) if step_result else max_retries + 1,
            "result": step_result,
        })

        if not step_result.get("ok") and not continue_on_error:
            break

    elapsed = round(time.time() - start_time, 1)
    success = all(r["ok"] for r in results)
    completed = sum(1 for r in results if r["ok"])

    return {
        "ok": success,
        "cap": "auto_pipeline",
        "action": "run",
        "domain": "运维域",
        "pipeline": name,
        "elapsed_sec": elapsed,
        "total_steps": len(pipe["steps"]),
        "completed": completed,
        "failed": len(pipe["steps"]) - completed,
        "step_results": results,
        "verdict": "全部完成" if success else f"{completed}/{len(pipe['steps'])}完成",
    }


def do_status(params):
    """查看流水线状态"""
    name = params.get("name", "")
    if name:
        with _pipeline_lock:
            pipe = _pipelines.get(name)
        if pipe:
            return {"ok": True, "pipeline": name, "status": pipe.get("status"), "steps": len(pipe.get("steps", []))}
        return {"ok": False, "error": f"流水线 {name} 不存在"}

    return {"ok": True, "pipelines": list(_pipelines.keys())}

def do_auto_chain(params):
    """自主吞噬→进化→健康检查流水线 — 一键启动完整自主维护周期"""
    steps = [
        {"cap": "devourer", "action": "devour", "params": {}},
        {"cap": "self_evolve", "action": "evolve", "params": {}},
        {"cap": "health_dashboard", "action": "check", "params": {}},
    ]
    return do_run({
        "name": params.get("name", "auto_chain"),
        "steps": steps,
        "retries": params.get("retries", 3),
        "continue_on_error": params.get("continue_on_error", False),
    })


def do_schedule_recurring(params):
    """使用smart_scheduler调度定期流水线 — cron风格重复执行"""
    name = params.get("name", f"recurring_{int(time.time())}")
    steps = params.get("steps", [])
    cron_expr = params.get("cron", "0 */6 * * *")

    if not steps:
        return {"ok": False, "error": "缺少 steps 参数"}

    pipeline = {
        "name": name, "steps": steps, "cron": cron_expr,
        "created": datetime.now().isoformat(), "status": "scheduled",
    }

    fpath = PIPELINE_DIR / f"{name}.json"
    fpath.write_text(json.dumps(pipeline, ensure_ascii=False, indent=2), encoding="utf-8")

    with _pipeline_lock:
        _pipelines[name] = pipeline

    sched_result = _call_cap("smart_scheduler", "schedule", {
        "task": f"python {CAPS_DIR / 'auto_pipeline' / 'run.py'} run {json.dumps({'name': name}, ensure_ascii=False)}",
        "priority": params.get("priority", 5),
    })

    return {
        "ok": True,
        "cap": "auto_pipeline",
        "action": "schedule_recurring",
        "domain": "运维域",
        "pipeline": name,
        "cron": cron_expr,
        "step_count": len(steps),
        "scheduler_task": sched_result.get("task_id"),
    }


HANDLERS = {"define": do_define, "run": do_run, "status": do_status,
            "auto_chain": do_auto_chain, "schedule_recurring": do_schedule_recurring}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "status"
    params_str = sys.argv[2] if len(sys.argv) > 2 else "{}"
    try:
        params = json.loads(params_str)
    except Exception:
        params = {}
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
