# 开发者：自由的风
"""self_diagnostic/run.py — 自诊断系统
全栈健康检测: Python环境 / 依赖 / 配置 / Git / 安全扫描 / 修复
"""
import sys, json, os, re, struct, subprocess, importlib, warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent.parent  # GBT-JXDWD/
SANDBOX_DIR = PROJECT_DIR / "sandbox"

# ─── helpers ───────────────────────────────────────────

def _try_import(name: str) -> tuple:
    """Returns (available, version_string_or_error)"""
    try:
        mod = importlib.import_module(name)
        ver = getattr(mod, '__version__', None)
        if ver is None:
            try:
                ver = mod.version
            except Exception:
                ver = None
        if ver is None:
            ver = "已安装"
        return True, str(ver) if ver != "已安装" else ver
    except BaseException as e:
        # Catch BaseException to handle numpy/cv2 native crashes
        return False, type(e).__name__ + ": " + str(e)[:200]

def _run_cmd(cmd: list, timeout: int = 15, cwd: str = None) -> dict:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                          encoding="utf-8", errors="replace", cwd=cwd)
        return {"ok": r.returncode == 0, "stdout": r.stdout.strip(), "stderr": r.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "超时"}
    except FileNotFoundError:
        return {"ok": False, "error": f"命令未找到: {cmd[0]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ─── check sections ────────────────────────────────────

def _check_python_environment() -> list:
    issues = []

    # Python version
    py_ver = sys.version_info
    ver_str = f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}"
    if py_ver < (3, 9):
        issues.append(f"Python版本过低: {ver_str} (建议 >= 3.9)")
    else:
        issues.append(f"Python {ver_str} ✓")

    # 64-bit
    is_64 = struct.calcsize("P") == 8
    if not is_64:
        issues.append("非64位Python (部分依赖可能受限)")

    # Executable path
    issues.append(f"解释器: {sys.executable}")

    # Platform
    issues.append(f"平台: {sys.platform} / {os.name}")

    # virtualenv / venv check
    in_venv = sys.prefix != sys.base_prefix
    if in_venv:
        issues.append(f"虚拟环境: ✓ ({sys.prefix})")
    else:
        pass  # not an issue

    # pip available
    pip_ok, pip_info = _try_import("pip")
    if not pip_ok:
        issues.append("pip 不可用 ⚠")

    return issues


def _check_dependencies() -> list:
    issues = []
    deps = [
        ("psutil",    "系统资源监控"),
        ("PIL",       "图像处理 (Pillow)"),
        ("requests",  "HTTP请求库"),
        ("pyautogui", "GUI自动化"),
        ("sqlite3",   "SQLite数据库"),
    ]
    for name, desc in deps:
        ok, info = _try_import(name)
        if ok:
            pass  # no issue
        else:
            issues.append(f"{desc} ({name}) 缺失: {info}")
    return issues


def _check_configs() -> list:
    issues = []

    # .env file
    env_files = list(PROJECT_DIR.glob(".env*"))
    env_file = PROJECT_DIR / ".env"
    if env_file.exists():
        content = env_file.read_text(encoding="utf-8")
        # Count non-empty, non-comment lines with = sign
        keys = [line.split("=")[0].strip() for line in content.splitlines()
                if line.strip() and not line.strip().startswith("#") and "=" in line]
        if keys:
            issues.append(f".env 存在, {len(keys)} 个配置项 ({', '.join(keys[:6])}{'…' if len(keys)>6 else ''})")
        else:
            issues.append(".env 存在但无配置项 ⚠")
    else:
        issues.append(".env 文件不存在 ⚠")
        if any(f.name == ".env.example" for f in env_files):
            issues.append("  提示: .env.example 存在, 可复制为 .env")

    # api_keys.json
    api_keys_file = PROJECT_DIR / "api_keys.json"
    if api_keys_file.exists():
        try:
            api_data = json.loads(api_keys_file.read_text(encoding="utf-8"))
            provider_count = len(api_data) if isinstance(api_data, dict) else 0
            issues.append(f"api_keys.json 存在, {provider_count} 个提供商")
        except json.JSONDecodeError:
            issues.append("api_keys.json 格式错误 ⚠")
    else:
        api_example = PROJECT_DIR / "api_keys.example.json"
        if api_example.exists():
            issues.append("api_keys.json 不存在 (api_keys.example.json 可作为模板)")
        else:
            issues.append("api_keys.json 不存在 ⚠")

    # License
    license_files = list(PROJECT_DIR.glob("LICEN[CS]E*")) + list(PROJECT_DIR.glob("license*"))
    if license_files:
        issues.append(f"许可证文件: {', '.join(f.name for f in license_files)} ✓")
    else:
        issues.append("无 LICENSE 文件 ⚠")

    # sandbox/caps count
    caps_dir = SANDBOX_DIR / "caps"
    if caps_dir.exists():
        cap_count = len([d for d in caps_dir.iterdir() if d.is_dir() and (d / "capability.json").exists()])
        issues.append(f"已安装能力模块: {cap_count} 个")

    return issues


