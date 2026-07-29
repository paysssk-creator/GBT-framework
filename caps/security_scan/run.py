# 开发者：自由的风
"""security_scan/run.py — 密钥泄露+危险模式全面扫描
==================================================
安全域 core — 扫描代码/文件中的密钥泄露、密码硬编码、危险模式。
支持20+种密钥格式识别 + 高熵字符串检测。
"""
import sys, json, os, re, math, datetime
from pathlib import Path
from collections import Counter

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ═══════════════════════════════════════════════════════════
#  密钥模式库 — 20+种云服务/API密钥格式
# ═══════════════════════════════════════════════════════════

SECRET_PATTERNS = [
    ("AWS Access Key", r'AKIA[0-9A-Z]{16}', "critical"),
    ("AWS Secret Key", r'(?i)aws.{0,20}(?:secret|key).{0,20}[0-9a-zA-Z/+]{40}', "critical"),
    ("GitHub Token", r'(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}', "critical"),
    ("GitHub OAuth", r'(?i)github.{0,20}(?:token|secret|key).{0,20}[0-9a-f]{40}', "critical"),
    ("Google API Key", r'AIza[0-9A-Za-z\-_]{35}', "critical"),
    ("Google OAuth", r'[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com', "critical"),
    ("Slack Token", r'xox[baprs]-[0-9A-Za-z\-]{10,}', "critical"),
    ("Slack Webhook", r'https://hooks\.slack\.com/services/T[a-zA-Z0-9_]{8,}/B[a-zA-Z0-9_]{8,}/[a-zA-Z0-9_]{24}', "critical"),
    ("Discord Token", r'[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}', "critical"),
    ("Telegram Bot Token", r'\d{9,10}:AA[0-9A-Za-z\-_]{33}', "critical"),
    ("Stripe Secret", r'(?:sk|rk)_(?:live|test)_[0-9a-zA-Z]{24,}', "critical"),
    ("Stripe Publishable", r'pk_(?:live|test)_[0-9a-zA-Z]{24,}', "warning"),
    ("Twilio SID", r'AC[a-f0-9]{32}', "critical"),
    ("Twilio Token", r'(?i)twilio.{0,20}(?:token|secret).{0,20}[a-f0-9]{32}', "critical"),
    ("OpenAI API Key", r'sk-[A-Za-z0-9]{32,}', "critical"),
    ("OpenAI Project Key", r'sk-proj-[A-Za-z0-9\-_]{32,}', "critical"),
    ("JWT Token", r'eyJ[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_.+/=]*', "warning"),
    ("Private Key PEM", r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----', "critical"),
    ("Bitcoin Private Key", r'[5KL][1-9A-HJ-NP-Za-km-z]{50,51}', "critical"),
    ("Ethereum Private Key", r'(?:0x)?[a-fA-F0-9]{64}', "high"),
    ("Generic Password", r'(?i)(?:password|passwd|pwd)\s*[:=]\s*["\'][^"\']{4,}["\']', "critical"),
    ("Generic API Key", r'(?i)(?:api[_-]?key|apikey)\s*[:=]\s*["\'][A-Za-z0-9\-_]{16,}["\']', "critical"),
    ("Generic Secret", r'(?i)(?:secret|token)\s*[:=]\s*["\'][A-Za-z0-9\-_]{16,}["\']', "critical"),
    ("Connection String", r'(?i)(?:mongodb|mysql|postgresql|postgres|redis|sqlite)://[^/\s]+:[^@\s]+@', "critical"),
    ("Generic Token in URL", r'(?i)[?&](?:token|api_key|apikey|access_token|auth)=[A-Za-z0-9\-_]{16,}', "critical"),
]


# ═══════════════════════════════════════════════════════════
#  危险代码模式 — eval/exec + shell注入 + 弱加密
# ═══════════════════════════════════════════════════════════

DANGER_PATTERNS = [
    # eval/exec
    (r'(?i)\beval\s*\(', "eval()代码执行", "critical"),
    (r'(?i)\bexec\s*\(', "exec()代码执行", "critical"),
    (r'(?i)\bcompile\s*\(', "compile()动态编译", "high"),
    (r'(?i)os\.system\s*\(', "os.system()命令执行", "warning"),
    (r'(?i)subprocess\.call\s*\(.*shell\s*=\s*True', "subprocess shell=True", "warning"),
    (r'(?i)subprocess\.(Popen|run|check_output)\s*\(.*shell\s*=\s*True', "subprocess shell注入", "warning"),
    (r'(?i)pickle\.loads?\s*\(', "pickle反序列化", "warning"),
    (r'(?i)yaml\.load\s*\(', "yaml.load()不安全", "warning"),
    (r'(?i)request\.get\s*\(.*verify\s*=\s*False', "SSL验证禁用", "warning"),
    (r'(?i)DEBUG\s*=\s*True', "DEBUG模式开启", "high"),

    # 命令/Shell注入
    (r'(?i);\s*(rm|cat|wget|curl|nc|bash|sh|powershell|cmd)\b', "命令注入(;)", "critical"),
    (r'(?i)\|\s*(rm|cat|wget|curl|nc|bash|sh|powershell|cmd)\b', "命令注入(|)", "critical"),
    (r'\$\{.*\}', "Shell变量注入", "warning"),
    (r'\$\(', "命令替换注入", "critical"),
    (r'`[^`]+`', "反引号命令执行", "critical"),
    (r'(?i)\bshell_exec\s*\(', "shell_exec()", "critical"),
    (r'(?i)\bpopen\s*\(', "popen()", "warning"),
    (r'(?i)\bpassthru\s*\(', "passthru()", "critical"),
    (r'(?i)\\x[0-9a-f]{2}', "Shell hex编码", "warning"),
    (r'(?i)\bimport\s+os\b.*\bsystem\b', "os.system导入+使用", "high"),

    # 弱加密
    (r'(?i)\bmd5\s*\(', "MD5散列(弱)", "high"),
    (r'(?i)\bsha1\s*\(', "SHA1散列(弱)", "high"),
    (r'(?i)\bDESede\b', "3DES加密(弱)", "high"),
    (r'(?i)\bRC4\b', "RC4流密码(弱)", "high"),
    (r'(?i)\bDES\b(?!ede)', "DES加密(弱)", "high"),
    (r'(?i)\bBlowfish\b', "Blowfish(过时)", "warning"),
    (r'(?i)ECB\b', "ECB模式(不安全)", "high"),
    (r'(?i)\brandom\b(?!.*SystemRandom)', "非加密随机数", "warning"),
    (r'(?i)math\.random\b', "math.random(非安全)", "warning"),
    (r'(?i)\bcrypt\.kdf\.PBKDF2HMAC\s*\(.*iterations\s*=\s*[0-9]{1,3}[^0-9]', "PBKDF2迭代次数过低", "warning"),
    (r'(?i)hashlib\.(md5|sha1)\s*\(', "hashlib弱算法", "high"),
    (r'(?i)ssl\.PROTOCOL_TLSv1[^2_]', "TLSv1.0/1.1(过时)", "high"),
]


def _entropy(data):
    """香农熵计算 — 检测高随机性字符串(可能的密钥)"""
    if not data:
        return 0
    counter = Counter(data)
    length = len(data)
    return -sum(count / length * math.log2(count / length) for count in counter.values())


def _scan_text(text, source="inline"):
    """扫描文本中的密钥"""
    findings = []

    # 模式匹配
    for name, pattern, severity in SECRET_PATTERNS:
        for m in re.finditer(pattern, text):
            match_text = m.group(0)
            # 截取上下文
            ctx_start = max(0, m.start() - 20)
            ctx_end = min(len(text), m.end() + 20)
            context = text[ctx_start:ctx_end].replace('\n', ' ')[:80]

            findings.append({
                "type": name,
                "severity": severity,
                "match": match_text[:80],
                "masked": match_text[:4] + "***" + match_text[-4:] if len(match_text) > 8 else "***",
                "context": context,
                "source": source,
            })

    # 高熵字符串检测
    for m in re.finditer(r'[A-Za-z0-9+/=]{32,}', text):
        match_text = m.group(0)
        if any(f["match"] == match_text[:80] for f in findings):
            continue
        ent = _entropy(match_text)
        if ent > 4.5:  # 高熵阈值
            findings.append({
                "type": "高熵字符串(疑似密钥)",
                "severity": "warning",
                "match": match_text[:40] + "...",
                "entropy": round(ent, 2),
                "source": source,
            })

    return findings


def do_scan(params):
    """扫描代码文本"""
    code = params.get("code", params.get("text", params.get("content", "")))
    source = params.get("source", "inline")

    if not code:
        return {"ok": False, "error": "缺少 code/text/content 参数"}

    findings = _scan_text(code, source)
    critical = [f for f in findings if f["severity"] == "critical"]

    # 脱敏处理: 返回结果中掩码敏感值
    safe_findings = []
    for f in findings:
        sf = dict(f)
        if "match" in sf and len(sf.get("match", "")) > 6:
            sf["match"] = sf["match"][:6] + "***"
        safe_findings.append(sf)

    return {
        "ok": True,
        "cap": "security_scan",
        "action": "scan",
        "domain": "安全域",
        "total_findings": len(findings),
        "critical_count": len(critical),
        "findings": safe_findings[:50],
        "verdict": "危险: 发现密钥泄露" if critical else "警告" if findings else "安全",
    }


def do_scan_keys(params):
    """仅扫描密钥模式"""
    return do_scan(params)


def do_scan_patterns(params):
    """扫描危险模式"""
    code = params.get("code", "")
    if not code:
        return {"ok": False, "error": "缺少 code 参数"}

    danger_patterns = [
        (r'(?i)eval\s*\(', "eval()代码执行", "critical"),
        (r'(?i)exec\s*\(', "exec()代码执行", "critical"),
        (r'(?i)os\.system\s*\(', "os.system()命令执行", "warning"),
        (r'(?i)subprocess\.call\s*\(.*shell\s*=\s*True', "subprocess shell=True", "warning"),
        (r'(?i)pickle\.loads?\s*\(', "pickle反序列化", "warning"),
        (r'(?i)yaml\.load\s*\(', "yaml.load()不安全", "warning"),
        (r'(?i)request\.get\s*\(.*verify\s*=\s*False', "SSL验证禁用", "warning"),
        (r'(?i)DEBUG\s*=\s*True', "DEBUG模式开启", "high"),
    ]

    findings = []
    for pattern, desc, severity in danger_patterns:
        for m in re.finditer(pattern, code):
            findings.append({
                "pattern": desc,
                "severity": severity,
                "line_content": code[max(0,m.start()-20):m.end()+40].replace('\n',' ')[:80],
            })

    return {
        "ok": True,
        "cap": "security_scan",
        "action": "scan_patterns",
        "findings": findings,
        "total": len(findings),
    }



AUDIT_LOG = Path.home() / ".gbt" / "security" / "audit_log.jsonl"
AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)


