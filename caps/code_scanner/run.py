# 开发者：自由的风
"""code_scanner/run.py — 代码层深度分析引擎·触手内置
====================================================
每个攻击/侦察触手都调用此引擎，不只扫表面，直接穿透代码层:
  - 安全漏洞模式库(SQL注入/XSS/命令注入/路径遍历/SSRF/反序列化)
  - 病毒/后门/恶意代码特征检测
  - 硬编码密钥/密码/Token泄露
  - 代码质量病因(Debug模式/堆栈泄露/异常处理缺陷)
  - 框架版本CVE关联分析
  - Semgrep AST级深度扫描(行业标准SAST)
"""
import sys, json, os, re, hashlib, base64, subprocess
from pathlib import Path

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ═══════════════════════════════════════════════════════════
#  安全漏洞模式库 — 触手自带的代码层感知
# ═══════════════════════════════════════════════════════════

SECURITY_PATTERNS = [
    # ── SQL注入 ──
    ("sql_injection_concat", r'(?i)(cursor\.execute\s*\(\s*["\'].*%\s*.*["\']|\.execute\s*\(\s*["\'].*\+.*["\']|\.execute\s*\(\s*f["\'])',
     "SQL注入: 字符串拼接构造查询", "critical",
     "使用参数化查询(?)或ORM代替字符串拼接"),

    ("sql_injection_raw", r'(?i)(\.raw\s*\(|\.execute\s*\(\s*["\'].*\$|db\.query\s*\()',
     "SQL注入: 原始查询可能拼接用户输入", "critical",
     "检查用户输入是否经过过滤或参数化"),

    # ── XSS ──
    ("xss_innerHTML", r'(?i)(\.innerHTML\s*=|document\.write\s*\(|\.outerHTML\s*=)',
     "XSS: 直接操作innerHTML/document.write", "critical",
     "使用textContent或DOMPurify过滤"),

    ("xss_reflect", r'(?i)(response\.write\s*\(\s*req\.|echo\s+\$_GET|print\s*\(\s*request\.)',
     "XSS: 用户输入直接回显到页面", "critical",
     "对所有输出做HTML实体编码"),

    ("xss_attr", r'(?i)(<\w+[^>]*\$\{.*\}[^>]*>)',
     "XSS: 模板变量未转义注入HTML属性", "high",
     "使用模板引擎的自动转义功能"),

    # ── 命令注入 ──
    ("cmd_injection", r'(?i)(os\.system\s*\(.*\$|subprocess\.call\s*\(.*\$|exec\s*\(.*\$|eval\s*\(.*\$|`.*\$.*`)',
     "命令注入: 用户输入拼接到系统命令", "critical",
     "使用subprocess.run([cmd, arg1, arg2])数组形式"),

    ("cmd_injection_shell", r'(?i)(shell_exec\s*\(|popen\s*\(|passthru\s*\()',
     "命令注入: PHP命令执行函数", "critical",
     "禁用shell_exec/popen/passthru, 使用白名单"),

    # ── 路径遍历 ──
    ("path_traversal", r'(?i)(open\s*\(.*\.\.\/|file_get_contents\s*\(.*\.\.|readFile\s*\(.*\.\.)',
     "路径遍历: 用户输入用于文件路径", "critical",
     "使用路径白名单+真实路径校验"),

    # ── 反序列化 ──
    ("deserialization", r'(?i)(pickle\.loads\s*\(|yaml\.load\s*\(.*Loader|unserialize\s*\()',
     "反序列化: 不可信数据反序列化", "critical",
     "避免反序列化不可信数据, pickle→json"),

    # ── SSRF ──
    ("ssrf", r'(?i)(requests\.get\s*\(.*url|urllib.*urlopen.*url|curl_setopt.*CURLOPT_URL.*\$_)',
     "SSRF: 用户控制URL发起请求", "high",
     "URL白名单+禁止内网IP"),

    # ── 认证缺陷 ──
    ("hardcoded_secret", r'(?i)(api_key\s*=\s*["\'][A-Za-z0-9_\-]{20,}["\']|secret\s*=\s*["\'][A-Za-z0-9_\-]{20,}["\']|password\s*=\s*["\'][^"\']+["\']|token\s*=\s*["\'][A-Za-z0-9_\-\.]{20,}["\'])',
     "硬编码密钥: API Key/Secret/Password/Token明文", "critical",
     "使用环境变量或密钥管理服务"),

    ("hardcoded_jwt", r'(?i)(["\'][A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+["\'])',
     "硬编码JWT Token", "high",
     "JWT不应硬编码在源码中"),

    # ── 弱加密 ──
    ("weak_crypto", r'(?i)(DES\s*\(|MD5\s*\(.*password|ECB\s*mode|RC4\s*\()',
     "弱加密: DES/MD5/ECB/RC4用于安全场景", "high",
     "使用AES-256-GCM或bcrypt/argon2"),

    # ── Debug/信息泄露 ──
    ("debug_enabled", r'(?i)(DEBUG\s*=\s*True|DEBUG\s*=\s*1|debug\s*:\s*true|APP_DEBUG\s*=\s*true)',
     "Debug模式开启: 生产环境危险", "critical",
     "生产环境必须关闭Debug模式"),

    ("stacktrace_leak", r'(?i)(printStackTrace\s*\(|console\.error\s*\(.*\.stack|traceback\.print_exc\s*\(\).*response)',
     "堆栈信息泄露: 异常堆栈返回给客户端", "high",
     "捕获异常后返回通用错误信息"),

    ("info_leak_path", r'(?i)(\.python|venv/|node_modules/|\.git/|\.env["\'\s])',
     "路径信息泄露", "medium",
     "移除错误信息中的文件系统路径"),

    # ── 权限问题 ──
    ("permission_chmod777", r'(?i)(chmod\s*\(.*0?777|os\.chmod.*0o777)',
     "权限过宽: chmod 777", "critical",
     "使用最小权限原则(644/755)"),

    ("sudo_in_script", r'(?i)(sudo\s+|os\.setuid\s*\(\s*0\s*\))',
     "提权操作: 脚本中使用sudo", "high",
     "避免脚本内提权, 用专门的权限管理"),
]