def _check_git() -> list:
    issues = []

    # git available
    git = _run_cmd(["git", "--version"])
    if git["ok"]:
        issues.append(f"Git ✓ ({git['stdout']})")
    else:
        issues.append("Git 未安装或不在PATH ⚠")
        return issues

    # git status
    status = _run_cmd(["git", "status", "--porcelain"], cwd=str(PROJECT_DIR))
    if status["ok"]:
        lines = [l for l in status["stdout"].splitlines() if l.strip()]
        if lines:
            modified = [l[3:].strip() for l in lines if l[:2].strip()]
            issues.append(f"未提交变更: {len(lines)} 个文件 ({', '.join(modified[:5])}{'…' if len(modified)>5 else ''})")
        else:
            issues.append("工作区干净 ✓")
    else:
        # maybe not a git repo
        if "not a git repository" in status.get("error", ""):
            issues.append("当前目录不是Git仓库 ⚠")
        else:
            issues.append(f"Git状态检查失败: {status.get('error', status.get('stderr', ''))}")

    # remote
    remote = _run_cmd(["git", "remote", "-v"], cwd=str(PROJECT_DIR))
    if remote["ok"] and remote["stdout"]:
        lines = remote["stdout"].splitlines()
        remotes = set()
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                remotes.add(f"{parts[0]}: {parts[1]}")
        issues.append(f"远程仓库: {len(remotes)} 个")
    elif remote["ok"]:
        issues.append("无远程仓库 ⚠")

    # branch
    branch = _run_cmd(["git", "branch", "--show-current"], cwd=str(PROJECT_DIR))
    if branch["ok"] and branch["stdout"]:
        issues.append(f"当前分支: {branch['stdout']}")

    return issues


HARDCODED_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey|api_secret|secret[_-]?key)\s*[:=]\s*["\'][A-Za-z0-9+/=_\-]{16,}["\']', "疑似硬编码 API Key"),
    (r'(?i)(password|passwd|pwd)\s*[:=]\s*["\'][^"\']{4,}["\']', "疑似硬编码密码"),
    (r'(?i)(token|access[_-]?token|auth[_-]?token)\s*[:=]\s*["\'][A-Za-z0-9+/=_\-]{16,}["\']', "疑似硬编码 Token"),
    (r'(?i)(private[_-]?key|PRIVATE[_-]?KEY)', "疑似硬编码私钥引用"),
    (r'(?i)(mongodb|mysql|postgresql|redis)://[^"\';\s]{10,}', "疑似硬编码数据库连接字符串"),
    (r'(?i)sk-[A-Za-z0-9]{16,}', "疑似 OpenAI API Key 格式"),
    (r'(?i)ghp_[A-Za-z0-9]{16,}', "疑似 GitHub Personal Access Token"),
    (r'(?i)gho_[A-Za-z0-9]{16,}', "疑似 GitHub OAuth Token"),
    (r'(?i)xox[bpras]-[A-Za-z0-9-]{10,}', "疑似 Slack Token"),
]


def _check_security(quick: bool = False) -> list:
    issues = []

    # Scan Python files in sandbox/caps for hardcoded keys (limit scope for quick)
    scan_dirs = [SANDBOX_DIR / "caps"]
    if not quick:
        scan_dirs.append(PROJECT_DIR)

    scanned = 0
    findings = []

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for py_file in scan_dir.rglob("*.py"):
            if any(p in str(py_file) for p in ['__pycache__', '.git', 'node_modules', '.venv', 'venv', 'site-packages']):
                continue
            scanned += 1
            try:
                content = py_file.read_text(encoding="utf-8")
                for lineno, line in enumerate(content.splitlines(), 1):
                    for pattern, label in HARDCODED_PATTERNS:
                        m = re.search(pattern, line)
                        if m:
                            # Skip obvious false positives: test files, example keys (***)
                            matched = m.group(0)
                            if '***' in matched:
                                continue
                            if '.example' in str(py_file) or 'example' in str(py_file).lower():
                                continue
                            if 'YOUR_' in matched or 'your_' in matched:
                                continue
                            snippet = matched[:80].replace('\n', '\\n')
                            findings.append({
                                "file": str(py_file.relative_to(PROJECT_DIR)),
                                "line": lineno,
                                "type": label,
                                "sample": snippet,
                            })
                            break  # one finding per line
            except Exception:
                pass

    if findings:
        by_severity = {}
        for f in findings:
            by_severity.setdefault(f["type"], []).append(f"{f['file']}:{f['line']}")
        for sev, locs in sorted(by_severity.items()):
            issues.append(f"{sev}: {len(locs)} 处 ({', '.join(locs[:3])}{'…' if len(locs)>3 else ''})")
    else:
        issues.append("未发现硬编码凭据 ✓")

    issues.append(f"已扫描: {scanned} 个文件")
    return issues


