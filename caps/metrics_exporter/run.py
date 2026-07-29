# 开发者：自由的风
"""metrics_exporter/run.py — Prometheus指标导出器
=================================================
运维域 core — 导出 cap 总量、域分布、测试通过数、内存、认知次数。
支持 text/plain (Prometheus), JSON, Pushgateway 推送。

"""
import sys, json, os, time, datetime
from pathlib import Path

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPS_DIR = Path(SANDBOX)
STATE_DIR = Path.home() / ".gbt"
STATE_DIR.mkdir(parents=True, exist_ok=True)


def _total_caps():
    """扫描 caps/ 目录统计总量"""
    return sum(1 for d in CAPS_DIR.iterdir() if (d / "capability.json").exists())


def _caps_by_domain():
    """按域统计 cap 数量"""
    domains = {}
    for d in CAPS_DIR.iterdir():
        cf = d / "capability.json"
        if not cf.exists():
            continue
        try:
            cap = json.loads(cf.read_text(encoding="utf-8"))
            domain = cap.get("category", cap.get("domain", "未分类"))
            domains[domain] = domains.get(domain, 0) + 1
        except Exception:
            domains["解析失败"] = domains.get("解析失败", 0) + 1
    return domains


def _memory_bytes():
    """获取当前进程内存 (RSS)"""
    try:
        import psutil
        return psutil.Process().memory_info().rss
    except ImportError:
        try:
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        except ImportError:
            return 0


def _counter(name, default=0):
    """读取持久化计数器"""
    f = STATE_DIR / f"counter_{name}"
    if not f.exists():
        return default
    try:
        return int(f.read_text().strip())
    except Exception:
        return default


def _inc_counter(name):
    """持久化计数器 +1"""
    f = STATE_DIR / f"counter_{name}"
    val = _counter(name) + 1
    f.write_text(str(val))
    return val


def _gather_metrics():
    """收集所有指标 → dict"""
    caps_total = _total_caps()
    by_domain = _caps_by_domain()
    mem = _memory_bytes()
    tests = _counter("tests_passed")
    cognition = _counter("cognition_count")

    return {
        "gbt_caps_total": caps_total,
        "gbt_caps_by_domain": by_domain,
        "gbt_tests_passed": tests,
        "gbt_memory_bytes": mem,
        "gbt_cognition_count": cognition,
        "timestamp": int(time.time()),
    }


def _prometheus_format(data):
    """格式化为 Prometheus text/plain"""
    ts = data["timestamp"]
    lines = [
        f"# HELP gbt_caps_total 已注册能力总数",
        f"# TYPE gbt_caps_total gauge",
        f"gbt_caps_total {data['gbt_caps_total']} {ts}",
        "",
        f"# HELP gbt_caps_by_domain 按域分布的能力数",
        f"# TYPE gbt_caps_by_domain gauge",
    ]
    for domain, count in data["gbt_caps_by_domain"].items():
        safe_label = domain.replace('"', '\\"').replace("\n", " ")
        lines.append(f'gbt_caps_by_domain{{domain="{safe_label}"}} {count} {ts}')
    lines += [
        "",
        f"# HELP gbt_tests_passed 累计测试通过数",
        f"# TYPE gbt_tests_passed counter",
        f"gbt_tests_passed {data['gbt_tests_passed']} {ts}",
        "",
        f"# HELP gbt_memory_bytes 进程内存占用(字节)",
        f"# TYPE gbt_memory_bytes gauge",
        f"gbt_memory_bytes {data['gbt_memory_bytes']} {ts}",
        "",
        f"# HELP gbt_cognition_count 认知执行次数",
        f"# TYPE gbt_cognition_count counter",
        f"gbt_cognition_count {data['gbt_cognition_count']} {ts}",
        "",
    ]
    return "\n".join(lines)


def do_metrics(params):
    """返回 Prometheus text/plain 格式"""
    data = _gather_metrics()
    return {"ok": True, "content_type": "text/plain", "body": _prometheus_format(data)}


def do_json(params):
    """返回 JSON 格式"""
    return {"ok": True, "metrics": _gather_metrics()}




