# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
caps/autonomous_loop/run.py — 自主执行循环引擎
===============================================
宪法第八条之二实现：
  ① task_mind 分钟级分解 → ② sub_agent_mgr 隔离子代理执行 →
  ③ circuit_breaker 门禁验证 → ④ self_evolve 吸收学习 →
  ⑤ 反复循环直到完美交付

用法:
  python caps/autonomous_loop/run.py start_loop
  python caps/autonomous_loop/run.py status
  python caps/autonomous_loop/run.py inject_task '{"goal":"监控A股3天"}'
"""
import sys, json, os, time, threading, subprocess, logging
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

LOOP_DIR = Path.home() / ".gbt" / "autonomous_loop"
LOOP_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = LOOP_DIR / "loop_state.json"

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
L = logging.getLogger("AutonomousLoop")

# 全局状态
_loop_running = False
_loop_thread = None
_iteration = 0
_completed_tasks = []
_pending_tasks = []
_max_iterations = 100  # 安全上限


def _call_cap(cap_name: str, action: str, params: dict = None, timeout: int = 60) -> dict:
    """调用能力模块"""
    run_py = ROOT / "caps" / cap_name / "run.py"
    if not run_py.exists():
        return {"ok": False, "error": f"cap {cap_name} 不存在"}
    try:
        args = [sys.executable, str(run_py), action]
        if params:
            args.append(json.dumps(params, ensure_ascii=False))
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout, cwd=str(ROOT))
        return json.loads((r.stdout or "{}").strip())
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"超时({timeout}s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def _breaker_check(cap_name: str, action: str) -> bool:
    """熔断器检查 — 调用前确认允许"""
    result = _call_cap("circuit_breaker", "enforce_before_call",
                       {"cap_name": cap_name, "action": action}, timeout=5)
    return result.get("allowed", True)


def _breaker_report(cap_name: str, success: bool):
    """熔断器报告 — 调用后报告结果"""
    _call_cap("circuit_breaker", "report_result",
              {"cap_name": cap_name, "success": success}, timeout=5)


def _compile_plan(goal: str) -> list:
    """调用 task_mind 分解目标为执行计划"""
    try:
        result = _call_cap("task_mind", "plan", {"goal": goal, "mode": "detailed"}, timeout=30)
        if result.get("ok") and result.get("steps"):
            return result["steps"]
    except Exception as e:
        L.warning(f"task_mind 规划失败: {e}")

    # 降级：简单分解
    return [{"description": goal, "cap": "auto_resolver", "action": "resolve",
             "params": {"task": goal}}]


def _execute_step(step: dict) -> dict:
    """执行单个步骤，带熔断保护"""
    cap_name = step.get("cap", "auto_resolver")
    action = step.get("action", "resolve")
    params = step.get("params", {})

    if not _breaker_check(cap_name, action):
        return {"ok": False, "error": "熔断器拒绝执行"}

    L.info(f"  🔧 执行: {cap_name}/{action}")
    result = _call_cap(cap_name, action, params, timeout=120)

    _breaker_report(cap_name, result.get("ok", False))
    return result


def _learn_from_result(goal: str, step: dict, result: dict):
    """从执行结果中学习"""
    try:
        _call_cap("self_evolve", "capture", {
            "event": "autonomous_step",
            "goal": goal,
            "step": step.get("description", ""),
            "cap": step.get("cap", ""),
            "success": result.get("ok", False),
            "detail": str(result)[:500]
        }, timeout=10)
    except Exception:
        pass


def _save_state():
    """持久化循环状态"""
    STATE_FILE.write_text(json.dumps({
        "iteration": _iteration,
        "completed": len(_completed_tasks),
        "pending": len(_pending_tasks),
        "last_update": datetime.now().isoformat(),
        "running": _loop_running
    }, ensure_ascii=False, indent=2))


def _loop_body():
    """单次循环迭代"""
    global _iteration, _completed_tasks, _pending_tasks

    _iteration += 1
    L.info(f"━━━ 自主循环 第{_iteration}轮 ━━━")

    # 1. 检查待处理任务
    if not _pending_tasks:
        L.info("  队列为空，等待新任务...")
        _save_state()
        return

    # 2. 取最高优先级任务
    task = _pending_tasks.pop(0)
    goal = task.get("goal", task.get("description", "unknown"))
    L.info(f"  📋 任务: {goal[:80]}")

    # 3. 思维导图分解
    steps = _compile_plan(goal)
    L.info(f"  🗺️ 分解为 {len(steps)} 步")

    # 4. 逐步执行
    all_passed = True
    for i, step in enumerate(steps):
        L.info(f"  [{i+1}/{len(steps)}] {step.get('description', step.get('action', '?'))[:60]}")

        result = _execute_step(step)

        if result.get("ok"):
            L.info(f"    ✅ 通过")
            _learn_from_result(goal, step, result)
        else:
            L.warning(f"    ❌ 失败: {result.get('error', 'unknown')[:100]}")
            all_passed = False
            # 卡点自主解析
            resolution = _call_cap("auto_resolver", "resolve",
                                   {"task": goal, "failed_step": step, "error": result}, timeout=60)
            if resolution.get("ok"):
                L.info(f"    🔄 自动解析成功，重试")
                result = _execute_step(step)
                all_passed = result.get("ok", False)

        if not all_passed:
            break

    # 5. 记录结果
    task["result"] = "passed" if all_passed else "failed"
    task["completed_at"] = datetime.now().isoformat()
    _completed_tasks.append(task)

    # 6. 触发自进化
    if all_passed:
        _call_cap("self_evolve", "evolve", timeout=30)

    _save_state()
    L.info(f"  {'✅ 全部通过' if all_passed else '❌ 存在失败'}")


def _loop_thread_fn(interval: int = 10):
    """循环线程主函数"""
    global _loop_running
    L.info("🚀 自主执行循环启动")
    while _loop_running:
        try:
            _loop_body()
        except Exception as e:
            L.error(f"循环异常: {e}")
        time.sleep(interval)


def do_start_loop(params: dict = None) -> dict:
    """启动自主执行循环"""
    global _loop_running, _loop_thread
    if _loop_running:
        return {"ok": True, "status": "already_running", "iteration": _iteration}

    params = params or {}
    interval = params.get("interval", 10)
    initial_tasks = params.get("tasks", [])

    for task in initial_tasks:
        _pending_tasks.append({"goal": task if isinstance(task, str) else task.get("goal", str(task)),
                               "added_at": datetime.now().isoformat()})

    _loop_running = True
    _loop_thread = threading.Thread(target=_loop_thread_fn, args=(interval,), daemon=True, name="autonomous-loop")
    _loop_thread.start()

    L.info(f"🚀 自主循环已启动 — 间隔{interval}s")
    return {"ok": True, "status": "started", "interval": interval, "pending": len(_pending_tasks)}


def do_stop_loop(params: dict = None) -> dict:
    """停止自主执行循环"""
    global _loop_running
    _loop_running = False
    _save_state()
    L.info("⏸️ 自主循环已停止")
    return {"ok": True, "status": "stopped", "iterations": _iteration, "completed": len(_completed_tasks)}


def do_status(params: dict = None) -> dict:
    """查看循环状态"""
    return {
        "ok": True,
        "running": _loop_running,
        "iteration": _iteration,
        "completed_tasks": len(_completed_tasks),
        "pending_tasks": len(_pending_tasks),
        "recent_completed": [t.get("goal", "")[:60] for t in _completed_tasks[-5:]],
        "pending_goals": [t.get("goal", "")[:60] for t in _pending_tasks[:5]]
    }


def do_inject_task(params: dict = None) -> dict:
    """注入新任务到运行中的循环"""
    params = params or {}
    goal = params.get("goal", params.get("task", ""))
    if not goal:
        return {"ok": False, "error": "缺少 goal 参数"}

    task = {"goal": goal, "added_at": datetime.now().isoformat()}
    _pending_tasks.append(task)
    L.info(f"📥 任务注入: {goal[:80]}")
    return {"ok": True, "injected": True, "goal": goal[:100], "queue_depth": len(_pending_tasks)}


HANDLERS = {
    "start_loop": do_start_loop,
    "stop_loop": do_stop_loop,
    "status": do_status,
    "inject_task": do_inject_task,
}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except Exception:
            pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知动作: {action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
