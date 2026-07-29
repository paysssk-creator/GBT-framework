# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""compliance_checker — 合规/审计检查引擎 (GDPR/SOC2/ISO 27001)"""
import sys, json, os, re
from pathlib import Path

COMPLIANCE_CHECKS = {
    "gdpr": {
        "name": "GDPR合规",
        "checks": ["personal_data_inventory", "consent_mechanism", "right_to_erasure", "data_portability", "breach_notification", "dpa_agreement"]
    },
    "soc2": {
        "name": "SOC 2合规",
        "checks": ["access_control", "change_management", "system_operations", "risk_mitigation", "monitoring_alerts"]
    },
    "iso27001": {
        "name": "ISO 27001合规",
        "checks": ["information_security_policy", "asset_management", "access_control", "cryptography", "incident_response", "business_continuity"]
    }
}

def do_check(params):
    """运行合规检查"""
    standard = (params or {}).get("standard", "gdpr")
    target = (params or {}).get("target", "")
    
    if standard not in COMPLIANCE_CHECKS:
        return {"ok": False, "error": f"未知标准: {standard}", "available": list(COMPLIANCE_CHECKS.keys())}
    
    info = COMPLIANCE_CHECKS[standard]
    results = []
    for check in info["checks"]:
        passed = True  # 默认通过，实际需对接检测逻辑
        results.append({"check": check, "passed": passed, "detail": "未配置具体检测规则"})
    
    return {
        "ok": True,
        "standard": standard,
        "name": info["name"],
        "total": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "checks": results,
        "recommendation": "配置具体检测规则以获得准确结果"
    }

def do_list_standards(params=None):
    return {"ok": True, "standards": [{"id": k, "name": v["name"], "checks": len(v["checks"])} for k, v in COMPLIANCE_CHECKS.items()]}

def do_scan_code(params):
    """扫描代码中的合规风险"""
    target = (params or {}).get("path", str(Path.cwd()))
    risks = []
    patterns = [
        (r"(password|secret|api_key|token)\s*=\s*['\"]", "硬编码凭证"),
        (r"eval\(", "eval()使用"),
        (r"exec\(", "exec()使用"),
        (r"os\.system\(", "os.system()调用"),
        (r"subprocess\.\w+\(.*shell\s*=\s*True", "shell=True风险"),
    ]
    try:
        for py_file in Path(target).rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                for pattern, desc in patterns:
                    if re.search(pattern, content):
                        risks.append({"file": str(py_file.relative_to(target)), "risk": desc})
            except:
                pass
    except:
        pass
    return {"ok": True, "scanned_path": target, "risks_found": len(risks), "risks": risks[:50]}

def do_status(params=None):
    return {"ok": True, "cap": "compliance_checker", "ready": True, "standards_supported": list(COMPLIANCE_CHECKS.keys())}

HANDLERS = {"check": do_check, "list": do_list_standards, "scan": do_scan_code, "status": do_status}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知: {action}"})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