# ═══════════════════════════════════════════════════════════
#  病毒/后门/恶意代码特征库
# ═══════════════════════════════════════════════════════════

MALWARE_PATTERNS = [
    ("reverse_shell", r'(?i)(/bin/sh\s*-i|/bin/bash\s*-i|nc\s+-e\s+/bin|python\s+-c\s+.*socket\.socket|import\s+pty.*spawn)',
     "反弹Shell: 远程命令执行后门", "critical",
     "立即移除, 检查服务器是否已被入侵"),

    ("obfuscated_code", r'(?i)(eval\s*\(\s*(?:atob|base64\.b64decode|fromCharCode|String\.fromCharCode|__import__\s*\(\s*["\'].*decode))',
     "混淆代码: eval+base64解码执行", "critical",
     "解码base64内容检查恶意行为"),

    ("crypto_miner", r'(?i)(stratum\+tcp://|xmrig|cpuminer|coinhive|\.cryptonight|mining\.pool)',
     "挖矿病毒: 加密货币矿工程序", "critical",
     "立即清除, 检查CPU占用"),

    ("ransomware", r'(?i)(\.encrypt\(|\.encrypt_file|ransom|bitcoin.*wallet.*[A-Za-z0-9]{26,}|\.aes_encrypt.*all.*files)',
     "勒索软件: 文件加密+比特币钱包", "critical",
     "立即隔离系统, 从备份恢复"),

    ("keylogger", r'(?i)(pynput.*keyboard|keyboard\.on_press|GetAsyncKeyState|SetWindowsHookEx.*WH_KEYBOARD)',
     "键盘记录器: 捕获击键", "critical",
     "立即清除, 修改所有输入过的密码"),

    ("data_exfil", r'(?i)(requests\.post.*\.read\(\)|send\(.*open\(|\.upload.*\.read|curl.*-F.*@.*\.)',
     "数据外传: 读取本地文件并发送到外部", "critical",
     "检查外传目标地址, 立即阻断"),

    ("backdoor_web", r'(?i)(preg_replace\s*\(\s*["\']/.*/e|assert\s*\(\s*\$_(?:GET|POST|REQUEST)|system\s*\(\s*\$_(?:GET|POST))',
     "Web后门: 一句话木马/代码执行后门", "critical",
     "立即删除, 全站文件扫描"),

    ("backdoor_php", r'(?i)(<\?php\s+(?:eval|assert|system|exec|shell_exec|passthru)\s*\(\s*\$_(?:GET|POST|REQUEST|COOKIE))',
     "PHP后门: eval/assert执行用户输入", "critical",
     "立即删除恶意文件, 检查上传目录"),

    ("privilege_escalation", r'(?i)(/etc/shadow|/etc/sudoers.*NOPASSWD|setuid\s*\(\s*0\s*\)|chmod\s*\+s)',
     "提权代码: 修改系统权限文件", "critical",
     "检查权限变更, 审计sudo配置"),

    ("persistence", r'(?i)(schtasks\s+/create|Registry.*\\Run|systemctl\s+enable|crontab.*@reboot|\.bashrc.*>>)',
     "持久化后门: 开机自启动/计划任务", "critical",
     "清理所有非授权自启动项"),
]

