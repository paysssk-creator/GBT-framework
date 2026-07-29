# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/autonomous_boot.py — GBT自主模式统一启动入口
===================================================
一键启动GBT全部自主能力：
  1. boot.boot()           — 标准启动自检
  2. session_resume        — 恢复上次会话状态
  3. event_wiring.wire_all — 订阅所有事件处理器
  4. daemon_launcher       — 启动心跳+调度器守护进程
  5. autonomous_loop       — 启动自主执行循环
  6. web_api (可选)        — 启动管理HTTP接口

用法:
  python brain/autonomous_boot.py              # 全部启动
  python brain/autonomous_boot.py --no-loop     # 跳过自主循环
  python brain/autonomous_boot.py --no-api      # 跳过管理API
  python brain/autonomous_boot.py --dry-run     # 仅检查，不实际启动

环境变量:
  GBT_DRY_RUN=1      演练模式
  GBT_SKIP_LOOP=1    跳过自主循环
  GBT_SKIP_API=1     跳过管理API
  GBT_API_PORT=9120  管理API端口
"""
import sys, os, json, time, subprocess, logging
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from brain.logging_pipeline import init_logging, get_logger, start_trace, end_trace
init_logging()
L = get_logger("AutonomousBoot")

import signal as _signal
def _handle_signal(signum, frame):
    """邻域接入: daemon_launcher 级联清理 — SIGTERM/SIGINT"""
    sig_name = _signal.Signals(signum).name
    L.warning("收到 %s — 开始级联清理...", sig_name)
    shutdown()
    L.info("级联清理完成，退出")
    sys.exit(0)
_signal.signal(_signal.SIGTERM, _handle_signal)
_signal.signal(_signal.SIGINT, _handle_signal)

# 后台子进程追踪
_bg_processes: list = []


def _call_cap(cap_name: str, action: str, params: dict = None, timeout: int = 30) -> dict:
    from brain.chain_kernel import enforce_chain
    enforce_chain(f"autonomous_boot.call_{cap_name}")

    """同步调用能力模块（用于短命令如 start_all, start_loop）"""
    run_py = ROOT / "caps" / cap_name / "run.py"
    if not run_py.exists():
        return {"ok": False, "error": f"cap '{cap_name}' 不存在"}
    try:
        args = [sys.executable, str(run_py), action]
        if params:
            args.append(json.dumps(params, ensure_ascii=False))
        r = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout,
            cwd=str(ROOT), encoding="utf-8", errors="replace"
        )
        stdout = (r.stdout or "").strip()
        if stdout:
            return json.loads(stdout)
        return {"ok": False, "error": (r.stderr or "无输出")[:200]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "超时"}
    except json.JSONDecodeError:
        return {"ok": False, "error": f"JSON解析失败: {(r.stdout or '')[:100]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def _launch_cap_bg(cap_name: str, action: str, params: dict = None) -> dict:
    """后台启动能力模块（用于长时间运行的服务如 web_api serve）"""
    run_py = ROOT / "caps" / cap_name / "run.py"
    if not run_py.exists():
        return {"ok": False, "error": f"cap '{cap_name}' 不存在"}
    try:
        args = [sys.executable, str(run_py), action]
        if params:
            args.append(json.dumps(params, ensure_ascii=False))
        proc = subprocess.Popen(
            args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            cwd=str(ROOT)
        )
        _bg_processes.append(proc)
        return {"ok": True, "pid": proc.pid, "status": "background"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def _log_step_header(step_num: int, name: str):
    """统一步骤日志格式"""
    L.info(f"━━━ Step {step_num}: {name} ━━━")


# ═══════════════════════════════════════════════════
#  步骤函数
# ═══════════════════════════════════════════════════

def step1_boot() -> dict:
    """Step 1: 标准启动自检 — 三层认知闭环 + 四脑协作 + 邻域感知"""
    _log_step_header(1, "启动自检")
    try:
        from brain.boot import boot
        result = boot()
        ok = result.get("ok", False)
        summary = result.get("summary", "")
        L.info(f"  {'✅' if ok else '❌'} 自检{'通过' if ok else '未通过'}: {summary}")
        return {
            "name": "boot",
            "ok": ok,
            "layers": result.get("layers", {}),
            "summary": summary
        }
    except ImportError:
        L.warning("  ⚠️ brain.boot 模块不可用，跳过启动自检")
        return {"name": "boot", "ok": False, "error": "模块不可用", "skipped": True}
    except Exception as e:
        L.warning(f"  ⚠️ 启动自检失败(非致命): {e}")
        return {"name": "boot", "ok": False, "error": str(e)[:200], "skipped": True}


def step2_session_resume() -> dict:
    """Step 2: 恢复会话状态 — 加载上次持久化的 TaskGraph"""
    _log_step_header(2, "会话恢复")
    try:
        from brain.session_resume import resume
        result = resume()
        resumed = result.get("resumed", False)
        tasks = result.get("pending_tasks", 0)
        L.info(f"  {'📂' if resumed else '🆕'} 恢复={'是' if resumed else '否'}, 待处理={tasks}")
        return {
            "name": "session_resume",
            "ok": True,
            "resumed": resumed,
            "pending_tasks": tasks
        }
    except ImportError:
        L.warning("  ⚠️ brain.session_resume 模块不可用，跳过会话恢复")
        return {"name": "session_resume", "ok": False, "error": "模块不可用", "skipped": True}
    except Exception as e:
        L.warning(f"  ⚠️ 会话恢复失败(非致命): {e}")
        return {"name": "session_resume", "ok": False, "error": str(e)[:100], "skipped": True}


def step3_event_wiring() -> dict:
    """Step 3: 事件总线接线 — 订阅所有默认事件处理器"""
    _log_step_header(3, "事件接线")
    try:
        from brain.event_wiring import wire_all
        result = wire_all()
        handler_count = result.get("handler_count", 0)
        topics = result.get("topics", [])
        L.info(f"  🔌 {handler_count} 个处理器已接线, 主题: {', '.join(topics) if topics else '无'}")
        return {
            "name": "event_wiring",
            "ok": True,
            "handler_count": handler_count,
            "topics": topics
        }
    except ImportError:
        L.warning("  ⚠️ brain.event_wiring 模块不可用，跳过事件接线")
        return {"name": "event_wiring", "ok": False, "error": "模块不可用", "skipped": True}
    except Exception as e:
        L.warning(f"  ⚠️ 事件接线失败(非致命): {e}")
        return {"name": "event_wiring", "ok": False, "error": str(e)[:100], "skipped": True}


def step4_daemons() -> dict:
    """Step 4: 启动守护进程 — heartbeat + scheduler worker"""
    _log_step_header(4, "守护进程")
    result = _call_cap("daemon_launcher", "start_all", timeout=15)
    ok = result.get("ok", False)
    if ok:
        detail = result.get("detail", {})
        started = result.get("started", [])
        L.info(f"  ✅ daemon_launcher: {len(started)} 个守护进程已启动")
    else:
        L.info(f"  ⚠️ daemon_launcher 未启动: {result.get('error', '未知')}")
    return {"name": "daemons", "ok": ok, "detail": result}


def step5_autonomous_loop() -> dict:
    """Step 5: 启动自主执行循环 — 定期编译+执行任务计划"""
    _log_step_header(5, "自主循环")
    result = _call_cap("autonomous_loop", "start_loop",
                       {"interval": 15}, timeout=10)
    ok = result.get("ok", False)
    status = result.get("status", "unknown")
    interval = result.get("interval", "?")
    if ok:
        L.info(f"  🚀 自主循环已启动: 间隔={interval}s, 状态={status}")
    else:
        L.info(f"  ⚠️ 自主循环未启动: {result.get('error', status)}")
    return {"name": "autonomous_loop", "ok": ok, "status": status, "interval": interval}


def step6_web_api(port: int = 9120) -> dict:
    """Step 6: 管理API — 后台启动HTTP管理接口（非阻塞）"""
    _log_step_header(6, "管理API")
    result = _launch_cap_bg("web_api", "serve", {"port": port, "silent": True})
    ok = result.get("ok", False)
    if ok:
        L.info(f"  🌐 管理API 后台启动: http://localhost:{port}/health (PID={result.get('pid')})")
    else:
        L.info(f"  ⚠️ 管理API未启动: {result.get('error', '未知')}")
    return {"name": "web_api", "ok": ok, "port": port, "detail": result}


# ═══════════════════════════════════════════════════
#  统一启动入口
# ═══════════════════════════════════════════════════

def _resolve_config(
    dry_run: Optional[bool] = None,
    skip_loop: Optional[bool] = None,
    skip_api: Optional[bool] = None,
    api_port: Optional[int] = None,
) -> dict:
    """合并 CLI 参数与环境变量配置"""
    env_true = lambda k: os.environ.get(k, "").strip().lower() in ("1", "true", "yes", "on")

    if dry_run is None:
        dry_run = env_true("GBT_DRY_RUN")
    if skip_loop is None:
        skip_loop = env_true("GBT_SKIP_LOOP")
    if skip_api is None:
        skip_api = env_true("GBT_SKIP_API")
    if api_port is None:
        api_port = int(os.environ.get("GBT_API_PORT", "9120"))

    return {
        "dry_run": dry_run or False,
        "skip_loop": skip_loop or False,
        "skip_api": skip_api or False,
        "api_port": api_port,
    }


def autonomous_boot(
    dry_run: Optional[bool] = None,
    skip_loop: Optional[bool] = None,
    skip_api: Optional[bool] = None,
    api_port: Optional[int] = None,
) -> dict:
    """GBT自主模式统一启动

    Args:
        dry_run: 演练模式 — 仅检查不实际启动
        skip_loop: 跳过自主执行循环
        skip_api: 跳过管理API
        api_port: 管理API端口 (默认 9120)

    Returns:
        {"ok": bool, "steps_passed": int, "steps_total": int,
         "results": [...], "mode": str, "components": {...}}
    """
    cfg = _resolve_config(dry_run, skip_loop, skip_api, api_port)
    dry_run = cfg["dry_run"]
    skip_loop = cfg["skip_loop"]
    skip_api = cfg["skip_api"]
    api_port = cfg["api_port"]

    L.info("═" * 50)
    L.info("  GBT 小土豆 · 自主模式启动")
    L.info(f"  时间: {__import__('datetime').datetime.now().isoformat()}")
    L.info(f"  模式: {'🔍 演练' if dry_run else '🚀 生产'}"
           f"  | 自主循环: {'⏭ 跳过' if skip_loop else '✅ 启用'}"
           f"  | 管理API: {'⏭ 跳过' if skip_api else f'✅ 端口 {api_port}'}")
    L.info("═" * 50)

    results = []

    # Step 1-3 始终执行（即使 dry_run 也做检查）
    always_steps = [
        ("step1_boot", step1_boot),
        ("step2_session_resume", step2_session_resume),
        ("step3_event_wiring", step3_event_wiring),
    ]

    for step_name, step_fn in always_steps:
        try:
            result = step_fn()
        except Exception as e:
            L.warning(f"  ⚠️ {step_name} 异常(非致命): {e}")
            result = {"name": step_name, "ok": False, "error": str(e)[:200], "skipped": True}
        results.append(result)
        time.sleep(0.3)

    # Step 4-6 仅在非演练模式下执行
    if dry_run:
        L.info("\n🔍 演练模式 — Step 4-6 跳过（仅检查）\n")
        for label in ("daemons", "autonomous_loop", "web_api"):
            results.append({"name": label, "ok": True, "skipped": "dry_run"})
    else:
        # Step 4: 守护进程
        try:
            results.append(step4_daemons())
        except Exception as e:
            L.warning(f"  ⚠️ 守护进程启动异常: {e}")
            results.append({"name": "daemons", "ok": False, "error": str(e)[:200]})
        time.sleep(0.3)

        # Step 5: 自主循环
        if skip_loop:
            L.info("━━━ Step 5: 自主循环 ━━━")
            L.info("  ⏭ 已跳过 (--no-loop / GBT_SKIP_LOOP)")
            results.append({"name": "autonomous_loop", "ok": True, "skipped": True})
        else:
            try:
                results.append(step5_autonomous_loop())
            except Exception as e:
                L.warning(f"  ⚠️ 自主循环启动异常: {e}")
                results.append({"name": "autonomous_loop", "ok": False, "error": str(e)[:200]})
        time.sleep(0.3)

        # Step 6: 管理API
        if skip_api:
            L.info("━━━ Step 6: 管理API ━━━")
            L.info("  ⏭ 已跳过 (--no-api / GBT_SKIP_API)")
            results.append({"name": "web_api", "ok": True, "skipped": True})
        else:
            try:
                results.append(step6_web_api(port=api_port))
            except Exception as e:
                L.warning(f"  ⚠️ 管理API启动异常: {e}")
                results.append({"name": "web_api", "ok": False, "error": str(e)[:200]})

    # ── 汇总 ──
    non_skipped = [r for r in results if not r.get("skipped")]
    passed = sum(1 for r in results if r.get("ok"))
    total = len(results)
    skipped = sum(1 for r in results if r.get("skipped"))

    L.info(f"\n{'═' * 50}")
    L.info(f"  启动完成: {passed}/{total} 步骤通过"
           f"{f' ({skipped} 跳过)' if skipped else ''}")
    _print_component_status(results)
    L.info(f"{'═' * 50}")

    summary = {
        "ok": all(r.get("ok") for r in results),
        "steps_passed": passed,
        "steps_total": total,
        "steps_skipped": skipped,
        "results": results,
        "mode": "dry_run" if dry_run else "production",
        "components": _build_component_map(results),
    }

    # 持久化启动日志
    try:
        BOOT_LOG.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8"
        )
    except Exception:
        pass

    return summary


def _build_component_map(results: list) -> dict:
    """构建组件状态映射"""
    status_icon = {
        True: "✅ 运行中",
        False: "❌ 失败",
        "skipped": "⏭ 跳过",
        "dry_run": "🔍 未启动",
    }
    comps = {}
    for r in results:
        name = r.get("name", "?")
        if r.get("skipped"):
            reason = "dry_run" if r.get("skipped") == "dry_run" else "user_skip"
            comps[name] = status_icon.get(reason, "⏭ 跳过")
        else:
            comps[name] = status_icon.get(r.get("ok"), "❓ 未知")
    return comps


def _print_component_status(results: list):
    """打印组件状态一览"""
    L.info("  组件状态:")
    for r in results:
        name = r.get("name", "?")
        if r.get("skipped"):
            icon = "🔍" if r.get("skipped") == "dry_run" else "⏭"
            L.info(f"    {icon} {name}: 跳过")
        elif r.get("ok"):
            L.info(f"    ✅ {name}: 正常")
        else:
            L.info(f"    ❌ {name}: {r.get('error', r.get('status', '失败'))}")


def shutdown():
    """优雅关闭：终止所有后台子进程"""
    global _bg_processes
    for proc in _bg_processes:
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    _bg_processes.clear()
    L.info("所有后台进程已终止")

import atexit as _atexit
_atexit.register(shutdown)


# ═══════════════════════════════════════════════════
#  CLI 入口
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(
        description="GBT自主模式统一启动",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                    全部启动
  %(prog)s --no-loop          跳过自主循环
  %(prog)s --no-api           跳过管理API
  %(prog)s --dry-run          仅检查，不实际启动
  %(prog)s --api-port 8080    使用自定义API端口

环境变量: GBT_DRY_RUN, GBT_SKIP_LOOP, GBT_SKIP_API, GBT_API_PORT
        """
    )
    p.add_argument("--dry-run", action="store_true", help="仅检查，不启动守护进程")
    p.add_argument("--no-loop", action="store_true", help="跳过自主执行循环")
    p.add_argument("--no-api", action="store_true", help="跳过管理API")
    p.add_argument("--api-port", type=int, default=None, help="管理API端口 (默认 9120)")

    args = p.parse_args()

    result = autonomous_boot(
        dry_run=args.dry_run or None,
        skip_loop=args.no_loop or None,
        skip_api=args.no_api or None,
        api_port=args.api_port,
    )

    if not result["ok"]:
        sys.exit(1)
