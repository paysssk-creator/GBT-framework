# 开发者：自由的风
"""bounty_hunter/run.py — 漏洞赏金全链路自动化
=============================================
攻击域 core — 全自动漏洞赏金狩猎: 信息收集→漏洞扫描→报告生成
"""
import sys, json, os, subprocess, time
from pathlib import Path

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPS_DIR = Path(SANDBOX) / "caps"


def _call_cap(cap_id, action, params, timeout=90):
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


def do_hunt(params):
    """全链路赏金狩猎"""
    target = params.get("target", params.get("domain", ""))
    if not target:
        return {"ok": False, "error": "缺少 target/domain 参数"}

    target = target.strip().lower().replace("http://", "").replace("https://", "").rstrip("/")

    results = {}
    start = time.time()

    # Phase 1: 侦察
    recon = _call_cap("port_scanner", "scan", {"host": target, "ports": "22,80,443,8080,8443,3306,5432"})
    subs = _call_cap("subdomain_enum", "enum", {"domain": target})
    results["recon"] = {
        "open_ports": recon.get("open_ports", 0) if recon.get("ok") else 0,
        "subdomains": subs.get("total_found", 0) if subs.get("ok") else 0,
    }

    # Phase 2: 构建目标URL列表
    urls = [f"http://{target}", f"https://{target}"]
    if subs.get("ok"):
        for sub in subs.get("alive_details", [])[:10]:
            subdomain = sub.get("subdomain", "")
            if subdomain:
                urls.append(f"http://{subdomain}")
                urls.append(f"https://{subdomain}")

    # Phase 3: 漏洞扫描
    vuln_findings = []
    for url in urls[:5]:
        sqli = _call_cap("sqli_tester", "test", {"url": url})
        if sqli.get("vulnerable_count", 0) > 0:
            vuln_findings.append({"url": url, "vuln": "SQLi", "count": sqli.get("vulnerable_count")})

        xss = _call_cap("xss_tester", "test", {"url": url})
        if xss.get("vulnerable_count", 0) > 0:
            vuln_findings.append({"url": url, "vuln": "XSS", "count": xss.get("vulnerable_count")})

    results["vulnerabilities"] = vuln_findings
    results["total_vulns"] = len(vuln_findings)

    # Phase 4: WAF检测
    waf = _call_cap("waf_bypass", "bypass", {"target": target})
    results["waf"] = waf.get("waf_detected", "Unknown") if waf.get("ok") else "N/A"

    elapsed = round(time.time() - start, 1)

    return {
        "ok": True,
        "cap": "bounty_hunter",
        "action": "hunt",
        "domain": "攻击域",
        "target": target,
        "elapsed_sec": elapsed,
        "findings": results,
        "bounty_potential": "high" if vuln_findings else "low",
    }


def do_report(params):
    """生成漏洞报告"""
    target = params.get("target", "")
    findings = params.get("findings", {})

    report = f"""# GBT 漏洞赏金报告
## 目标: {target}
## 扫描时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

### 侦察结果
- 开放端口: {findings.get('recon', {}).get('open_ports', 'N/A')}
- 发现子域名: {findings.get('recon', {}).get('subdomains', 'N/A')}

### 漏洞发现
"""
    for v in findings.get("vulnerabilities", []):
        report += f"- {v.get('url')}: {v.get('vuln')} ({v.get('count')}处)\n"

    report += f"\n### WAF: {findings.get('waf', 'N/A')}\n"
    report += f"\n### 赏金潜力: {findings.get('bounty_potential', 'N/A')}\n"

    return {"ok": True, "cap": "bounty_hunter", "action": "report", "report": report}


HANDLERS = {"hunt": do_hunt, "report": do_report}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "hunt"
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