# ═══════════════════════════════════════════════════════════
#  代码质量病因检测
# ═══════════════════════════════════════════════════════════

CODE_QUALITY_PATTERNS = [
    ("todo_fixme", r'(?i)(TODO|FIXME|HACK|XXX|WORKAROUND|TEMP)',
     "代码标记: 未完成的TODO/FIXME", "info",
     "评估是否需要立即修复"),

    ("bare_except", r'(?i)(except\s*:)',
     "裸except: 捕获所有异常可能隐藏bug", "warning",
     "指定具体异常类型"),

    ("empty_catch", r'(?i)(except\s+\w+:\s*\n\s*pass)',
     "空异常处理: 吞掉异常静默失败", "warning",
     "至少记录日志"),

    ("resource_leak", r'(?i)(open\s*\([^)]*\)(?!.*\bwith\b).*\n(?!.*\.close))',
     "资源泄露: 文件未关闭", "warning",
     "使用with语句自动管理资源"),

    ("infinite_loop_risk", r'(?i)(while\s+True\s*:(?!.*\bbreak\b)(?!.*\btime\.sleep\b))',
     "潜在死循环: while True无退出条件", "warning",
     "添加break条件或超时机制"),
]


def _scan_text(text, patterns, source="unknown"):
    """通用的模式扫描器 — 每根触手都调用这个"""
    findings = []
    for pattern_id, pattern, description, severity, fix in patterns:
        matches = list(re.finditer(pattern, text, re.MULTILINE))
        if matches:
            for m in matches[:3]:  # 每种最多3个实例
                ctx_start = max(0, m.start() - 40)
                ctx_end = min(len(text), m.end() + 40)
                context = text[ctx_start:ctx_end].replace('\n', ' ').replace('\r', '')
                findings.append({
                    "pattern_id": pattern_id,
                    "finding": description,
                    "severity": severity,
                    "fix": fix,
                    "match": m.group(0)[:100],
                    "context": context[:120],
                    "source": source,
                })

    return findings


def do_scan(params):
    """扫描代码文本(直接传入代码字符串)"""
    code = params.get("code", params.get("text", params.get("content", "")))
    source = params.get("source", "inline")

    if not code:
        return {"ok": False, "error": "缺少 code/text/content 参数"}

    security = _scan_text(code, SECURITY_PATTERNS, source)
    malware = _scan_text(code, MALWARE_PATTERNS, source)
    quality = _scan_text(code, CODE_QUALITY_PATTERNS, source)

    all_findings = security + malware + quality
    critical = [f for f in all_findings if f["severity"] == "critical"]

    return {
        "ok": True,
        "cap": "code_scanner",
        "action": "scan",
        "domain": "AI编程",
        "source": source,
        "total_findings": len(all_findings),
        "critical_count": len(critical),
        "categories": {
            "security": len(security),
            "malware": len(malware),
            "quality": len(quality),
        },
        "findings": all_findings,
        "verdict": "发现严重问题" if critical else "发现警告" if all_findings else "代码干净",
    }


def do_scan_file(params):
    """扫描代码文件"""
    path = params.get("path", params.get("file", ""))
    if not path:
        return {"ok": False, "error": "缺少 path/file 参数"}

    try:
        p = Path(path)
        if not p.exists():
            return {"ok": False, "error": f"文件不存在: {path}"}

        code = p.read_text(encoding="utf-8", errors="replace")
        return do_scan({"code": code, "source": str(p)})
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def do_scan_response(params):
    """扫描HTTP响应体(从攻击cap传入)"""
    body = params.get("body", params.get("response", ""))
    url = params.get("url", params.get("source", "http_response"))

    if not body:
        return {"ok": False, "error": "缺少 body/response 参数"}

    return do_scan({"code": body, "source": url})