def _scan_cap_code(cap_dir: Path):
    """扫描单个cap的所有代码 — 返回findings汇总"""
    findings = {"secrets": [], "danger": [], "total": 0}
    for fname in ("run.py", "capability.json", "tool.py", "init.py"):
        fpath = cap_dir / fname
        if not fpath.exists():
            continue
        try:
            code = fpath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        findings["secrets"].extend(_scan_text(code, f"{cap_dir.name}/{fname}"))
        for pattern, desc, severity in DANGER_PATTERNS:
            for m in re.finditer(pattern, code):
                findings["danger"].append({
                    "pattern": desc,
                    "severity": severity,
                    "file": f"{cap_dir.name}/{fname}",
                    "line_content": code[max(0, m.start()-20):m.end()+40].replace('\n',' ')[:80],
                })
    findings["total"] = len(findings["secrets"]) + len(findings["danger"])
    return findings


def _score_from_findings(findings: dict) -> int:
    """根据findings计算安全评分 0-100"""
    score = 100
    severity_deductions = {
        "critical": 30, "high": 20, "warning": 5,
    }
    for f in findings.get("secrets", []):
        score -= severity_deductions.get(f.get("severity", "warning"), 5)
    for f in findings.get("danger", []):
        score -= severity_deductions.get(f.get("severity", "warning"), 5)
    return max(0, score)


