# 开发者：自由的风
"""health_dashboard/run.py — 全系统健康聚合面板
================================================
53个能力模块状态 + 系统资源 + 后端连接 + LLM审计统计
"""
import sys, json, os, time, subprocess, shutil, importlib
from pathlib import Path
from datetime import datetime, timezone

SANDBOX_DIR = Path(__file__).parent.parent.parent
CAPS_DIR = SANDBOX_DIR / "caps"
DATA_DIR = Path.home() / ".gbt" / "sandbox"
HEALTH_CACHE = Path.home() / ".gbt" / "health_cache.json"
CACHE_TTL = 60  # seconds

def _safe_import(mod):
    try: return importlib.import_module(mod), None
    except Exception as e: return None, str(e)

def _check_caps():
    """检查所有能力模块"""
    caps_status = {"total": 0, "ok": 0, "broken": 0, "details": []}
    if not CAPS_DIR.exists():
        return caps_status
    for d in sorted(CAPS_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        caps_status["total"] += 1
        mf = d / "capability.json"
        rp = d / "run.py"
        issues = []
        if not mf.exists():
            issues.append("missing capability.json")
        else:
            try:
                m = json.loads(mf.read_text(encoding="utf-8"))
                if not m.get("name"): issues.append("no name")
                if not m.get("risk_level"): issues.append("no risk_level")
            except Exception as e:
                issues.append(f"bad json: {e}")
        if not rp.exists():
            issues.append("missing run.py")
        status = "ok" if not issues else "broken"
        if status == "ok": caps_status["ok"] += 1
        else: caps_status["broken"] += 1
        caps_status["details"].append({
            "name": d.name,
            "status": status,
            "issues": issues,
        })
    return caps_status

def _check_resources():
    """系统资源"""
    info = {"cpu_percent": None, "memory": None, "disk": None}
    psutil, err = _safe_import("psutil")
    if psutil:
        try:
            info["cpu_percent"] = psutil.cpu_percent(interval=0.3)
            mem = psutil.virtual_memory()
            info["memory"] = {"total_gb": round(mem.total / 2**30, 1),
                            "used_gb": round(mem.used / 2**30, 1),
                            "percent": mem.percent}
            disk = psutil.disk_usage(str(Path.home()))
            info["disk"] = {"total_gb": round(disk.total / 2**30, 1),
                          "used_gb": round(disk.used / 2**30, 1),
                          "percent": disk.percent}
        except Exception:
            pass
    return info

def _check_backends():
    """后端连接状态"""
    backends = {}
    # Kimi API
    kimi_key = (os.environ.get("MOONSHOT_API_KEY") or
                os.environ.get("KIMI_API_KEY") or "")
    backends["kimi_api"] = {"status": "ok" if kimi_key else "missing",
                            "key_prefix": kimi_key[:8] + "..." if kimi_key else ""}
    # LLM Audit stats
    audit_file = DATA_DIR / "logs" / "llm_audit.jsonl"
    if audit_file.exists():
        try:
            lines = audit_file.read_text(encoding="utf-8").strip().split("\n")
            total = len(lines)
            errors = sum(1 for l in lines if '"status":"error"' in l)
            backends["llm_audit"] = {"status": "ok", "total_calls": total, "errors": errors}
        except Exception:
            backends["llm_audit"] = {"status": "error"}
    else:
        backends["llm_audit"] = {"status": "no_data"}
    # Payment
    pay_key = os.environ.get("FUTURAPAY_API_KEY", "")
    backends["payment"] = {"status": "ok" if pay_key else "dev_mode"}
    # GBT编程工具
    import shutil
    gbt_bin = shutil.which("GBT") or shutil.which("GBT.cmd")
    if gbt_bin:
        try:
            result = subprocess.run([gbt_bin, "--version"], capture_output=True, text=True, timeout=5)
            ver = result.stdout.strip().split("\n")[0] if result.stdout else "unknown"
            backends["GBT"] = {"status": "ok", "version": ver, "path": gbt_bin}
        except Exception:
            backends["GBT"] = {"status": "error", "path": gbt_bin}
    else:
        backends["GBT"] = {"status": "missing"}
    return backends

def do_check(params=None):
    """全系统健康检查"""
    t0 = time.time()
    result = {
        "ok": True,
        "ts": datetime.now(timezone.utc).isoformat(),
        "duration_ms": 0,
        "caps": _check_caps(),
        "resources": _check_resources(),
        "backends": _check_backends(),
    }
    result["duration_ms"] = int((time.time() - t0) * 1000)
    # 综合评分
    score = 100
    if result["caps"]["broken"] > 0: score -= result["caps"]["broken"] * 2
    if result["backends"]["kimi_api"]["status"] != "ok": score -= 20
    result["health_score"] = max(0, score)
    result["summary"] = (
        f"{result['caps']['ok']}/{result['caps']['total']} caps OK, "
        f"{result['caps']['broken']} broken | "
        f"Kimi: {result['backends']['kimi_api']['status']} | "
        f"Score: {result['health_score']}/100"
    )
    return result

def do_quick(params=None):
    r = do_check()
    del r["caps"]
    return r

def do_caps(params=None):
    return {"ok": True, "caps": _check_caps()}


def _read_cache():
    """Read health cache if still fresh (< CACHE_TTL seconds old)."""
    try:
        if not HEALTH_CACHE.exists():
            return None
        data = json.loads(HEALTH_CACHE.read_text(encoding="utf-8"))
        age = time.time() - data.get("_cached_at", 0)
        if age < CACHE_TTL:
            return data
    except Exception:
        pass
    return None


def _write_cache(data):
    """Write health data to cache file."""
    try:
        HEALTH_CACHE.parent.mkdir(parents=True, exist_ok=True)
        data["_cached_at"] = time.time()
        HEALTH_CACHE.write_text(json.dumps(data, ensure_ascii=False, default=str))
    except Exception:
        pass


def do_live_check(params=None):
    """Real-time health scan using nexus neighborhoods + syntax validation.

    Returns {overall_health: 0-100, failing_caps: [...], warnings: [...], last_check: iso_time}
    Results cached to ~/.gbt/health_cache.json with 60s TTL.
    """
    force = (params or {}).get("force", False)
    if not force:
        cached = _read_cache()
        if cached is not None:
            return cached

    failing_caps = []
    warnings = []

    # Use nexus to get all defined caps from neighborhoods
    try:
        sys.path.insert(0, str(SANDBOX_DIR))
        from brain.nexus import get_nexus
        nexus = get_nexus()
        scan_result = nexus.scan(force=True)
    except Exception as e:
        return {
            "ok": False,
            "error": f"nexus scan failed: {e}",
            "overall_health": 0,
            "failing_caps": [],
            "warnings": [],
            "last_check": datetime.now(timezone.utc).isoformat()
        }

    # Collect all cap names from nexus neighborhoods
    all_cap_names = set()
    for domain, info in nexus.neighborhoods.items():
        for cap_name in info["caps"]:
            all_cap_names.add(cap_name)

    total = len(all_cap_names)
    ok_count = 0

    for cap_name in sorted(all_cap_names):
        cap_dir = CAPS_DIR / cap_name
        rp = cap_dir / "run.py"
        mf = cap_dir / "capability.json"
        cap_issues = []

        # Check run.py exists
        if not rp.exists():
            cap_issues.append("missing run.py")
        else:
            # Syntax-validate run.py
            try:
                code = rp.read_text(encoding="utf-8")
                compile(code, str(rp), "exec")
            except SyntaxError as se:
                cap_issues.append(f"syntax error: {se}")
            except Exception as ex:
                cap_issues.append(f"unreadable: {ex}")

        # Check capability.json
        if not mf.exists():
            cap_issues.append("missing capability.json")
        else:
            try:
                data = json.loads(mf.read_text(encoding="utf-8"))
                if not data.get("name"):
                    cap_issues.append("capability.json: no name")
                if not data.get("actions"):
                    cap_issues.append("capability.json: no actions")
            except json.JSONDecodeError as je:
                cap_issues.append(f"capability.json: corrupt JSON ({je})")
            except Exception as ex:
                cap_issues.append(f"capability.json: {ex}")

        if cap_issues:
            # Determine severity: missing core files = failure, other = warning
            has_critical = any("missing" in i or "syntax error" in i or "corrupt JSON" in i for i in cap_issues)
            if has_critical:
                failing_caps.append({"cap": cap_name, "issues": cap_issues})
            else:
                warnings.append({"cap": cap_name, "issues": cap_issues})
        else:
            ok_count += 1

    # Also catch caps that exist on disk but are NOT in any nexus neighborhood
    actual_dirs = {d.name for d in CAPS_DIR.iterdir() if d.is_dir() and not d.name.startswith("_")}
    orphan_caps = actual_dirs - all_cap_names - {"_shared"}  # skip special dirs
    for orphan in orphan_caps:
        warnings.append({"cap": orphan, "issues": ["orphan: not registered in any nexus neighborhood"]})

    overall_health = round((ok_count / max(total, 1)) * 100)
    result = {
        "ok": len(failing_caps) == 0,
        "overall_health": overall_health,
        "total_caps": total,
        "ok_caps": ok_count,
        "failing_caps": failing_caps,
        "warnings": warnings,
        "last_check": datetime.now(timezone.utc).isoformat(),
    }

    _write_cache(result)
    return result


def do_list(params=None):
    """列出 dashboard 提供的面板/指标"""
    return {
        "ok": True,
        "action": "list",
        "panels": {
            "caps": "53个能力模块状态检查",
            "resources": "系统资源 (CPU / 内存 / 磁盘)",
            "backends": "后端连接状态 (Kimi API / LLM Audit / Payment / GBT CLI)",
            "health_score": "综合健康评分 (0-100)",
            "live_check": "实时扫描 (nexus + 语法验证) 含 failing_caps / warnings",
        },
        "actions": {
            "check": "全系统健康检查 (含 caps + resources + backends + health_score)",
            "quick": "快速检查 (不含 caps 明细)",
            "caps": "仅能力模块状态",
            "live_check": "实时健康扫描 (nexus neighborhoods + 语法验证, 60s 缓存)",
            "list": "本列表",
            "self_test": "核心组件自检",
            "help": "帮助信息 (同 list)",
        },
    }


def do_self_test(params=None):
    """核心组件自检"""
    results = {}

    # 1. importlib 可用
    try:
        import importlib as _il
        results["importlib"] = "ok"
    except Exception as e:
        results["importlib"] = f"fail: {e}"

    # 2. CAPS_DIR 存在
    results["caps_dir"] = "ok" if CAPS_DIR.exists() else "fail: missing"

    # 3. SANDBOX_DIR 存在
    results["sandbox_dir"] = "ok" if SANDBOX_DIR.exists() else "fail: missing"

    # 4. json 模块
    try:
        json.dumps({})
        results["json_module"] = "ok"
    except Exception as e:
        results["json_module"] = f"fail: {e}"

    # 5. psutil (optional)
    psutil_mod, psutil_err = _safe_import("psutil")
    results["psutil"] = "ok" if psutil_mod else f"unavailable: {psutil_err}"

    # 6. 缓存目录可写
    try:
        HEALTH_CACHE.parent.mkdir(parents=True, exist_ok=True)
        test_file = HEALTH_CACHE.parent / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
        results["health_cache_dir"] = "ok"
    except Exception as e:
        results["health_cache_dir"] = f"fail: {e}"

    all_ok = all(v == "ok" for v in results.values())
    return {
        "ok": all_ok,
        "action": "self_test",
        "components": results,
        "verdict": "PASS" if all_ok else "FAIL",
    }


do_help = do_list  # help 同 list


HANDLERS = {
    "check": do_check,
    "quick": do_quick,
    "caps": do_caps,
    "live_check": do_live_check,
    "list": do_list,
    "self_test": do_self_test,
    "help": do_help,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "check"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    else:
        # stdin mode: read JSON line with "action" and "params" keys
        try:
            raw = sys.stdin.read().strip()
            if raw:
                payload = json.loads(raw)
                if isinstance(payload, dict):
                    action = payload.get("action", action)
                    params = payload.get("params", params)
        except Exception:
            pass
    h = HANDLERS.get(action, do_check)
    result = h(params)
    print(json.dumps(result, ensure_ascii=False, default=str))
