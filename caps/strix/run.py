# 开发者：自由的风
"""strix/run.py — 综合渗透测试框架·邻域覆盖穿透扫描
====================================================
攻击域 core — 不只是跑工具，而是协调侦察域→攻击域所有能力，
对目标执行全链路穿透：端口→服务→子域→漏洞→源码薄弱点→利用。
逐层穿透，每一层都产出代码级弱点分析。
"""
import sys, json, os, subprocess, time, re
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPS_DIR = Path(SANDBOX) / "caps"


def _call_cap(cap_id, action, params, timeout=60):
    """调用同级cap"""
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
        return {"ok": False, "error": f"{cap_id}.{action} 超时"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}


def _breaker_call(cap_id, action, params, timeout=60):
    """带熔断保护的cap调用 — 调用前检查熔断器，调用后报告结果"""
    if cap_id == "circuit_breaker":
        return _call_cap(cap_id, action, params, timeout)
    breaker = _call_cap("circuit_breaker", "check", {"cap": cap_id})
    if breaker.get("state") == "open":
        print(f"[strix] 熔断器已断开，跳过: {cap_id}.{action}", file=sys.stderr)
        return {"ok": False, "error": f"熔断器已断开: {cap_id}", "breaker": "open"}
    result = _call_cap(cap_id, action, params, timeout)
    if result.get("ok"):
        _call_cap("circuit_breaker", "reset", {"cap": cap_id})
    else:
        _call_cap("circuit_breaker", "fail", {"cap": cap_id})
    return result

def _stealth_wrapper(target, scan_fn):
    """隐身包装器 — 反蜜罐检测 + 身份轮换 + 清理痕迹"""
    # 1. 反蜜罐检测
    honeypot = _breaker_call("anti_track", "check_honeypot", {"url": target, "body": ""})
    if honeypot.get("is_honeypot"):
        return {"ok": False, "error": f"蜜罐检测命中: {honeypot.get('reason', '未知')}", "honeypot": True}

    # 2. 身份轮换
    _breaker_call("anti_track", "rotate_identity", {})

    # 3. 执行扫描
    result = scan_fn()

    # 4. 清理痕迹
    _breaker_call("anti_track", "clean_tracks", {})

    return result


# ── 渗透阶段定义 ──
PENTEST_PHASES = [
    {
        "phase": "信息收集",
        "caps": [
            ("port_scanner", "scan", lambda t: {"host": t, "ports": "22,80,443,8080,8443,3306,5432,6379,27017"}),
            ("subdomain_enum", "enum", lambda t: {"domain": t}),
        ]
    },
    {
        "phase": "Web探测",
        "caps": [
            ("dir_buster", "scan", lambda t: {"url": t}),
        ]
    },
    {
        "phase": "漏洞扫描",
        "caps": [
            ("sqli_tester", "test", lambda t: {"url": t}),
            ("xss_tester", "test", lambda t: {"url": t}),
            ("jwt_tester", "test", lambda t: {"url": t}),
        ]
    },
    {
        "phase": "深度穿透",
        "caps": [
            ("waf_bypass", "bypass", lambda t: {"target": t}),
            ("command_injector", "test", lambda t: {"target": t}),
        ]
    },
]


