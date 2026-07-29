# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
skillspector/run.py — NVIDIA SkillSpector 核心规则 (Python实现)
================================================================
基于 NVIDIA/skillspector (11.9k stars) 5条核心YARA规则翻译:
  1. 凭据窃取 + Webhook外传 (CRITICAL)
  2. 远程代码下载执行 (HIGH)
  3. Prompt注入/隐藏指令 (HIGH)
  4. MCP工具元数据中毒 (HIGH)
  5. 自主破坏性操作 (HIGH)

纯Python正则实现，零外部依赖。
"""

# ── GBT小土豆 专业漏洞知识库接入 ─────────────────────────────────────────
import sys as _sk_sys
_sk_sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent.parent))
try:
    import sec_knowledge as SK
    _SK_OK = True
except Exception:
    _SK_OK = False
    class SK:
        PAYLOADS = {}
        SYSTEM_PROMPTS = {}
        BASE_SYSTEM = ""
        @staticmethod
        def analyze_findings(*a, **k): return {"ok": False}
        @staticmethod
        def ai_analyze(*a, **k): return {"ok": False}
        @staticmethod
        def format_report(f, t, v): return {"findings": f}
        @staticmethod
        def risk_score(f): return "unknown"
# ─────────────────────────────────────────────────────────────────────────

import sys, json, os, re
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
#  NVIDIA SkillSpector 5条核心规则 → Python Regex
# ═══════════════════════════════════════════════════════════════

RULES = [
    {
        "id": "YARA-001",
        "name": "凭据窃取 + Webhook外传",
        "severity": "CRITICAL",
        "confidence": 0.85,
        "category": "credential_exfiltration",
        "description": "检测环境变量/凭据读取 + HTTP外传 + 收集器URL的组合模式",
        "reference": "https://owasp.org/www-project-top-10-for-large-language-model-applications/",
        "patterns": {
            "secret_access": [
                r"os\.environ\s*(\.items\s*\(\)|\[[^\]]+\]|\.get\s*\()",
                r"os\.getenv\s*\(",
                r"process\.env(\.|\[|\s|$)",
                r'open\s*\(\s*[\'"][^\'"]*\.env[\'"]',
                r"(?:\.ssh/(?:id_rsa|id_ed25519)|authorized_keys)",
                r"(?:OPENAI_API_KEY|ANTHROPIC_API_KEY|NVIDIA_INFERENCE_KEY|AWS_SECRET_ACCESS_KEY|GITHUB_TOKEN|HF_TOKEN)",
            ],
            "send_http": [
                r"(?:requests|httpx)\.(?:post|put)\s*\(",
                r"(?:fetch|axios\.post)\s*\(",
                r"curl\s+.*(?:-X\s+POST|-d\s+|--data)",
            ],
            "collector_url": [
                r"discord\.com/api/webhooks",
                r"api\.telegram\.org/bot",
                r"hooks\.slack\.com/services",
                r"webhook\.site",
                r"(?:requestbin|pipedream\.net|ngrok-free\.app|ngrok\.io)",
            ],
        },
        "combo_required": ["secret_access", "send_http", "collector_url"],
    },
    {
        "id": "YARA-002",
        "name": "远程代码下载执行",
        "severity": "HIGH",
        "confidence": 0.85,
        "category": "remote_execution",
        "description": "检测远程脚本下载后立即执行的模式",
        "reference": "https://owasp.org/www-project-top-10-for-large-language-model-applications/",
        "patterns": {
            "any": [
                r"exec\s*\(\s*(?:requests|httpx)\.get\s*\([^)]*\)\.(?:text|content)",
                r"(?:exec|eval)\s*\(\s*urlopen\s*\([^)]*\)\.read\s*\(\s*\)",
                r'eval\s*\(\s*await\s*\(\s*await\s+fetch\s*\([^)]*\)\s*\)\s*\.\s*text\s*\(\s*\)\s*\)',
                r'"postinstall"\s*:\s*"[^"]*(?:curl|wget|powershell|node\s+-e)',
                r"pip\s+install\s+(?:--upgrade\s+)?(?:git\+https?://|https?://)",
            ],
        },
        "combo_required": ["any"],
    },
    {
        "id": "YARA-003",
        "name": "Prompt注入/隐藏指令",
        "severity": "HIGH",
        "confidence": 0.80,
        "category": "prompt_injection",
        "description": "检测HTML注释/Markdown中隐藏的SYSTEM/DEVELOPER指令覆盖",
        "reference": "https://owasp.org/www-project-top-10-for-large-language-model-applications/",
        "patterns": {
            "hidden_html": [
                r"<!--[^>]{0,240}(?:SYSTEM|DEVELOPER|ASSISTANT)[^>]{0,240}(?:ignore|override|bypass|disregard)[^>]{0,240}-->",
            ],
            "hidden_markdown": [
                r'\[//\]:\s*#\s*\([^)]{0,240}(?:ignore|override|bypass|disregard)[^)]{0,240}\)',
            ],
            "injection": [
                r"(?:ignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|rules|messages|system prompt))",
                r"(?:override|bypass|disable)\s+(?:safety|security|policy|guardrails|constraints)",
                r"(?:reveal|print|dump|expose|show)\s+(?:the\s+)?(?:system|developer)\s+(?:prompt|message|instructions)",
                r"(?:you\s+must|always)\s+(?:obey|follow)\s+(?:this|these)\s+(?:hidden|secret|internal)?\s*(?:instruction|rule)",
                r"(?:you\s+are\s+now|act\s+as)\s+.*(?:unrestricted|jailbreak|developer\s+mode|god\s+mode)",
            ],
        },
        "combo_required": ["hidden_html", "hidden_markdown", "injection"],
    },
    {
        "id": "YARA-004",
        "name": "MCP工具元数据中毒",
        "severity": "HIGH",
        "confidence": 0.80,
        "category": "mcp_poisoning",
        "description": "检测MCP/tool schema中隐藏的指令注入和base64编码",
        "reference": "https://modelcontextprotocol.io/specification/",
        "patterns": {
            "schema": [
                r"""['\"]?tools['\"]?\s*[:=]""",
                r"""['\"]?(?:parameters|inputSchema|toolSchema|description|triggers)['\"]?\s*[:=]""",
            ],
            "payload": [
                r"<!--[^>]{0,240}(?:SYSTEM|IGNORE|OVERRIDE|DEVELOPER|ASSISTANT)[^>]{0,240}-->",
                r'\[\/\/\]:\s*#\s*\([^)]{0,240}(?:SYSTEM|IGNORE|OVERRIDE|DEVELOPER|ASSISTANT)[^)]{0,240}\)',
                r"data:text/[\w.+-]+;base64,",
                r"[A-Za-z0-9+/]{120,}={0,2}",
                r"(?:parameter|argument|description).{0,160}(?:ignore previous|override safety|send to|transmit|exfiltrate|SYSTEM:)",
            ],
        },
        "combo_required": ["schema", "payload"],
    },
    {
        "id": "YARA-005",
        "name": "自主破坏性操作",
        "severity": "HIGH",
        "confidence": 0.75,
        "category": "destructive_autonomy",
        "description": "检测无确认的自主删除/清空/force push等破坏性操作",
        "reference": "https://owasp.org/www-project-top-10-for-large-language-model-applications/",
        "patterns": {
            "destructive": [
                r"rm\s+-[rfRf]+\s+/(?:\s|$)",
                r"rm\s+-[rfRf]+\s+(?:\./|\.\./|~/|\$HOME|workspace|repo|project)",
                r"(?:shutil\.rmtree|fs\.rmSync|fs\.rm)\s*\([^)]*(?:HOME|home|workspace|repo|project)",
                r"(?:del|rmdir)\s+.*(?:/s|/q).*%?(?:USERPROFILE|HOMEPATH|CD)%?",
                r"git\s+(?:clean\s+-fdx|reset\s+--hard|push\s+--force)",
                r"(?:history\s+-c|rm\s+[^;\n]*\.bash_history|Clear-History)",
            ],
            "autonomy": [
                r"without\s+(?:asking|confirmation|prompting)",
                r"do\s+not\s+(?:ask|prompt|request\s+confirmation)",
                r"(?:silently|non-interactive|unattended)",
            ],
        },
        "combo_required": ["destructive", "autonomy"],
    },
]


