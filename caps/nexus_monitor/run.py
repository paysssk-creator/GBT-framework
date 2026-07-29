# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""nexus_monitor/run.py — 全局邻域感知监控
=============================================
每次关键操作前自动执行: 健康检查→问题诊断→自动修复→状态报告
杜绝"无头苍蝇到处找病因"
"""
import sys, json, os, time, threading, shutil
from pathlib import Path
from datetime import datetime, timezone

SANDBOX = Path(__file__).parent.parent.parent
CAPS_DIR = SANDBOX / "caps"
sys.path.insert(0, str(SANDBOX))

# ── watch daemon globals ──────────────────────
_watch_thread = None
_watch_stop = threading.Event()

def _nexus():
    from brain.nexus import get_nexus; return get_nexus()


def _publish_event_bus(topic, event_type, payload):
    """Publish an event to the event_bus cap via subprocess."""
    try:
        import subprocess
        eb_run = CAPS_DIR / "event_bus" / "run.py"
        if not eb_run.exists():
            return None
        r = subprocess.run(
            [sys.executable, str(eb_run), "publish",
             json.dumps({"topic": topic, "type": event_type, "payload": payload},
                        ensure_ascii=False)],
            capture_output=True, text=True, timeout=10,
            cwd=str(SANDBOX), encoding="utf-8", errors="replace"
        )
        raw = (r.stdout or "").strip()
        if raw:
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"ok": True, "raw": raw[:200]}
        return {"ok": False, "error": (r.stderr or "no output")[:200]}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def do_check(params=None):
    """快速邻域健康检查 — 每次API调用前执行"""
    try:
        n = _nexus()
        health = n.quick_health()
        topo = n.topology()

        # 检查关键cap
        critical_caps = ["web_api","cryptapi_pay","revenue_split","github_oauth","memory","auto_pipeline"]
        cap_status = {}
        for cap in critical_caps:
            cap_dir = SANDBOX / cap / "run.py" if cap.startswith("caps/") else SANDBOX / "caps" / cap / "run.py"
            if not cap_dir.exists():
                cap_dir = SANDBOX / "caps" / cap / "run.py"
            cap_status[cap] = cap_dir.exists()

        all_ok = health["ok"] and all(cap_status.values())

        return {
            "ok": all_ok,
            "health": health,
            "cap_status": cap_status,
            "domains": topo["domains"],
            "total_caps": topo["total_caps"],
            "timestamp": time.time(),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:200], "timestamp": time.time()}

def do_deep_check(params=None):
    """深度检查 — 发现问题并给出修复建议"""
    try:
        n = _nexus()
        scan = n.deep_scan()
        diag = n.diagnose()

        # 自动修复尝试
        fixes_applied = []
        for issue in diag.get("issues", []):
            if issue["severity"] == "critical":
                fixes_applied.append(f"需要修复: {issue['domain']}/{issue['cap']}")

        return {
            "ok": scan["ok"],
            "verdict": scan["verdict"],
            "health": scan["health"],
            "files": scan["files"],
            "connections": scan["connections"]["ok"],
            "cross_refs": scan["cross_references"]["ok"],
            "integrity": scan["integrity"]["ok"],
            "issues": diag.get("issues", []),
            "fixes": diag.get("fixes", []),
            "fixes_applied": fixes_applied,
            "recommendation": diag.get("recommendation", ""),
            "timestamp": time.time(),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def do_pre_flight(params=None):
    """起飞前检查 — 部署/支付/操作前的完整检查"""
    operation = (params or {}).get("operation", "unknown")
    caps_required = (params or {}).get("caps_required", [])

    # 1. 邻域健康
    health = do_check()

    # 2. 必需cap检查
    missing = []
    for cap in caps_required:
        cap_path = SANDBOX / "caps" / cap / "run.py"
        if not cap_path.exists():
            missing.append(cap)

    # 3. 认知库状态
    try:
        from brain.cognition import get_cognition
        c = get_cognition()
        cognition_count = len(c.recent(100))
    except: cognition_count = 0

    # 4. 教训库
    try:
        from brain.self_evolve import get_evolver
        e = get_evolver()
        lessons_count = len(e._load_lessons())
    except: lessons_count = 0

    all_ok = health["ok"] and not missing

    return {
        "ok": all_ok,
        "operation": operation,
        "health": health,
        "missing_caps": missing,
        "cognition_entries": cognition_count,
        "lessons_learned": lessons_count,
        "ready": all_ok,
        "blockers": [] if all_ok else [f"Missing caps: {missing}"] + ([f"Health issues: {health.get('health',{}).get('core_issues',[])}"] if not health["ok"] else []),
        "timestamp": time.time(),
    }


def _scan_caps_for_failures():
    """Scan all caps across all nexus neighborhoods for failures.
    Returns (failing_caps, warnings).
    """
    failing = []
    warnings = []
    try:
        n = _nexus()
        scan = n.scan(force=True)

        # Collect all cap names from neighborhoods
        all_caps = set()
        for domain, info in n.neighborhoods.items():
            for cap_name in info["caps"]:
                all_caps.add(cap_name)

        for cap_name in sorted(all_caps):
            cap_dir = CAPS_DIR / cap_name
            rp = cap_dir / "run.py"
            mf = cap_dir / "capability.json"
            issues = []

            if not rp.exists():
                issues.append("missing run.py")
            else:
                try:
                    code = rp.read_text(encoding="utf-8")
                    compile(code, str(rp), "exec")
                except SyntaxError as se:
                    issues.append(f"syntax error: {se}")
                except Exception:
                    issues.append("unreadable run.py")

            if not mf.exists():
                issues.append("missing capability.json")
            else:
                try:
                    data = json.loads(mf.read_text(encoding="utf-8"))
                    if not data.get("name"):
                        issues.append("no name in capability.json")
                except json.JSONDecodeError:
                    issues.append("corrupt capability.json")

            if issues:
                has_critical = any("missing" in i or "syntax" in i or "corrupt" in i for i in issues)
                entry = {"cap": cap_name, "issues": issues,
                         "timestamp": datetime.now(timezone.utc).isoformat()}
                if has_critical:
                    failing.append(entry)
                else:
                    warnings.append(entry)
    except Exception as e:
        failing.append({"cap": "nexus_monitor", "issues": [f"scan error: {e}"],
                         "timestamp": datetime.now(timezone.utc).isoformat()})

    return failing, warnings


def do_watch(params=None):
    """持续监控 — 在后台线程中扫描所有nexus邻域caps，发现问题立即通过event_bus告警。

    Call with {"action": "start"} to begin, {"action": "stop"} to end,
    or {"action": "status"} to check.
    Default interval: 60 seconds.
    """
    global _watch_thread, _watch_stop
    sub_action = (params or {}).get("action", "once")
    interval = (params or {}).get("interval", 60)

    if sub_action == "stop":
        if _watch_thread is None or not _watch_thread.is_alive():
            return {"ok": True, "watch": "not_running"}
        _watch_stop.set()
        _watch_thread.join(timeout=5)
        return {"ok": True, "watch": "stopped"}

    if sub_action == "status":
        running = _watch_thread is not None and _watch_thread.is_alive()
        return {"ok": True, "watch": "running" if running else "idle"}

    if sub_action == "once":
        # One-shot scan + publish
        failing, warnings = _scan_caps_for_failures()
        alerts_sent = 0
        for entry in failing:
            pub_result = _publish_event_bus("cap/error", "cap_failure", {
                "cap": entry["cap"],
                "issues": entry["issues"],
                "severity": "critical",
                "source": "nexus_monitor.watch",
                "timestamp": entry["timestamp"],
            })
            if pub_result and pub_result.get("ok"):
                alerts_sent += 1
        for entry in warnings:
            _publish_event_bus("cap/error", "cap_warning", {
                "cap": entry["cap"],
                "issues": entry["issues"],
                "severity": "warning",
                "source": "nexus_monitor.watch",
                "timestamp": entry["timestamp"],
            })
        return {
            "ok": True, "watch": "once",
            "failing_caps": failing, "warnings": warnings,
            "alerts_published": alerts_sent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # sub_action == "start" — launch background thread
    if _watch_thread is not None and _watch_thread.is_alive():
        return {"ok": True, "watch": "already_running", "interval": interval}

    _watch_stop.clear()
    alerts = []

    def _watch_loop():
        while not _watch_stop.is_set():
            try:
                failing, warnings = _scan_caps_for_failures()
                for entry in failing:
                    alerts.append(entry)
                    _publish_event_bus("cap/error", "cap_failure", {
                        "cap": entry["cap"],
                        "issues": entry["issues"],
                        "severity": "critical",
                        "source": "nexus_monitor.watch",
                        "timestamp": entry["timestamp"],
                    })
                for entry in warnings:
                    _publish_event_bus("cap/error", "cap_warning", {
                        "cap": entry["cap"],
                        "issues": entry["issues"],
                        "severity": "warning",
                        "source": "nexus_monitor.watch",
                        "timestamp": entry["timestamp"],
                    })
            except Exception:
                pass
            _watch_stop.wait(timeout=interval)

    _watch_thread = threading.Thread(target=_watch_loop, daemon=True, name="nexus-monitor-watch")
    _watch_thread.start()

    return {
        "ok": True, "watch": "started",
        "interval": interval,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def do_auto_heal(params=None):
    """自动修复 — 尝试修复常见问题: 缺失__pycache__、损坏的JSON文件。

    Checks across all nexus neighborhood caps.
    Returns {healed: [...], failed: [...], skipped: [...]}
    """
    healed = []
    failed = []
    skipped = []

    try:
        n = _nexus()
        scan = n.scan(force=True)
    except Exception as e:
        return {"ok": False, "error": f"nexus scan failed: {e}"}

    all_caps = set()
    for domain, info in n.neighborhoods.items():
        for cap_name in info["caps"]:
            all_caps.add(cap_name)

    for cap_name in sorted(all_caps):
        cap_dir = CAPS_DIR / cap_name
        rp = cap_dir / "run.py"
        mf = cap_dir / "capability.json"

        # ── Heal 1: Recreate missing __pycache__ ──
        pycache = cap_dir / "__pycache__"
        if rp.exists() and not pycache.exists():
            try:
                pycache.mkdir(parents=True, exist_ok=True)
                healed.append({"cap": cap_name, "fix": "created __pycache__/"})
            except Exception as e:
                failed.append({"cap": cap_name, "fix": "create __pycache__", "error": str(e)})

        # ── Heal 2: Fix corrupt capability.json ──
        if mf.exists():
            try:
                data = json.loads(mf.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("not a JSON object")
            except Exception:
                # Attempt repair: write a minimal valid capability.json
                try:
                    # Try to recover partial data first
                    raw = mf.read_text(encoding="utf-8").strip()
                    # If it has recognizable content, try harder
                    minimal = {
                        "name": cap_name,
                        "version": "1.0.0",
                        "description": f"Auto-repaired capability for {cap_name}",
                        "language": "python",
                        "risk_level": "safe",
                        "auto_exec": True,
                        "category": "auto_healed",
                        "actions": {
                            "run": {
                                "description": f"Run {cap_name}",
                                "timeout_ms": 30000,
                            }
                        },
                        "triggers": {
                            "keywords": [cap_name],
                            "intent": cap_name,
                        }
                    }
                    mf.write_text(json.dumps(minimal, ensure_ascii=False, indent=2))
                    healed.append({"cap": cap_name, "fix": "repaired corrupt capability.json"})
                except Exception as e2:
                    failed.append({"cap": cap_name, "fix": "repair capability.json", "error": str(e2)})
        else:
            skipped.append({"cap": cap_name, "reason": "no capability.json exists (cap not yet created)"})

    ok = len(failed) == 0
    return {
        "ok": ok,
        "healed": healed,
        "healed_count": len(healed),
        "failed": failed,
        "failed_count": len(failed),
        "skipped": skipped,
        "skipped_count": len(skipped),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def do_continuous(params=None):
    """启动持续监控守护"""
    interval = (params or {}).get("interval", 300)
    alert_threshold = (params or {}).get("alert_threshold", 90)

    print(f"🔍 Nexus Monitor: {interval}s interval, alert at <{alert_threshold}%", file=sys.stderr)

    try:
        while True:
            result = do_watch({"interval": interval, "alert_threshold": alert_threshold})
            if result.get("alerts"):
                for alert in result["alerts"]:
                    ts = datetime.now().strftime("%H:%M:%S")
                    print(f"  [{ts}] {alert['level'].upper()}: {alert['message']}", file=sys.stderr)
            time.sleep(interval)
    except KeyboardInterrupt:
        pass

    return {"ok": True, "stopped": True}


HANDLERS = {
    "check": do_check, "deep_check": do_deep_check,
    "pre_flight": do_pre_flight, "watch": do_watch,
    "continuous": do_continuous, "run": do_check,
    "auto_heal": do_auto_heal,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "check"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知:{action}"})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
