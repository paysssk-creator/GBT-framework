# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
# ⛔ 链路内核集成 — 不可绕过
"""
brain/neural_proprioception.py — 神经本体感知层 v1.0
====================================================
L8层: 系统自我感知 — 像人类本体感觉一样感知自身状态。

覆盖:
  brain/     — 所有脑模块导入健康 + handler 有效性
  tentacles  — 神经触手/吞噬触手/导航触手/视觉触手状态
  nexus      — 邻域注册完整性 + cap数目一致性
  web        — web/ 目录结构完整性
  api        — web_api 端口存活检测
  memory     — memory_store.json + 状态文件完整性
  cross_val  — 交叉验证日志健康度

每条感知输出: {component, status, detail, heartbeat_age}
"""
import json, time, os, sys
from pathlib import Path
from datetime import datetime, timezone
from importlib import util as importlib_util

ROOT = Path(__file__).parent.parent
BRAIN_DIR = ROOT / "brain"
CAPS_DIR = ROOT / "caps"
WEB_DIR = ROOT / "web"
GST_DIR = Path.home() / ".gbt"


def _now():
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════
# 1. 脑模块感知
# ═══════════════════════════════════════════════

def sense_brain_modules() -> dict:
    """感知所有 brain/*.py 模块的导入健康度"""
    modules = []
    errors = []
    for py_file in sorted(BRAIN_DIR.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        mod_name = py_file.stem
        try:
            spec = importlib_util.spec_from_file_location(f"brain.{mod_name}", str(py_file))
            if spec and spec.loader:
                mod = importlib_util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                modules.append({"name": mod_name, "ok": True, "import_ms": 0})
        except Exception as e:
            errors.append({"name": mod_name, "ok": False, "error": str(e)[:120]})
            modules.append({"name": mod_name, "ok": False, "error": str(e)[:120]})

    return {
        "ok": len(errors) == 0,
        "component": "brain_modules",
        "total": len(modules),
        "healthy": len(modules) - len(errors),
        "errors": errors,
        "modules": [m["name"] for m in modules if m["ok"]],
    }


# ═══════════════════════════════════════════════
# 2. 触手状态感知
# ═══════════════════════════════════════════════

def sense_tentacles() -> dict:
    """感知所有触手的活性和状态"""
    tentacles = {}
    state_dir = GST_DIR / "neural_tentacle"

    # 神经触手
    nt_state = state_dir / "tentacle_state.json"
    if nt_state.exists():
        try:
            data = json.loads(nt_state.read_text(encoding="utf-8"))
            age_s = time.time() - _parse_iso(data.get("last_scan_at", ""))
            tentacles["neural"] = {
                "ok": True, "scans": data.get("total_scans", 0),
                "last_scan_age_s": int(age_s), "issues_found": data.get("total_issues_found", 0),
                "issues_fixed": data.get("total_issues_fixed", 0),
            }
        except Exception:
            tentacles["neural"] = {"ok": False, "error": "state file corrupted"}
    else:
        tentacles["neural"] = {"ok": False, "error": "no state file"}

    # 吞噬触手
    dv_state = state_dir / "devour_state.json"
    if dv_state.exists():
        try:
            data = json.loads(dv_state.read_text(encoding="utf-8"))
            age_s = time.time() - _parse_iso(data.get("last_devour_at", ""))
            tentacles["devour"] = {
                "ok": True, "devours": data.get("total_devours", 0),
                "absorbed": data.get("total_absorbed", 0),
                "caps_created": data.get("total_caps_created", 0),
                "last_devour_age_s": int(age_s),
                "learnings": len(data.get("scan_learnings", [])),
            }
        except Exception:
            tentacles["devour"] = {"ok": False, "error": "state file corrupted"}
    else:
        tentacles["devour"] = {"ok": False, "error": "no state file"}

    # 导航触手
    nav_state = GST_DIR / "navigation" / "nav_state.json"
    if nav_state.exists():
        try:
            data = json.loads(nav_state.read_text(encoding="utf-8"))
            tentacles["navigation"] = {"ok": True, "navigations": data.get("total_navigations", 0)}
        except Exception:
            tentacles["navigation"] = {"ok": False, "error": "state corrupted"}
    else:
        tentacles["navigation"] = {"ok": False, "error": "no state"}

    # 视觉触手
    vis_state = GST_DIR / "neural_tentacle" / "vision_state.json"
    if vis_state.exists():
        try:
            data = json.loads(vis_state.read_text(encoding="utf-8"))
            tentacles["vision"] = {"ok": True, "captures": data.get("total_captures", 0)}
        except Exception:
            tentacles["vision"] = {"ok": False, "error": "state corrupted"}
    else:
        tentacles["vision"] = {"ok": True, "captures": 0, "note": "not yet initialized"}

    all_ok = all(t.get("ok", False) for t in tentacles.values())
    return {"ok": all_ok, "component": "tentacles", "tentacles": tentacles}


# ═══════════════════════════════════════════════
# 3. Nexus 一致性感知
# ═══════════════════════════════════════════════

def sense_nexus() -> dict:
    """感知 nexus 注册状态一致性"""
    try:
        from brain.nexus import get_nexus
        nx = get_nexus()
        topo = nx.topology()

        # 检查cap数目 — 排除多脑域(脑模块不在caps/下)
        brain_domain_caps = len(topo.get("breakdown", {}).get("🧠 多脑域", {}).get("core", []))
        cap_count = topo.get("total_caps", 0) - brain_domain_caps
        domain_count = topo.get("domains", 0)

        # 检查磁盘上实际存在的cap目录数 (_2captcha 是唯一 _ 前缀真cap)
        actual_dirs = 0
        for base in [CAPS_DIR, ROOT / "integrations" / "payment"]:
            if base.exists():
                actual_dirs += len([d for d in base.iterdir() if d.is_dir()
                                    and not d.name.startswith(".")
                                    and (not d.name.startswith("_") or d.name == "_2captcha")])

        # 检查内存缓存
        cached = nx._scan_cache if hasattr(nx, "_scan_cache") else None
        cache_ok = cached.get("ok", False) if cached else None

        # 检查上次扫描时间
        last_scan_age = time.time() - (nx._last_scan or 0) if hasattr(nx, "_last_scan") and nx._last_scan else None

        healthy = True
        issues = []
        gap = cap_count - actual_dirs
        if gap != 0:
            healthy = False
            issues.append(f"注册{cap_count}(不含脑域) vs 磁盘{actual_dirs} — 差异{gap}个")
        if last_scan_age and last_scan_age > 3600:
            issues.append(f"上次扫描距今{last_scan_age/3600:.1f}小时")

        return {
            "ok": healthy,
            "component": "nexus",
            "domains": domain_count,
            "caps_registered": cap_count,
            "caps_on_disk": actual_dirs,
            "last_scan_age_s": int(last_scan_age) if last_scan_age else None,
            "cache_healthy": cache_ok,
            "issues": issues,
        }
    except Exception as e:
        return {"ok": False, "component": "nexus", "error": str(e)[:120]}


# ═══════════════════════════════════════════════
# 4. Web目录 + API端口感知
# ═══════════════════════════════════════════════

def sense_web() -> dict:
    """感知 web/ 目录完整性和 API 端口"""
    web_ok = WEB_DIR.exists()
    web_files = 0
    index_exists = False
    if web_ok:
        web_files = len(list(WEB_DIR.rglob("*")))
        index_exists = (WEB_DIR / "index.html").exists()

    # API端口检测
    api_port = 9120
    api_alive = False
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        api_alive = s.connect_ex(("127.0.0.1", api_port)) == 0
        s.close()
    except Exception:
        pass

    return {
        "ok": web_ok and index_exists,
        "component": "web",
        "web_dir_exists": web_ok,
        "index_exists": index_exists,
        "total_files": web_files,
        "api_port": api_port,
        "api_alive": api_alive,
    }


# ═══════════════════════════════════════════════
# 5. 内存/状态文件感知
# ═══════════════════════════════════════════════

def sense_memory() -> dict:
    """感知 memory_store.json 和关键状态文件完整性"""
    mem_file = ROOT / "memory_store.json"
    mem_ok = False
    mem_size = 0
    if mem_file.exists():
        try:
            data = json.loads(mem_file.read_text(encoding="utf-8"))
            mem_ok = True
            mem_size = mem_file.stat().st_size
        except Exception:
            pass

    # 检查 .gbt/ 状态文件
    gbt_files = {}
    for fname in ["last_scan.json", "tp_sessions.json", "config.yml"]:
        fp = GST_DIR / fname
        gbt_files[fname] = fp.exists()

    return {
        "ok": mem_ok,
        "component": "memory",
        "memory_store_ok": mem_ok,
        "memory_store_size": mem_size,
        "gbt_state_files": gbt_files,
    }


# ═══════════════════════════════════════════════
# 6. 交叉验证日志感知
# ═══════════════════════════════════════════════

def sense_cross_validation() -> dict:
    """感知交叉验证系统的活跃度和冲突率"""
    xv_log = GST_DIR / "cross_validation" / "validations.jsonl"
    if not xv_log.exists():
        return {"ok": True, "component": "cross_validation", "total_validations": 0, "note": "not yet initialized"}

    try:
        lines = xv_log.read_text(encoding="utf-8").strip().split("\n")
        total = len(lines)
        conflicts = 0
        recent_rules = []
        for line in lines[-20:]:
            entry = json.loads(line)
            if entry.get("verdict") == "conflict":
                conflicts += 1
            recent_rules.append(entry.get("rule", "?"))
        return {
            "ok": True,
            "component": "cross_validation",
            "total_validations": total,
            "conflicts": conflicts,
            "conflict_rate": round(conflicts / max(total, 1), 2),
            "recent_rules": list(set(recent_rules)),
        }
    except Exception as e:
        return {"ok": False, "component": "cross_validation", "error": str(e)[:120]}


# ═══════════════════════════════════════════════
# 全感知入口
# ═══════════════════════════════════════════════

def full_proprioception() -> dict:
    from brain.chain_kernel import enforce_chain as _enf; _enf("neural_proprioception.init")
    """本体感知全扫描 — 一次感知所有自身子系统"""
    t0 = time.time()
    senses = {}

    scanners = [
        ("L8_brain", sense_brain_modules),
        ("L8_tentacles", sense_tentacles),
        ("L8_nexus", sense_nexus),
        ("L8_web", sense_web),
        ("L8_memory", sense_memory),
        ("L8_crossval", sense_cross_validation),
    ]

    for name, scanner in scanners:
        try:
            senses[name] = scanner()
        except Exception as e:
            senses[name] = {"ok": False, "error": str(e)[:120]}

    all_ok = all(s.get("ok", False) for s in senses.values())
    elapsed = int((time.time() - t0) * 1000)

    return {
        "ok": all_ok,
        "timestamp": _now(),
        "elapsed_ms": elapsed,
        "layer": "L8_本体感知",
        "components_total": len(senses),
        "components_ok": sum(1 for s in senses.values() if s.get("ok", False)),
        "senses": senses,
    }


# ═══════════════════════════════════════════════
# 工具
# ═══════════════════════════════════════════════

def _parse_iso(iso_str: str) -> float:
    """ISO时间字符串 → epoch秒"""
    if not iso_str:
        return 0
    try:
        from datetime import datetime as dt
        return dt.fromisoformat(iso_str).timestamp()
    except Exception:
        return 0


if __name__ == "__main__":
    r = full_proprioception()
    # Windows GBK console fix: reconfigure stdout to UTF-8
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