# ─── action handlers ───────────────────────────────────

def _score_sections(sections: dict) -> tuple:
    """Calculate overall score as N/M"""
    total_checks = 0
    passed = 0
    all_issues = 0

    for section_name, items in sections.items():
        for item in items:
            total_checks += 1
            if '✓' in item and '⚠' not in item:
                passed += 1
            elif '⚠' in item or '缺失' in item or '疑似' in item:
                all_issues += 1

    # In findgins with "疑似" in security items, count each
    for item in sections.get("security", []):
        if "处" in item and "未发现" not in item:
            # already counted once above
            pass

    return f"{passed}/{total_checks}", all_issues


def do_full(params):
    sections = {
        "python":       _check_python_environment(),
        "dependencies": _check_dependencies(),
        "configs":      _check_configs(),
        "git":          _check_git(),
        "security":     _check_security(quick=False),
    }

    score, issue_count = _score_sections(sections)

    fixes = []
    for item in sections["dependencies"]:
        if "缺失" in item:
            if "psutil" in item.lower():
                fixes.append("pip install psutil")
            if "Pillow" in item.lower() or "PIL" in item.lower():
                fixes.append("pip install Pillow")
            if "requests" in item.lower():
                fixes.append("pip install requests")

    return {
        "ok": True,
        "score": score,
        "issues": issue_count,
        "sections": sections,
        "fixes_available": list(set(fixes)),
    }


def do_quick(params):
    sections = {
        "python":       _check_python_environment(),
        "dependencies": _check_dependencies(),
        "configs":      _check_configs()[:4],  # summary only
        "git":          _check_git()[:3],
        "security":     _check_security(quick=True),
    }

    score, issue_count = _score_sections(sections)

    fixes = []
    for item in sections["dependencies"]:
        if "缺失" in item:
            if "psutil" in item.lower():
                fixes.append("pip install psutil")
            if "Pillow" in item.lower() or "PIL" in item.lower():
                fixes.append("pip install Pillow")
            if "requests" in item.lower():
                fixes.append("pip install requests")

    return {
        "ok": True,
        "score": score,
        "issues": issue_count,
        "sections": sections,
        "fixes_available": list(set(fixes)),
    }


CRITICAL_DEPS = ["psutil", "requests", "Pillow"]

def do_fix(params):
    fixed = []
    failed = []

    # First, detect what's missing
    for dep in CRITICAL_DEPS:
        import_name = "PIL" if dep == "Pillow" else dep
        ok, _ = _try_import(import_name)
        if not ok:
            r = _run_cmd([sys.executable, "-m", "pip", "install", dep, "-q"], timeout=120)
            if r["ok"]:
                fixed.append(dep)
            else:
                failed.append({"dep": dep, "error": r.get("error", r.get("stderr", "未知错误"))})

    # Re-run quick check to get updated status
    sections = {
        "python":       _check_python_environment(),
        "dependencies": _check_dependencies(),
        "configs":      _check_configs()[:4],
        "git":          _check_git()[:3],
        "security":     _check_security(quick=True),
    }
    score, issue_count = _score_sections(sections)

    return {
        "ok": True,
        "action": "fix",
        "fixed": fixed,
        "failed": failed,
        "post_fix_diagnostic": {
            "score": score,
            "issues": issue_count,
            "dependencies": sections["dependencies"],
        },
    }


# ─── main ──────────────────────────────────────────────

handlers = {
    "full":  do_full,
    "quick": do_quick,
    "fix":   do_fix,
}

if __name__ == "__main__":
    # 标准规范: argv[1]=action  argv[2]=params_json (不读 stdin，防止永久阻塞)
    action = sys.argv[1] if len(sys.argv) > 1 else "quick"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    handler = handlers.get(action, lambda p: {"ok": False, "error": f"未知动作: {action}", "available": list(handlers.keys())})
    result = handler(params)
    print(json.dumps(result, ensure_ascii=False, default=str))