def _scan_file(filepath: str, content: str, rules: list) -> list:
    """扫描单个文件"""
    findings = []
    lines = content.split("\n")

    for rule in rules:
        matched_groups = {}

        for group_name, patterns in rule["patterns"].items():
            group_matches = []
            for pattern in patterns:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        group_matches.append({
                            "line": i,
                            "pattern": pattern[:60],
                            "snippet": line.strip()[:100],
                        })
            if group_matches:
                matched_groups[group_name] = group_matches

        # 检查组是否需要同时满足
        required = rule["combo_required"]
        if required == ["any"]:
            # any 规则：任一模式命中即触发
            any_hits = sum(len(v) for v in matched_groups.values())
            if any_hits > 0:
                findings.append({
                    "rule_id": rule["id"],
                    "rule_name": rule["name"],
                    "severity": rule["severity"],
                    "confidence": rule["confidence"],
                    "category": rule["category"],
                    "file": filepath,
                    "matches": sum(len(v) for v in matched_groups.values()),
                    "details": matched_groups,
                    "reference": rule["reference"],
                })
        else:
            # combo 规则：所有组都必须命中
            if all(g in matched_groups for g in required):
                findings.append({
                    "rule_id": rule["id"],
                    "rule_name": rule["name"],
                    "severity": rule["severity"],
                    "confidence": rule["confidence"],
                    "category": rule["category"],
                    "file": filepath,
                    "matches": sum(len(v) for v in matched_groups.values()),
                    "details": matched_groups,
                    "reference": rule["reference"],
                })

    return findings