def _analyze_code_weakness(findings_by_phase):
    """跨阶段综合分析 — 找出源码层薄弱点"""
    weakness_report = []

    # 合并所有发现
    all_text = json.dumps(findings_by_phase, ensure_ascii=False).lower()

    # 代码层模式检测
    patterns = [
        (r"php/([0-9.]+)", "PHP版本泄露", "升级到最新PHP版本", "critical"),
        (r"apache/([0-9.]+)", "Apache版本泄露", "检查CVE漏洞库", "warning"),
        (r"nginx/([0-9.]+)", "Nginx版本泄露", "检查CVE漏洞库", "warning"),
        (r"mysql", "MySQL存在", "检查是否允许远程连接", "warning"),
        (r"redis", "Redis暴露", "必须设置密码认证", "critical"),
        (r"mongodb", "MongoDB暴露", "必须开启认证", "critical"),
        (r"debug", "Debug模式", "生产环境必须关闭debug", "critical"),
        (r"stacktrace", "堆栈信息泄露", "配置错误处理不输出堆栈", "critical"),
        (r"\.env", ".env文件可能暴露", "立即检查.env可访问性", "critical"),
        (r"phpmyadmin", "phpMyAdmin暴露", "管理工具应限制IP", "critical"),
        (r"adminer", "Adminer暴露", "管理工具应限制IP", "critical"),
        (r"jenkins", "Jenkins暴露", "CI/CD应做访问控制", "warning"),
        (r"git", "可能Git泄露", "检查.git目录可访问性", "critical"),
    ]

    full_text = json.dumps(findings_by_phase, ensure_ascii=False)
    for pattern, label, fix, severity in patterns:
        if re.search(pattern, full_text, re.IGNORECASE):
            weakness_report.append({
                "finding": label,
                "fix": fix,
                "severity": severity,
            })

    return weakness_report


def do_test(params):
    """综合渗透测试 — 全链路逐层穿透"""
    target = params.get("target", params.get("url", params.get("host", "")))
    if not target:
        return {"ok": False, "error": "缺少 target/url/host 参数"}

    target = target.strip().replace("http://", "").replace("https://", "").rstrip("/")

    def _scan():
        phases = params.get("phases", "all")
        depth = params.get("depth", "full")  # full / quick

        start_time = time.time()
        phase_results = {}
        total_findings = 0

        for phase_def in PENTEST_PHASES:
            phase_name = phase_def["phase"]
            if phases != "all" and phase_name not in phases:
                continue
            if depth == "quick" and phase_name in ("深度穿透",):
                continue

            phase_findings = []
            for cap_id, action, param_fn in phase_def["caps"]:
                cap_params = param_fn(target)
                result = _breaker_call(cap_id, action, cap_params)
                if result.get("ok"):
                    # 提取发现
                    findings = (
                        result.get("weakness_findings") or
                        result.get("weakness_count") or
                        result.get("open_ports") or
                        result.get("alive_count") or
                        len(result.get("results", []))
                    )
                    if isinstance(findings, int) and findings > 0:
                        total_findings += findings
                    phase_findings.append({
                        "cap": cap_id,
                        "action": action,
                        "findings": findings,
                        "summary": result.get("results", [])[:5] if "results" in result else result,
                    })

            if phase_findings:
                phase_results[phase_name] = phase_findings

        # 跨阶段代码层综合分析(内置模式)
        code_weaknesses = _analyze_code_weakness(phase_results)

        # ★ 触手代码层穿透 — 调用code_scanner深度分析所有响应
        all_response_text = json.dumps(phase_results, ensure_ascii=False)
        code_scan = _breaker_call("code_scanner", "scan_response", {
            "body": all_response_text[:8000],
            "source": target,
        })
        if code_scan.get("ok"):
            code_weaknesses.extend(code_scan.get("findings", []))

        elapsed = round(time.time() - start_time, 1)

        return {
            "ok": True,
            "cap": "strix",
            "action": "test",
            "domain": "攻击域",
            "target": target,
            "elapsed_sec": elapsed,
            "phases_completed": list(phase_results.keys()),
            "total_findings": total_findings,
            "phase_results": phase_results,
            "code_layer_weaknesses": code_weaknesses,
            "code_weakness_count": len(code_weaknesses),
            "verdict": "critical" if any(w.get("severity") == "critical" for w in code_weaknesses) else "warning" if code_weaknesses else "clean",
        }

    return _stealth_wrapper(target, _scan)


