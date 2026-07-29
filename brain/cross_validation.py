# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
# ⛔ 链路内核集成 — 不可绕过
"""
brain/cross_validation.py — 触手交叉互查 · 不盲目做事 v1.0
==========================================================
铁律: 一个触手说了不算，至少两个触手互相印证才准行动。

四条互查规则:
  ① Gap→Reality    吞噬器说缺 → 神经触手验磁盘 + nexus验注册
  ② Error→Pattern  神经触手报错 → 吞噬器验已知模式 + 导航验引用链
  ③ Creation→Safety 吞噬器要创建 → nexus验重复 + 神经验磁盘
  ④ Injection→Consistency 注入前 → 验nexus现状 vs 扫描结果差异

每条规则输出: {verdict, evidence, conflicts, action}
- confirmed: 两个以上触手一致 → 可信
- conflict:   触手结果矛盾 → 标记冲突，不做盲目操作
- unverified: 只有一个触手数据 → 标记待验证
"""
import json
import time
from datetime import datetime
from pathlib import Path
ROOT = Path(__file__).parent.parent
CAPS_DIR = ROOT / "caps"

XVAL_DIR = Path.home() / ".gbt" / "cross_validation"
XVAL_DIR.mkdir(parents=True, exist_ok=True)
XVAL_LOG = XVAL_DIR / "validations.jsonl"