def _count_lines(path):
    try:
        with open(path, errors='replace') as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def _task_completion_rate():
    memf = STATE_DIR / "evolve" / "memory.jsonl"
    if not memf.exists():
        return {"total": 0, "success": 0, "failure": 0, "rate": 0.0, "rate_pct": "0%"}
    total = 0
    success = 0
    failure = 0
    try:
        with open(memf, errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    total += 1
                    t = e.get("type", "")
                    if t == "success":
                        success += 1
                    elif t in ("error", "failure"):
                        failure += 1
                except Exception:
                    pass
    except Exception:
        pass
    rate = round(success / max(1, total), 4)
    return {"total": total, "success": success, "failure": failure, "rate": rate,
            "rate_pct": f"{round(rate * 100, 1)}%"}


def _cap_health():
    total = _total_caps()
    healthy = 0
    degraded = 0
    dead = 0
    for d in CAPS_DIR.iterdir():
        cf = d / "capability.json"
        if not cf.exists():
            continue
        try:
            cap = json.loads(cf.read_text(encoding="utf-8"))
            status = cap.get("status", cap.get("health", "unknown"))
            if status in ("active", "healthy", "ok", "ready"):
                healthy += 1
            elif status in ("degraded", "warning"):
                degraded += 1
            else:
                dead += 1
        except Exception:
            dead += 1
    return {"total": total, "healthy": healthy, "degraded": degraded, "dead": dead,
            "health_pct": f"{round(healthy / max(1, total) * 100, 1)}%"}


def _evolution_count():
    ef = STATE_DIR / "evolve" / "insights.json"
    if ef.exists():
        try:
            data = json.loads(ef.read_text(encoding="utf-8"))
            return data.get("total_evolutions", 0)
        except Exception:
            pass
    return 0


def _memory_size():
    total = 0
    sizes = {}
    for f in STATE_DIR.rglob("*"):
        if f.is_file():
            try:
                sz = f.stat().st_size
                total += sz
                parent = str(f.parent.relative_to(STATE_DIR))
                sizes[parent] = sizes.get(parent, 0) + sz
            except Exception:
                pass
    top = sorted(sizes.items(), key=lambda x: x[1], reverse=True)[:10]
    return {"total_bytes": total, "total_mb": round(total / 1048576, 2),
            "top_dirs": [{"dir": k, "bytes": v} for k, v in top]}


def _daemon_uptime():
    pidf = STATE_DIR / "daemon_launcher" / "pids.json"
    daemons = []
    running = 0
    if pidf.exists():
        try:
            data = json.loads(pidf.read_text())
            import psutil
            for name, pid in data.items():
                try:
                    p = psutil.Process(pid)
                    ct = p.create_time()
                    uptime_s = int(time.time() - ct)
                    daemons.append({"name": name, "pid": pid, "uptime_s": uptime_s,
                                    "status": "running" if p.is_running() else "dead"})
                    if p.is_running():
                        running += 1
                except Exception:
                    daemons.append({"name": name, "pid": pid, "uptime_s": 0, "status": "dead"})
        except Exception:
            try:
                for name, pid in json.loads(pidf.read_text()).items():
                    daemons.append({"name": name, "pid": pid, "uptime_s": 0, "status": "unknown"})
                    running += 1
            except Exception:
                pass
    return {"running": running, "total": len(daemons), "daemons": daemons,
            "running_pct": f"{round(running / max(1, len(daemons)) * 100, 1)}%"}


def do_collect_all(params):
    return {"ok": True, "action": "collect_all",
            "task_completion": _task_completion_rate(),
            "cap_health": _cap_health(),
            "memory_size": _memory_size(),
            "evolution_count": _evolution_count(),
            "daemon_uptime": _daemon_uptime(),
            "timestamp": int(time.time())}


def do_prometheus_format(params):
    data = _gather_metrics()
    body = _prometheus_format(data)
    extra = []
    extra.append(f"# HELP gbt_task_completion_rate 任务完成率")
    extra.append(f"# TYPE gbt_task_completion_rate gauge")
    tcr = _task_completion_rate()
    extra.append(f"gbt_task_completion_rate {tcr['rate']} {data['timestamp']}")
    extra.append("")
    extra.append(f"# HELP gbt_evolution_count 进化次数")
    extra.append(f"# TYPE gbt_evolution_count counter")
    extra.append(f"gbt_evolution_count {_evolution_count()} {data['timestamp']}")
    extra.append("")
    ch = _cap_health()
    extra.append(f"# HELP gbt_cap_health 能力健康状态")
    extra.append(f"# TYPE gbt_cap_health gauge")
    extra.append(f"gbt_cap_health{{status=\"healthy\"}} {ch['healthy']} {data['timestamp']}")
    extra.append(f"gbt_cap_health{{status=\"degraded\"}} {ch['degraded']} {data['timestamp']}")
    extra.append(f"gbt_cap_health{{status=\"dead\"}} {ch['dead']} {data['timestamp']}")
    extra.append("")
    du = _daemon_uptime()
    extra.append(f"# HELP gbt_daemon_running 运行中的守护进程数")
    extra.append(f"# TYPE gbt_daemon_running gauge")
    extra.append(f"gbt_daemon_running {du['running']} {data['timestamp']}")
    extra.append("")
    ms = _memory_size()
    extra.append(f"# HELP gbt_state_size_bytes 状态目录总大小(字节)")
    extra.append(f"# TYPE gbt_state_size_bytes gauge")
    extra.append(f"gbt_state_size_bytes {ms['total_bytes']} {data['timestamp']}")
    extra.append("")
    return {"ok": True, "content_type": "text/plain", "body": body + "\n" + "\n".join(extra)}


def do_trend_report(params):
    days = params.get("days", 7)
    memf = STATE_DIR / "evolve" / "memory.jsonl"
    if not memf.exists():
        return {"ok": False, "error": "无进化记忆数据"}
    now = time.time()
    cutoff = now - days * 86400
    daily = {}
    weekly_buckets = {}
    try:
        with open(memf, errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    ts_str = e.get("ts", "")
                    if not ts_str:
                        continue
                    t = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    epoch = t.timestamp()
                    if epoch < cutoff:
                        continue
                    day_key = t.strftime("%Y-%m-%d")
                    week_key = t.strftime("%Y-W%W")
                    etype = e.get("type", "unknown")
                    if day_key not in daily:
                        daily[day_key] = {"total": 0, "success": 0, "failure": 0, "other": 0}
                    daily[day_key]["total"] += 1
                    if etype == "success":
                        daily[day_key]["success"] += 1
                    elif etype in ("error", "failure"):
                        daily[day_key]["failure"] += 1
                    else:
                        daily[day_key]["other"] += 1
                    if week_key not in weekly_buckets:
                        weekly_buckets[week_key] = {"total": 0, "success": 0, "failure": 0, "other": 0}
                    weekly_buckets[week_key]["total"] += 1
                    if etype == "success":
                        weekly_buckets[week_key]["success"] += 1
                    elif etype in ("error", "failure"):
                        weekly_buckets[week_key]["failure"] += 1
                    else:
                        weekly_buckets[week_key]["other"] += 1
                except Exception:
                    pass
    except Exception:
        pass
    daily_sorted = []
    for d in sorted(daily.keys()):
        v = daily[d]
        rate = round(v["success"] / max(1, v["total"]) * 100, 1)
        daily_sorted.append({"date": d, "total": v["total"], "success": v["success"],
                             "failure": v["failure"], "other": v["other"], "rate_pct": rate})
    weekly_sorted = []
    for w in sorted(weekly_buckets.keys()):
        v = weekly_buckets[w]
        rate = round(v["success"] / max(1, v["total"]) * 100, 1)
        weekly_sorted.append({"week": w, "total": v["total"], "success": v["success"],
                              "failure": v["failure"], "other": v["other"], "rate_pct": rate})
    return {"ok": True, "action": "trend_report", "period_days": days,
            "daily": daily_sorted, "weekly": weekly_sorted,
            "timestamp": int(time.time())}

HANDLERS = {"metrics": do_metrics, "json": do_json,
             "collect_all": do_collect_all, "prometheus_format": do_prometheus_format,
             "trend_report": do_trend_report}



if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "metrics"
    try:
        raw = sys.stdin.read().strip()
        params = json.loads(raw) if raw else {}
    except Exception:
        params = {}
    handler = HANDLERS.get(action)
    if not handler:
        print(json.dumps({"ok": False, "error": f"未知动作: {action}", "available": list(HANDLERS.keys())}, ensure_ascii=False))
    else:
        result = handler(params)
        print(json.dumps(result, ensure_ascii=False, default=str))