def do_auto_audit_cycle(params):
    """全量安全审计：扫描所有caps，记录到audit_log.jsonl
    扫描维度：硬编码密钥、eval/exec、Shell注入、弱加密
    """
    scope = params.get("scope", "all")
    caps_root = Path(SANDBOX)
    ts = datetime.datetime.now().isoformat()

    results = []
    for cap_dir in sorted(caps_root.iterdir()):
        if not cap_dir.is_dir():
            continue
        if scope != "all" and cap_dir.name not in scope:
            continue
        findings = _scan_cap_code(cap_dir)
        score = _score_from_findings(findings)
        entry = {
            "cap": cap_dir.name,
            "score": score,
            "secret_count": len(findings["secrets"]),
            "danger_count": len(findings["danger"]),
            "secrets": [{"type": f["type"], "severity": f["severity"]}
                        for f in findings["secrets"]],
            "dangers": [{"pattern": f["pattern"], "severity": f["severity"]}
                        for f in findings["danger"]],
        }
        results.append(entry)

    # 持久化
    log_entry = {"ts": ts, "scope": scope, "total_caps": len(results),
                  "results": results}
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False, default=str) + "\n")

    scored = sorted(results, key=lambda x: x["score"])
    return {
        "ok": True,
        "cap": "security_scan",
        "action": "auto_audit_cycle",
        "ts": ts,
        "audit_log": str(AUDIT_LOG),
        "total_caps": len(results),
        "critical_caps": [r for r in results if r["score"] < 60],
        "top_risks": [r for r in scored[:5] if r["score"] < 80],
        "results": results,
    }


