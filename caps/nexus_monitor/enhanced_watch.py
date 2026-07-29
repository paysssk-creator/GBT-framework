# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""nexus_monitor/enhanced_watch.py — 独立持续邻域监控守护

每30秒扫描所有17邻域，检测：
  - cap file 缺失 (run.py / capability.json)
  - JSON 损坏 / 格式错误
  - Python 语法/导入错误
  - 过期(stale)的 run.py
  - 缺失 __init__.py

发现即自动修复 + 通过 event_bus 发布告警到 topic 'nexus/alert'
日志写入 ~/.gbt/nexus_watch.log

启动: python caps/nexus_monitor/enhanced_watch.py [--once] [--interval 30]
"""

import sys
import json
import os
import time
import threading
import subprocess
from pathlib import Path
from datetime import datetime, timezone

SANDBOX = Path(__file__).parent.parent.parent
CAPS_DIR = SANDBOX / "caps"
sys.path.insert(0, str(SANDBOX))

LOG_DIR = Path.home() / ".gbt"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "nexus_watch.log"

# ── 全局状态 ──────────────────────────────────
_watch_stop = threading.Event()
_watch_thread = None


def _log(msg: str) -> None:
    """写入监控日志"""
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line)


def _nexus():
    """懒加载 NexusHub 单例"""
    from brain.nexus import get_nexus
    return get_nexus()


def _publish_alert(topic: str, payload: dict) -> dict | None:
    """通过 event_bus 发布告警事件"""
    try:
        eb_run = CAPS_DIR / "event_bus" / "run.py"
        if not eb_run.exists():
            _log("WARN: event_bus/run.py 不存在，无法发布告警")
            return None

        event = {
            "topic": topic,
            "type": "nexus_alert",
            "payload": payload,
        }
        r = subprocess.run(
            [sys.executable, str(eb_run), "publish", json.dumps(event, ensure_ascii=False)],
            capture_output=True, text=True, timeout=10,
            cwd=str(SANDBOX), encoding="utf-8", errors="replace",
        )
        raw = (r.stdout or "").strip()
        if raw:
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"ok": True, "raw": raw[:200]}
        return {"ok": False, "error": (r.stderr or "no output")[:200]}
    except Exception as e:
        _log(f"ERROR: event_bus 发布失败: {e}")
        return {"ok": False, "error": str(e)[:200]}


def _auto_heal_cap(cap_name: str, issues: list[str], cap_dir: Path) -> list[str]:
    """对单个 cap 尝试自动修复，返回修复日志列表"""
    healed = []
    rp = cap_dir / "run.py"
    mf = cap_dir / "capability.json"
    ip = cap_dir / "__init__.py"
    pycache = cap_dir / "__pycache__"

    for issue in issues:
        # ── Fix 1: 重建 __pycache__ ──
        if "pycache" in issue.lower() or "__pycache__" in issue.lower():
            try:
                pycache.mkdir(parents=True, exist_ok=True)
                # 尝试编译 run.py 生成 .pyc
                if rp.exists():
                    import py_compile
                    try:
                        py_compile.compile(str(rp), cfile=str(pycache / f"{rp.stem}.cpython-{sys.version_info.major}{sys.version_info.minor}.pyc"), doraise=False)
                    except Exception:
                        pass
                healed.append(f"rebuilt __pycache__ for {cap_name}")
                _log(f"  HEAL: {cap_name} → rebuilt __pycache__")
            except Exception as e:
                _log(f"  FAIL: {cap_name} → rebuild __pycache__: {e}")

        # ── Fix 2: 修复 JSON 语法 ──
        if "corrupt" in issue.lower() and "json" in issue.lower():
            if mf.exists():
                try:
                    raw = mf.read_text(encoding="utf-8").strip()
                    # 尝试修复常见问题: 尾部逗号、未闭合括号
                    fixed = _repair_json(raw)
                    json.loads(fixed)  # 验证
                    mf.write_text(fixed, encoding="utf-8")
                    healed.append(f"repaired capability.json for {cap_name}")
                    _log(f"  HEAL: {cap_name} → repaired capability.json")
                except Exception:
                    # 无法修复 → 写入最小有效 JSON
                    try:
                        minimal = {
                            "name": cap_name,
                            "version": "1.0.0",
                            "description": f"Auto-repaired capability for {cap_name}",
                            "language": "python",
                            "risk_level": "safe",
                            "auto_exec": True,
                            "category": "auto_healed",
                            "actions": {"run": {"description": f"Run {cap_name}", "timeout_ms": 30000}},
                            "triggers": {"keywords": [cap_name], "intent": cap_name},
                        }
                        mf.write_text(json.dumps(minimal, ensure_ascii=False, indent=2))
                        healed.append(f"recreated capability.json for {cap_name}")
                        _log(f"  HEAL: {cap_name} → recreated capability.json")
                    except Exception as e2:
                        _log(f"  FAIL: {cap_name} → recreate capability.json: {e2}")

        # ── Fix 3: 重建缺失 __init__.py ──
        if "missing __init__.py" in issue.lower():
            try:
                ip.write_text(
                    f"# {cap_name} — auto-generated by nexus_monitor\n"
                    f"# Created: {datetime.now(timezone.utc).isoformat()}\n",
                    encoding="utf-8"
                )
                healed.append(f"created __init__.py for {cap_name}")
                _log(f"  HEAL: {cap_name} → created __init__.py")
            except Exception as e:
                _log(f"  FAIL: {cap_name} → create __init__.py: {e}")

    return healed


def _repair_json(raw: str) -> str:
    """尝试修复常见的 JSON 损坏"""
    if not raw:
        return "{}"
    # 去除尾部逗号 (最后一个 , 在 ] 或 } 之前)
    import re
    raw = re.sub(r',\s*([}\]])', r'\1', raw)
    # 尝试补全未闭合括号
    open_braces = raw.count('{') - raw.count('}')
    open_brackets = raw.count('[') - raw.count(']')
    raw = raw.rstrip()
    raw += '}' * max(open_braces, 0)
    raw += ']' * max(open_brackets, 0)
    return raw


def run_once(scan: dict | None = None) -> dict:
    """单次扫描+修复+告警，返回报告"""
    if scan is None:
        try:
            n = _nexus()
            scan = n.scan_all(force=True)
        except Exception as e:
            _log(f"ERROR: scan_all() 失败: {e}")
            return {"ok": False, "error": str(e)}

    total_healed = 0
    total_alerts = 0
    details = []

    for domain, info in scan.get("neighborhoods", {}).items():
        for cap_name, cap in info.get("caps", {}).items():
            issues = cap.get("issues", [])
            if not issues:
                continue

            cap_dir = CAPS_DIR / cap_name

            # 发布告警
            alert_payload = {
                "cap": cap_name,
                "domain": domain,
                "issues": issues,
                "severity": "critical" if cap.get("status") == "core" else "warning",
                "source": "nexus_monitor.enhanced_watch",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            result = _publish_alert("nexus/alert", alert_payload)
            if result and result.get("ok"):
                total_alerts += 1

            # 自动修复
            healed = _auto_heal_cap(cap_name, issues, cap_dir)
            total_healed += len(healed)

            details.append({
                "cap": cap_name,
                "domain": domain,
                "issues": issues,
                "healed": healed,
            })

    report = {
        "ok": scan.get("ok", False),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "health_pct": scan.get("health_pct", 0),
        "total_caps": scan.get("total_caps", 0),
        "found": scan.get("found", 0),
        "missing": scan.get("missing", 0),
        "issues_found": scan.get("total_issues", 0),
        "alerts_published": total_alerts,
        "auto_healed": total_healed,
        "details": details,
    }
    _log(f"SCAN: {scan.get('found',0)}/{scan.get('total_caps',0)} caps OK "
         f"| {scan.get('total_issues',0)} issues | {total_healed} healed | {total_alerts} alerts")
    return report


def _watch_loop(interval: int) -> None:
    """后台监控循环"""
    _log(f"STARTED: enhanced_watch daemon (interval={interval}s)")
    while not _watch_stop.is_set():
        try:
            n = _nexus()
            scan = n.scan_all(force=True)
            run_once(scan)
        except Exception as e:
            _log(f"ERROR: watch tick failed: {e}")

        _watch_stop.wait(timeout=interval)

    _log("STOPPED: enhanced_watch daemon")


def start(interval: int = 30) -> dict:
    """启动后台监控线程"""
    global _watch_thread, _watch_stop

    if _watch_thread is not None and _watch_thread.is_alive():
        return {"ok": True, "status": "already_running", "interval": interval}

    _watch_stop.clear()
    _watch_thread = threading.Thread(
        target=_watch_loop,
        args=(interval,),
        daemon=True,
        name="nexus-enhanced-watch",
    )
    _watch_thread.start()
    _log(f"DAEMON: enhanced_watch started (interval={interval}s)")
    return {
        "ok": True,
        "status": "started",
        "interval": interval,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def stop() -> dict:
    """停止后台监控"""
    global _watch_thread, _watch_stop
    if _watch_thread is None or not _watch_thread.is_alive():
        return {"ok": True, "status": "not_running"}
    _watch_stop.set()
    _watch_thread.join(timeout=5)
    _log("DAEMON: enhanced_watch stopped")
    return {"ok": True, "status": "stopped"}


def status() -> dict:
    """查询守护状态"""
    global _watch_thread
    running = _watch_thread is not None and _watch_thread.is_alive()
    return {"ok": True, "status": "running" if running else "idle"}


# ── CLI ───────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GBT Nexus 持续邻域监控守护")
    parser.add_argument("--once", action="store_true", help="单次扫描+修复+告警，然后退出")
    parser.add_argument("--interval", type=int, default=30, help="扫描间隔(秒)，默认30")
    parser.add_argument("--daemon", action="store_true", help="后台持续运行")
    parser.add_argument("--stop", action="store_true", help="停止运行中的守护")
    parser.add_argument("--status", action="store_true", help="查询守护状态")
    args = parser.parse_args()

    if args.stop:
        print(json.dumps(stop(), ensure_ascii=False, indent=2))
    elif args.status:
        print(json.dumps(status(), ensure_ascii=False, indent=2))
    elif args.once:
        report = run_once()
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.daemon:
        result = start(interval=args.interval)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        # 保持主线程存活
        try:
            while _watch_thread and _watch_thread.is_alive():
                _watch_thread.join(1)
        except KeyboardInterrupt:
            stop()
            print("\nDaemon stopped.")
    else:
        # 默认: 单次扫描
        report = run_once()
        print(json.dumps(report, ensure_ascii=False, indent=2))