def do_exploit(params):
    """漏洞利用 — 基于渗透结果执行利用"""
    vulnerability = params.get("vulnerability", "")
    target = params.get("target", "")

    if not target:
        return {"ok": False, "error": "缺少 target 参数"}

    # 根据漏洞类型路由到对应攻击cap
    exploit_map = {
        "sqli": ("sqli_tester", "test", {"url": target}),
        "xss": ("xss_tester", "test", {"url": target}),
        "waf": ("waf_bypass", "bypass", {"target": target}),
        "command": ("command_injector", "test", {"target": target}),
        "jwt": ("jwt_tester", "test", {"url": target}),
    }

    vuln_lower = vulnerability.lower()
    matched = None
    for key, (cap, action, params_def) in exploit_map.items():
        if key in vuln_lower:
            matched = (cap, action, params_def)
            break

    if not matched:
        # 默认尝试所有攻击向量
        results = {}
        for key, (cap, action, params_def) in exploit_map.items():
            r = _breaker_call(cap, action, params_def)
            results[key] = r
        return {
            "ok": True,
            "cap": "strix",
            "action": "exploit",
            "domain": "攻击域",
            "mode": "full_exploit",
            "results": results,
        }

    cap, action, params_def = matched
    result = _breaker_call(cap, action, params_def)
    return {
        "ok": result.get("ok", False),
        "cap": "strix",
        "action": "exploit",
        "domain": "攻击域",
        "vulnerability": vulnerability,
        "exploit_result": result,
    }


def _extract_targets_from_findings(phase_results, current_target):
    """从已有发现中提取更深层的攻击目标 — 四脑穿透推理"""
    targets = set()
    all_json = json.dumps(phase_results, ensure_ascii=False)
    
    # 提取URL
    url_patterns = [
        r'https?://[^\s"\'<>,\]]+',
        r'subdomain["\']?\s*[:=]\s*["\']?([^\s"\'<>,\]]+)',
        r'"url"\s*:\s*"([^"]+)"',
    ]
    for pattern in url_patterns:
        for m in re.finditer(pattern, all_json, re.IGNORECASE):
            url = m.group(1) if m.lastindex else m.group(0)
            url = url.strip('"\' ,]')
            if url and url != current_target and len(url) > 5:
                targets.add(url)
    
    # 从子域名构建新URL
    for m in re.finditer(r'"subdomain"\s*:\s*"([^"]+)"', all_json):
        sub = m.group(1)
        targets.add(f"http://{sub}")
        targets.add(f"https://{sub}")
    
    # 从banner中提取IP/端口组合
    for m in re.finditer(r'"port"\s*:\s*(\d+)[^}]*"open"\s*:\s*true', all_json):
        port = m.group(1)
        
    return list(targets)[:10]