def do_score_cap(params):
    """对单个cap进行安全评分 0-100"""
    cap_name = params.get("cap", params.get("name", ""))
    caps_root = Path(SANDBOX)

    if cap_name:
        cap_dir = caps_root / cap_name
        if not cap_dir.is_dir():
            return {"ok": False, "error": f"cap {cap_name} 未找到"}
        findings = _scan_cap_code(cap_dir)
        score = _score_from_findings(findings)
        return {
            "ok": True, "cap": cap_name, "score": score,
            "secret_count": len(findings["secrets"]),
            "danger_count": len(findings["danger"]),
            "details": findings,
        }

    # 无cap名 → 返回所有cap评分
    scores = {}
    for cap_dir in sorted(caps_root.iterdir()):
        if not cap_dir.is_dir():
            continue
        findings = _scan_cap_code(cap_dir)
        scores[cap_dir.name] = {
            "score": _score_from_findings(findings),
            "secret_count": len(findings["secrets"]),
            "danger_count": len(findings["danger"]),
        }
    return {
        "ok": True,
        "action": "score_cap",
        "scores": scores,
        "average": round(sum(s["score"] for s in scores.values()) / max(len(scores), 1), 1),
    }


HANDLERS = {"scan": do_scan, "keys": do_scan_keys, "patterns": do_scan_patterns,
             "auto_audit_cycle": do_auto_audit_cycle, "score_cap": do_score_cap}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "scan"
    params_str = sys.argv[2] if len(sys.argv) > 2 else "{}"
    try:
        params = json.loads(params_str)
    except Exception:
        params = {}
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
