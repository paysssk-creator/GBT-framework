# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/heartbeat.py — GBT持久心跳守护进程
==========================================
GBT的自主心跳。while True循环，每次tick:
  1. 检查 smart_scheduler 队列中到期任务
  2. 每日首次触发 devourer 吞噬引擎
  3. 发布 heartbeat/tick 事件到 event_bus
  4. 日志记录到 ~/.gbt/heartbeat.log

用法:
  python brain/heartbeat.py                  # 前台运行
  python brain/heartbeat.py --interval 30    # 自定义间隔(秒)
  python brain/heartbeat.py --once           # 单次执行后退出
"""
import sys, os, json, time, subprocess, logging, logging.handlers
from pathlib import Path
from datetime import datetime, date

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

HEARTBEAT_DIR = Path.home() / ".gbt" / "heartbeat"
HEARTBEAT_DIR.mkdir(parents=True, exist_ok=True)
HEARTBEAT_LOG = HEARTBEAT_DIR / "heartbeat.log"
PID_FILE = HEARTBEAT_DIR / "heartbeat.pid"
TODAY_MARKER = HEARTBEAT_DIR / f"devourer_ran_{date.today().isoformat()}"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.handlers.RotatingFileHandler(
            HEARTBEAT_LOG, encoding="utf-8",
            maxBytes=5*1024*1024, backupCount=3,
        ),
        logging.StreamHandler(sys.stdout)
    ]
)
L = logging.getLogger("Heartbeat")


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
        if r.returncode != 0:
            return {"ok": False, "error": r.stderr[:200]}
        return json.loads(r.stdout.strip() or "{}")
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"超时({timeout}s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def _publish_event(topic: str, data: dict):
    """发布事件到 event_bus"""
    try:
        _call_cap("event_bus", "publish", {"topic": topic, "data": data}, timeout=5)
    except Exception:
        pass


def _check_scheduler():
    """检查 smart_scheduler 到期任务并触发执行"""
    try:
        result = _call_cap("smart_scheduler", "list", timeout=5)
        if result.get("ok"):
            tasks = result.get("tasks", [])
            L.info(f"调度器: {len(tasks)} 个任务")
    except Exception as e:
        L.warning(f"调度器检查失败: {e}")


def _trigger_devourer_daily():
    """每日首次触发吞噬引擎"""
    if TODAY_MARKER.exists():
        return
    L.info("🚀 触发每日吞噬引擎...")
    try:
        result = _call_cap("devourer", "daily", timeout=300)
        if result.get("ok"):
            TODAY_MARKER.write_text(datetime.now().isoformat())
            L.info(f"✅ 吞噬完成: {result.get('summary', result.get('status', 'ok'))}")
            _publish_event("devourer/daily_done", result)
            # 触发自进化
            _call_cap("self_evolve", "evolve", timeout=30)
        else:
            L.error(f"❌ 吞噬失败: {result.get('error', 'unknown')}")
    except Exception as e:
        L.error(f"❌ 吞噬异常: {e}")


def _health_pulse():
    """健康脉冲 — 检查关键cap是否存活"""
    checks = {
        "nexus": ("brain.nexus", "quick_health"),
        "cognition": ("brain.cognition", "who_am_i"),
        "devourer": ("caps.devourer", "do_scan"),
    }
    alive = 0
    for name, (mod, func) in checks.items():
        try:
            m = __import__(mod, fromlist=[func])
            getattr(m, func)()
            alive += 1
        except Exception:
            pass
    L.debug(f"健康脉冲: {alive}/{len(checks)} 检查通过")


def _tentacle_pulse():
    """神经触手脉冲 — 穿透扫描 + 邻域注入"""
    try:
        from brain.neural_tentacle import get_tentacle
        t = get_tentacle(auto_heal=True)
        r = t.pulse()
        L.info(f"🧬 触手脉冲: {'🟢' if r['ok'] else '🔴'} 错误{r['total_errors']} 修复{r['fixes_applied']}")
        return r
    except Exception as e:
        L.warning(f"触手异常: {e}")
        return {"ok": False, "error": str(e)[:100]}


def run_heartbeat(interval: int = 60):
    """主循环 — 带启动互斥锁，防止重复实例"""
    # 互斥检查：已有存活实例则拒绝启动
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            import ctypes, ctypes.wintypes
            SYNCHRONIZE = 0x00100000
            PROCESS_QUERY_INFORMATION = 0x0400
            handle = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE | PROCESS_QUERY_INFORMATION, False, old_pid)
            if handle:
                exit_code = ctypes.wintypes.DWORD()
                ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
                ctypes.windll.kernel32.CloseHandle(handle)
                if exit_code.value == 259:  # STILL_ACTIVE
                    L.warning(f"心跳已在运行 (PID {old_pid})，拒绝重复启动")
                    return
        except (ValueError, OSError):
            pass  # PID 文件损坏或进程已死，继续启动

    PID_FILE.write_text(str(os.getpid()))
    L.info(f"💓 GBT心跳启动 — 间隔{interval}s — PID {os.getpid()}")

    tick_count = 0

    try:
        while True:
            tick_count += 1
            L.info(f"💓 Tick #{tick_count}")

            # 1. 每日吞噬
            _trigger_devourer_daily()

            # 2. 调度器检查
            _check_scheduler()

            # 3. 健康脉冲
            if tick_count % 10 == 0:  # 每10次tick做一次完整健康检查
                _health_pulse()

            # 4. 发布心跳事件
            _publish_event("heartbeat/tick", {
                "tick": tick_count,
                "time": datetime.now().isoformat(),
                "pid": os.getpid()
            })

            time.sleep(interval)

    except KeyboardInterrupt:
        L.info("💤 心跳收到停止信号，正在退出...")
    except Exception:
        L.exception("心跳异常退出")
    finally:
        try:
            if PID_FILE.exists():
                PID_FILE.unlink()
        except OSError:
            pass
        L.info("💤 心跳已停止")


def run_once():
    """单次执行 — 用于测试或手动触发"""
    L.info("💓 单次心跳脉冲")
    _trigger_devourer_daily()
    _check_scheduler()
    _health_pulse()
    L.info("✅ 单次脉冲完成")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="GBT心跳守护进程")
    p.add_argument("--interval", type=int, default=60, help="Tick间隔(秒)")
    p.add_argument("--once", action="store_true", help="单次执行后退出")
    args = p.parse_args()

    if args.once:
        run_once()
    else:
        run_heartbeat(interval=args.interval)