def do_semgrep_scan(params):
    """Semgrep AST级深度扫描 — 行业标准SAST引擎
    
    参数:
        target: 要扫描的目录或文件路径
    返回:
        正则扫描 + Semgrep 合并报告
    """
    target = params.get("target", params.get("dir", params.get("path", "")))
    if not target:
        return {"ok": False, "error": "缺少 target/dir/path 参数"}
    
    target_path = Path(target)
    if not target_path.exists():
        return {"ok": False, "error": f"目标不存在: {target}"}
    
    # 1) 检查 Semgrep 是否已安装
    semgrep_installed = False
    semgrep_version = None
    try:
        check = subprocess.run(
            ["semgrep", "--version"],
            capture_output=True, text=True, timeout=10
        )
        semgrep_installed = (check.returncode == 0)
        if semgrep_installed:
            semgrep_version = check.stdout.strip().split("\n")[0]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    # 2) 用触手正则引擎扫描所有文件
    regex_findings = []
    if target_path.is_dir():
        for f in target_path.rglob("*"):
            if f.is_file() and f.suffix in {".py", ".js", ".ts", ".java", ".go", ".rb", ".php",
                                              ".c", ".cpp", ".h", ".hpp", ".cs", ".swift", ".kt",
                                              ".rs", ".sh", ".bash", ".yaml", ".yml", ".json",
                                              ".xml", ".html", ".htm", ".sql", ".toml", ".cfg"}:
                try:
                    code = f.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue
                for pat_set in [SECURITY_PATTERNS, MALWARE_PATTERNS, CODE_QUALITY_PATTERNS]:
                    regex_findings.extend(_scan_text(code, pat_set, str(f)))
    elif target_path.is_file():
        try:
            code = target_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return {"ok": False, "error": f"无法读取文件: {target}"}
        for pat_set in [SECURITY_PATTERNS, MALWARE_PATTERNS, CODE_QUALITY_PATTERNS]:
            regex_findings.extend(_scan_text(code, pat_set, str(target_path)))
    
    # 3) Semgrep AST 级扫描
    semgrep_findings = []
    semgrep_available = False
    
    if semgrep_installed:
        try:
            result = subprocess.run(
                ["semgrep", "--config=auto", "--json", "--no-git-ignore", str(target_path)],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode in (0, 1):  # 0=clean, 1=findings found
                try:
                    data = json.loads(result.stdout)
                except json.JSONDecodeError:
                    pass
                else:
                    semgrep_available = True
                    for entry in data.get("results", []):
                        semgrep_findings.append({
                            "pattern_id": entry.get("check_id", "semgrep-unknown"),
                            "finding": entry.get("extra", {}).get("message", "Semgrep finding"),
                            "severity": _map_semgrep_severity(entry.get("extra", {}).get("severity", "")),
                            "fix": entry.get("extra", {}).get("fix", ""),
                            "match": entry.get("extra", {}).get("lines", ""),
                            "context": f"{entry.get('path', '')}:{entry.get('start', {}).get('line', '?')}",
                            "source": entry.get("path", str(target_path)),
                            "engine": "semgrep",
                        })
        except (subprocess.TimeoutExpired, Exception):
            pass  # semgrep超时或出错时回退到纯正则报告
    
    # 4) 合并报告
    all_findings = regex_findings + semgrep_findings
    critical = [f for f in all_findings if f["severity"] == "critical"]
    security = [f for f in all_findings if f["severity"] in ("critical", "high", "medium", "low")]
    
    result = {
        "ok": True,
        "cap": "code_scanner",
        "action": "semgrep",
        "domain": "AI编程",
        "target": str(target_path),
        "total_findings": len(all_findings),
        "critical_count": len(critical),
        "regex_findings": len(regex_findings),
        "semgrep_findings": len(semgrep_findings),
        "semgrep_available": semgrep_available,
        "semgrep_version": semgrep_version,
        "engine": "regex + semgrep" if semgrep_available else "regex",
        "findings": all_findings,
        "verdict": "发现严重问题" if critical else "发现警告" if all_findings else "代码干净",
    }
    
    if not semgrep_installed:
        result["semgrep_note"] = "Semgrep未安装。运行: pip install semgrep 以启用AST级深度扫描"
    
    return result


def _map_semgrep_severity(sev):
    """Semgrep severity → 统一severity等级"""
    mapping = {
        "ERROR": "critical",
        "WARNING": "high",
        "INFO": "medium",
    }
    return mapping.get(sev.upper(), "low")


HANDLERS = {
    "scan": do_scan,
    "scan_file": do_scan_file,
    "scan_response": do_scan_response,
    "semgrep": do_semgrep_scan,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "scan"
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