def _log(rule: str, result: dict):
    """记录交叉验证结果到日志"""
    entry = {"ts": datetime.now().isoformat(), "rule": rule, **result}
    try:
        with open(XVAL_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ═══════════════════════════════════════════════
# 规则① Gap → Reality
# 吞噬器说"缺cap X" → 神经触手验磁盘 + nexus验注册
# ═══════════════════════════════════════════════

def validate_gap(gap_name: str, gap_source: str = "devourer") -> dict:
    """吞噬器发现缺口 → 交叉验证是否真的不存在"""
    from brain.chain_kernel import enforce_chain
    enforce_chain("cross_validation.validate_gap")
    from brain.immutable_chain import get_state, persist_state
    from datetime import datetime
    s = get_state()
    s["last_cross_validation_gap"] = datetime.now().isoformat()
    persist_state(s)
    evidence = []
    conflicts = []
    verdict = "unverified"

    # 证据1: 神经触手 — 磁盘上存在吗?
    disk_exists = False
    disk_path = None
    for base in [CAPS_DIR, ROOT / "integrations" / "payment"]:
        p = base / gap_name
        if p.is_dir():
            disk_exists = True
            disk_path = str(p)
            break
    evidence.append({"source": "neural_L0_disk", "exists": disk_exists, "path": disk_path})

    # 证据2: nexus — 注册了吗?
    nexus_registered = False
    nexus_info = None
    try:
        from brain.nexus import get_nexus
        nx = get_nexus()
        topo = nx.topology()
        for domain, info in topo.get("breakdown", {}).items():
            all_caps = info.get("core", []) + info.get("ready", [])
            if gap_name in all_caps:
                nexus_registered = True
                nexus_info = domain
                break
    except Exception:
        pass
    evidence.append({"source": "nexus_registry", "registered": nexus_registered, "domain": nexus_info})

    # 证据3: 导入可用吗? (用 importlib 试一下)
    import_ok = False
    import_error = None
    try:
        import importlib
        # Python模块名不能以数字开头，所以 _2captcha → 需要变换
        mod_name = gap_name
        if mod_name[0].isdigit():
            mod_name = "_" + mod_name  # _2captcha
        importlib.import_module(f"caps.{mod_name}")
        import_ok = True
    except ImportError as e:
        import_error = str(e)[:120]
    except Exception as e:
        import_error = str(e)[:120]
    evidence.append({"source": "import_check", "importable": import_ok, "error": import_error})

    # 裁决
    if disk_exists and nexus_registered:
        verdict = "conflict"
        conflicts.append(f"吞噬器认为缺 {gap_name}，但磁盘({disk_path})和nexus({nexus_info})都存在")
    elif disk_exists:
        verdict = "conflict"
        conflicts.append(f"吞噬器认为缺 {gap_name}，但磁盘已存在: {disk_path}（nexus未注册）")
    elif nexus_registered:
        verdict = "conflict"
        conflicts.append(f"吞噬器认为缺 {gap_name}，但nexus已注册在{nexus_info}（磁盘缺失）")
    elif import_ok:
        verdict = "conflict"
        conflicts.append(f"吞噬器认为缺 {gap_name}，但实际可以导入")
    else:
        verdict = "confirmed"
        # 检查是否是命名问题
        if gap_name[0].isdigit():
            evidence.append({"note": f"cap名以数字开头({gap_name})，Python导入需前缀下划线"})

    result = {"verdict": verdict, "evidence": evidence, "conflicts": conflicts,
              "action": "skip_create" if verdict == "conflict" else "allow_create"}
    _log("gap_reality", result)
    return result


# ═══════════════════════════════════════════════
# 规则② Error → Pattern
# 神经触手报错 → 吞噬器验已知模式 + 导航验引用链
# ═══════════════════════════════════════════════

def validate_error(error_msg: str, cap_name: str = "", error_path: str = "") -> dict:
    """神经触手报错 → 交叉验证是否误报/已知模式"""
    evidence = []
    conflicts = []
    verdict = "unverified"

    # 证据1: 吞噬器 — 以前见过这个错误吗?（用于判断是顽固问题还是新问题）
    seen_before = False
    seen_count = 0
    try:
        from brain.devour_tentacle import get_devourer
        d = get_devourer()
        learnings = d.state.get("scan_learnings", [])
        for learning in learnings:
            if cap_name and cap_name in learning:
                seen_count += 1
            elif error_msg and error_msg[:30] in learning:
                seen_count += 1
        seen_before = seen_count > 0
    except Exception:
        pass
    evidence.append({"source": "devourer_memory", "seen_before": seen_before, "occurrences": seen_count})

    # 证据2: 引用链 — 如果是"引用了不存在的cap"，检查是否命名问题
    if "引用了不存在的" in error_msg or "import" in error_msg.lower():
        import re
        match = re.search(r"caps\.(\w+)", error_msg)
        if match:
            ref_name = match.group(1)
            actual_exists = False
            actual_path = None
            for base in [CAPS_DIR, ROOT / "integrations" / "payment"]:
                for variant in [ref_name, ref_name.lstrip("_"), f"_{ref_name}"]:
                    p = base / variant
                    if p.is_dir():
                        actual_exists = True
                        actual_path = str(p)
                        break
            if actual_exists:
                evidence.append({"source": "name_variant_check",
                               "referenced_as": f"caps.{ref_name}",
                               "actual_path": actual_path,
                               "note": "cap存在于磁盘但引用名不匹配"})
                conflicts.append(f"引用 caps.{ref_name} 报不存在，但 {actual_path} 存在 — 命名问题，非真实错误")

    # 证据3: 导航触手 — 依赖链中有这个cap吗?
    nav_info = None
    try:
        from brain.navigation_tentacle import get_nav
        n = get_nav()
        deps = n.state.get("deps", {})
        if cap_name in deps:
            nav_info = deps[cap_name]
    except Exception:
        pass
    evidence.append({"source": "navigation_deps", "has_dep_info": nav_info is not None})

    # 裁决 — 核心原则: 顽固复发 → 升级；命名冲突 → 降级为假阳性
    if conflicts:
        # 磁盘/nexus证明cap存在 → 这是引用命名问题，非真实错误
        verdict = "conflict"
    elif seen_before and seen_count >= 3:
        # 反复出现3次以上 → 顽固问题，升级
        verdict = "confirmed"
        evidence.append({"note": f"顽固问题: 已出现{seen_count}次，建议优先修复"})
    elif seen_before:
        verdict = "confirmed"
        evidence.append({"note": f"复发问题: 出现过{seen_count}次"})
    else:
        verdict = "confirmed"  # 新问题，无矛盾证据

    # 行动建议
    if conflicts:
        action = "downgrade"       # 命名冲突 → 非真实错误
    elif seen_before and seen_count >= 3:
        action = "escalate"        # 顽固问题 → 升级
    else:
        action = "report"          # 正常上报

    result = {"verdict": verdict, "evidence": evidence, "conflicts": conflicts,
              "cap": cap_name, "error": error_msg[:150],
              "action": action, "recurrence": seen_count}
    return result


# ═══════════════════════════════════════════════
# 规则③ Creation → Safety
# 吞噬器要创建cap → nexus验重复 + 神经验磁盘 + 模糊匹配
# ═══════════════════════════════════════════════

def validate_creation(cap_name: str, cap_desc: str = "") -> dict:
    """创建cap前 → 三重验证不会重复造轮子"""
    evidence = []
    conflicts = []
    verdict = "unverified"

    # 证据1: nexus — 同名cap已注册?
    nexus_duplicate = False
    try:
        from brain.nexus import get_nexus
        nx = get_nexus()
        topo = nx.topology()
        for domain, info in topo.get("breakdown", {}).items():
            if cap_name in info.get("core", []) or cap_name in info.get("ready", []):
                nexus_duplicate = True
                evidence.append({"source": "nexus", "duplicate": True, "domain": domain})
                break
        else:
            evidence.append({"source": "nexus", "duplicate": False})
    except Exception:
        evidence.append({"source": "nexus", "duplicate": False, "error": "nexus查询失败"})

    # 证据2: 磁盘 — 目录已存在?
    disk_exists = False
    disk_path = None
    for base in [CAPS_DIR, ROOT / "integrations" / "payment"]:
        p = base / cap_name
        if p.is_dir():
            disk_exists = True
            disk_path = str(p)
            break
    evidence.append({"source": "disk", "exists": disk_exists, "path": disk_path})

    # 证据3: 模糊匹配 — 有没有类似cap?
    similar = []
    try:
        from brain.nexus import get_nexus
        nx = get_nexus()
        topo = nx.topology()
        all_caps = []
        for _domain, info in topo.get("breakdown", {}).items():
            all_caps.extend(info.get("core", []))
            all_caps.extend(info.get("ready", []))
        # 简单相似度: 包含关系 或 编辑距离
        for existing in set(all_caps):
            if existing == cap_name:
                continue
            if cap_name in existing or existing in cap_name:
                similar.append({"name": existing, "reason": "containment"})
            elif _levenshtein_ratio(cap_name, existing) > 0.7:
                similar.append({"name": existing, "reason": "similar"})
    except Exception:
        pass
    evidence.append({"source": "fuzzy_match", "similar": similar[:5]})

    # 裁决
    if nexus_duplicate or disk_exists:
        verdict = "conflict"
        conflicts.append(f"cap {cap_name} 已存在，不能重复创建")
    elif similar:
        verdict = "conflict"
        conflicts.append(f"cap {cap_name} 与已有cap过于相似: {[s['name'] for s in similar[:3]]}")
    else:
        verdict = "confirmed"

    result = {"verdict": verdict, "evidence": evidence, "conflicts": conflicts,
              "cap": cap_name, "action": "abort" if verdict == "conflict" else "proceed"}
    _log("creation_safety", result)
    return result


# ═══════════════════════════════════════════════
# 规则④ Injection → Consistency
# 注入nexus前 → 验现状 vs 扫描结果差异
# ═══════════════════════════════════════════════

def validate_injection(scan_result: dict) -> dict:
    """注入nexus前 → 交叉验证扫描结果与nexus现状一致性"""
    evidence = []
    conflicts = []
    verdict = "unverified"

    # 证据1: nexus当前健康状态
    nexus_health = None
    try:
        from brain.nexus import get_nexus
        nx = get_nexus()
        prev = nx._scan_cache if hasattr(nx, "_scan_cache") else None
        nexus_health = prev
    except Exception:
        pass
    evidence.append({"source": "nexus_prev_state", "exists": nexus_health is not None})

    # 证据2: 扫描结果 vs nexus差异
    if nexus_health:
        scan_ok = scan_result.get("ok", False)
        nexus_ok = nexus_health.get("ok", False)
        if scan_ok != nexus_ok:
            conflicts.append(f"扫描结果({scan_ok})与nexus现状({nexus_ok})不一致")
        scan_errs = scan_result.get("total_errors", 0)
        nexus_errs = nexus_health.get("total_errors", 0)
        if scan_errs != nexus_errs:
            conflicts.append(f"扫描错误数({scan_errs})与nexus记录({nexus_errs})不一致")


    # 裁决
    if conflicts:
        verdict = "conflict"
    elif nexus_health:
        verdict = "confirmed"
    else:
        verdict = "unverified"  # 首次扫描，无可比数据

    result = {"verdict": verdict, "evidence": evidence, "conflicts": conflicts,
              "action": "warn" if verdict == "conflict" else "inject"}
    _log("injection_consistency", result)
    return result


# ═══════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════

def _levenshtein_ratio(a: str, b: str) -> float:
    """简化的编辑距离相似度"""
    if not a or not b:
        return 0.0
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return 0.0
    # 动态规划
    dp = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(la + 1):
        dp[i][0] = i
    for j in range(lb + 1):
        dp[0][j] = j
    for i in range(1, la + 1):
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    return 1.0 - dp[la][lb] / max(la, lb)


# ═══════════════════════════════════════════════
# 批量互查 — pulse 入口
# ═══════════════════════════════════════════════

def cross_check_pulse(scan_result: dict, devour_result: dict = None) -> dict:
    """脉冲级交叉互查: 一个入口，执行全部适用规则"""
    from brain.chain_kernel import enforce_chain
    enforce_chain("cross_validation.cross_check_pulse")
    from brain.immutable_chain import get_state, persist_state
    from datetime import datetime
    s = get_state()
    s["last_cross_validation_pulse"] = datetime.now().isoformat()
    persist_state(s)
    t0 = time.time()
    checks = {}

    # 规则④: 注入一致性（扫描结果 vs nexus现状）
    checks["injection"] = validate_injection(scan_result)

    # 规则⑤: 本体自检 — 感知系统是否在感知自己
    proprioception = (scan_result.get("layers", {}).get("L8_本体感知", {})
                      .get("proprioception", {}))
    checks["self_health"] = {
        "ok": proprioception.get("ok", False),
        "components_total": proprioception.get("components_total", 0),
        "components_ok": proprioception.get("components_ok", 0),
        "breakdown": {
            name: sense.get("ok", False)
            for name, sense in proprioception.get("senses", {}).items()
        },
    }

    # 规则②: 扫描错误 → 已知模式（每条error交叉验证）
    error_checks = []
    for _lname, ldata in scan_result.get("layers", {}).items():
        for issue in ldata.get("detail", []):
            if issue.get("level") in ("error", "warn"):
                try:
                    r = validate_error(
                        error_msg=issue.get("msg", ""),
                        cap_name=issue.get("cap", ""),
                        error_path=issue.get("path", ""),
                    )
                    error_checks.append(r)
                except Exception:
                    pass
    checks["errors"] = {
        "total": len(error_checks),
        "confirmed": sum(1 for c in error_checks if c.get("verdict") == "confirmed"),
        "conflict": sum(1 for c in error_checks if c.get("verdict") == "conflict"),
        "escalated": sum(1 for c in error_checks if c.get("action") == "escalate"),
        "downgraded": sum(1 for c in error_checks if c.get("action") == "downgrade"),
        "details": error_checks[:10],
    }

    # 规则①+③: 吞噬器缺口 → 现实验证
    gap_checks = []
    if devour_result:
        gaps = devour_result.get("gaps_found", 0)
        if gaps:
            # 从devour_result中取具体gap名
            new_caps = devour_result.get("new_caps", [])
            for cap_name in new_caps:
                if isinstance(cap_name, str):
                    gap_checks.append(validate_gap(cap_name, "devourer"))
                    gap_checks.append(validate_creation(cap_name))
    checks["gaps"] = {
        "total": len(gap_checks),
        "conflict": sum(1 for c in gap_checks if c.get("verdict") == "conflict"),
        "allowed": sum(1 for c in gap_checks if c.get("action") == "allow_create"),
        "aborted": sum(1 for c in gap_checks if c.get("action") in ("abort", "skip_create")),
        "details": gap_checks[:10],
    }

    elapsed = int((time.time() - t0) * 1000)
    return {
        "ok": True,
        "elapsed_ms": elapsed,
        "rules_checked": 5,
        "total_conflicts": (checks["errors"]["conflict"] + checks["gaps"]["conflict"] +
                           (1 if checks["injection"]["verdict"] == "conflict" else 0) +
                           (0 if checks.get("self_health", {}).get("ok", True) else 1)),
        "checks": checks,
    }