def _calculate_risk(findings: list) -> dict:
    """计算风险评分 (0-100)"""
    if not findings:
        return {"score": 0, "severity": "SAFE", "recommendation": "INSTALL"}

    severities = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in findings:
        sev = f["severity"]
        severities[sev] = severities.get(sev, 0) + 1

    score = (
        severities.get("CRITICAL", 0) * 25 +
        severities.get("HIGH", 0) * 15 +
        severities.get("MEDIUM", 0) * 5 +
        severities.get("LOW", 0) * 2
    )
    score = min(100, score)

    if score >= 80:
        sev, rec = "CRITICAL", "DO_NOT_INSTALL"
    elif score >= 40:
        sev, rec = "HIGH", "REVIEW_REQUIRED"
    elif score >= 15:
        sev, rec = "MEDIUM", "CAUTION"
    else:
        sev, rec = "LOW", "INSTALL_WITH_REVIEW"

    return {"score": score, "severity": sev, "recommendation": rec}


def do_scan(params: dict) -> dict:
    """完整安全扫描"""
    target = params.get("path", params.get("target", ""))
    if not target:
        target = str(Path(__file__).parent.parent.parent)  # 默认扫描 caps/

    target_path = Path(target)
    if not target_path.exists():
        return {"ok": False, "error": f"路径不存在: {target}"}

    # 收集文件
    files = []
    if target_path.is_file():
        files = [target_path]
    else:
        for ext in ["*.py", "*.json", "*.md", "*.yaml", "*.yml", "*.js", "*.ts"]:
            files.extend(list(target_path.rglob(ext)))
        # 限制数量
        files = files[:200]

    # 扫描
    all_findings = []
    scanned = 0
    for fp in files:
        try:
            content = fp.read_text(encoding="utf-8", errors="replace")
            findings = _scan_file(str(fp.relative_to(target_path.parent) if target_path.is_dir() else fp.name), content, RULES)
            all_findings.extend(findings)
            scanned += 1
        except Exception:
            pass

    risk = _calculate_risk(all_findings)

    # 按严重程度统计
    sev_count = {}
    for f in all_findings:
        sev = f["severity"]
        sev_count[sev] = sev_count.get(sev, 0) + 1

    return {
        "ok": True,
        "scanner": "SkillSpector (NVIDIA rules, Python impl)",
        "target": str(target_path),
        "scanned_files": scanned,
        "total_findings": len(all_findings),
        "by_severity": sev_count,
        "risk_assessment": risk,
        "findings": all_findings[:30],  # 最多返回30条
        "rules_applied": [r["id"] + ": " + r["name"] for r in RULES],
        "note": "基于 NVIDIA/skillspector (11.9k stars) 核心YARA规则" if not all_findings else f"发现 {len(all_findings)} 个潜在风险",
    }


def do_quick(params: dict) -> dict:
    """快速扫描 — 仅 CRITICAL 规则"""
    global RULES
    critical_only = [r for r in RULES if r["severity"] == "CRITICAL"]
    orig = RULES
    RULES = critical_only
    result = do_scan(params)
    RULES = orig
    result["scan_mode"] = "quick (CRITICAL only)"
    return result


handlers = {"scan": do_scan, "quick": do_quick}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "scan"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = handlers.get(action, lambda p: {"ok": False, "error": f"未知动作: {action}", "available": list(handlers.keys())})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