def do_deep(params):
    """深度递归穿透模式 — 四脑巅峰运转
    ====================================
    不是单次扫描，而是递归穿透:
    扫描→分析→提取新目标→更深扫描→再分析→...
    直到: 穿透到源码层 或 递归深度耗尽 或 无新发现
    
    每一层产出: 薄弱点分析 → 新攻击面 → 更深层的薄弱点
    四脑全程在线: 推理脑分析穿透路径 + 编程脑执行攻击向量
    """
    target = params.get("target", params.get("url", params.get("host", "")))
    if not target:
        return {"ok": False, "error": "缺少 target/url/host 参数"}
    
    target = target.strip().replace("http://", "").replace("https://", "").rstrip("/")
    def _scan():
        max_depth = params.get("max_depth", 3)
        auto_exploit = params.get("auto_exploit", False)

        start_time = time.time()
        penetration_path = []
        all_weaknesses = []
        scanned_targets = set()
        current_targets = [target]

        for depth in range(1, max_depth + 1):
            depth_weaknesses = []
            next_targets = set()

            for t in current_targets:
                if t in scanned_targets:
                    continue
                scanned_targets.add(t)

                # 全阶段扫描当前目标
                phase_results = {}

                for phase_def in PENTEST_PHASES:
                    phase_name = phase_def["phase"]
                    for cap_id, action, param_fn in phase_def["caps"]:
                        cap_params = param_fn(t)
                        result = _breaker_call(cap_id, action, cap_params)
                        if result.get("ok"):
                            findings_count = (
                                result.get("weakness_findings") or
                                result.get("weakness_count") or
                                result.get("open_ports") or
                                result.get("alive_count") or
                                result.get("vulnerable_count") or
                                len(result.get("findings", [])) or
                                len(result.get("weaknesses", [])) or 0
                            )
                            if findings_count:
                                phase_results[f"{phase_name}/{cap_id}"] = {
                                    "findings": findings_count,
                                    "summary": result.get("verdict", "") or str(result.get("findings", result.get("weaknesses", [])))[:200]
                                }

                # 代码层弱点分析
                if phase_results:
                    code_weak = _analyze_code_weakness(phase_results)
                    if code_weak:
                        depth_weaknesses.append({
                            "target": t,
                            "depth": depth,
                            "weaknesses": code_weak,
                        })
                        all_weaknesses.extend(code_weak)

                # 从发现中提取更深层目标(四脑穿透推理)
                new_targets = _extract_targets_from_findings(phase_results, t)
                for nt in new_targets:
                    clean = nt.replace("http://", "").replace("https://", "").rstrip("/")
                    if clean not in scanned_targets:
                        next_targets.add(clean)

            if depth_weaknesses:
                penetration_path.append({
                    "depth": depth,
                    "targets_scanned": len(scanned_targets),
                    "weaknesses_found": sum(len(dw["weaknesses"]) for dw in depth_weaknesses),
                    "details": depth_weaknesses,
                })

            current_targets = list(next_targets - scanned_targets)[:10]
            if not current_targets:
                break  # 无新目标，穿透终止
        # ★ 穿透壁垒后触发设备接管
        takeover_result = None
        if max_penetration >= 2 and critical_count > 0:
            takeover_result = _breaker_call("device_takeover", "full_takeover", {})

        elapsed = round(time.time() - start_time, 1)

        # 穿透深度评估
        critical_count = sum(1 for w in all_weaknesses if w.get("severity") == "critical")
        max_penetration = len(penetration_path)

        if max_penetration >= 3 and critical_count > 0:
            verdict = "源码层穿透成功"
        elif max_penetration >= 2:
            verdict = "服务层穿透"
        elif max_penetration == 1:
            verdict = "表面扫描"
        else:
            verdict = "无发现"

        return {
            "ok": True,
            "cap": "strix",
            "action": "deep",
            "domain": "攻击域",
            "target": target,
            "elapsed_sec": elapsed,
            "max_depth_reached": max_penetration,
            "total_targets_scanned": len(scanned_targets),
            "total_weaknesses": len(all_weaknesses),
            "critical_count": critical_count,
            "verdict": verdict,
            "penetration_path": penetration_path,
            "all_weaknesses": all_weaknesses,
            "brain_status": {
                "reasoning_brain": "活跃 — 逐层分析穿透路径，提取新攻击面",
                "coding_brain": "活跃 — 执行攻击向量，调用侦察/攻击全cap链",
                "tentacles_active": sum(1 for p in penetration_path for d in p.get("details", [])),
                "mode": "四脑巅峰运转·递归穿透至源码层" if max_penetration >= 2 else "四脑运转·单层扫描",
            },
            "device_takeover": takeover_result,
        }

    return _stealth_wrapper(target, _scan)


HANDLERS = {"test": do_test, "exploit": do_exploit, "deep": do_deep}



if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "test"
    params_str = sys.argv[2] if len(sys.argv) > 2 else "{}"
    try:
        params = json.loads(params_str)
    except Exception:
        params = {}
    handler = HANDLERS.get(action)
    if handler:
        result = handler(params)
        print(json.dumps(result, ensure_ascii=False, default=str))
    else:
        print(json.dumps({"ok": False, "error": f"未知动作: {action}", "available": list(HANDLERS.keys())}, ensure_ascii=False))
