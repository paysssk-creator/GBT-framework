# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""root_cause_debugger/run.py — 病因定位引擎
按 假设 -> 取证 -> 复现 -> 修复 -> 验证 的链路调查问题，并归档证据。
"""
import ast
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None

PROJECT_DIR = Path(__file__).resolve().parents[3]
CASE_HOME = Path.home() / ".gbt" / "root_cause_cases"
CASE_HOME.mkdir(parents=True, exist_ok=True)

TEXT_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".toml", ".md", ".txt",
    ".yaml", ".yml", ".ini", ".cfg", ".env", ".rs", ".go", ".java", ".cs",
    ".sql", ".sh", ".ps1", ".bat",
}
SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build",
    "target", ".idea", ".vscode", ".next", ".cache",
}
STOPWORDS = {
    "the", "and", "for", "that", "with", "this", "from", "have", "your",
    "http", "https", "www", "when", "what", "why", "how", "does", "into",
    "帮我", "这个", "那个", "一个", "已经", "现在", "还是", "然后",
}
HYPOTHESIS_RULES = [
    {
        "key": "syntax_or_format",
        "title": "语法或格式错误",
        "triggers": ["syntaxerror", "jsondecodeerror", "toml", "格式错误", "unterminated", "invalid syntax"],
        "verify": "先对目标文件跑语法/格式校验，确认是否在解析阶段就失败。",
        "fix": "修正语法、逗号、引号、缩进或配置格式后重跑复现。",
    },
    {
        "key": "dependency_missing",
        "title": "依赖缺失或版本不匹配",
        "triggers": ["modulenotfounderror", "importerror", "no module named", "命令未找到", "not recognized", "版本过低"],
        "verify": "检查 import/命令失败点，对照环境依赖和 PATH 是否存在。",
        "fix": "补装缺失依赖、锁定版本，或切回与运行环境一致的解释器。",
    },
    {
        "key": "path_or_file_missing",
        "title": "路径、文件或资源不存在",
        "triggers": ["no such file", "filenotfounderror", "找不到", "不存在", "missing", "路径"],
        "verify": "确认报错路径是否真实存在，是否相对路径基准错误。",
        "fix": "修正 cwd、资源路径、文件生成顺序或部署产物位置。",
    },
    {
        "key": "config_or_secret_missing",
        "title": "配置缺失或环境变量不完整",
        "triggers": [".env", "环境变量", "config", "apikey", "token", "secret", "未配置"],
        "verify": "核对 .env、api_keys.json、配置模板与当前环境变量。",
        "fix": "补齐配置并保持 dev/staging/prod 模板同构。",
    },
    {
        "key": "permission_or_auth",
        "title": "权限、认证或鉴权失败",
        "triggers": ["permission denied", "403", "401", "unauthorized", "forbidden", "access denied", "权限"],
        "verify": "确认当前账号、令牌、文件权限和远端 ACL 是否允许该动作。",
        "fix": "修复令牌权限、文件权限或账号范围后再验证。",
    },
    {
        "key": "network_or_connectivity",
        "title": "网络、端口或连通性异常",
        "triggers": ["timeout", "timed out", "connection refused", "dns", "socket", "network", "无法连接", "超时"],
        "verify": "检查目标地址、端口、DNS 和本地网络可达性。",
        "fix": "修正地址、端口、防火墙或代理设置，并补重试策略。",
    },
    {
        "key": "state_or_cache",
        "title": "状态污染、缓存或旧进程残留",
        "triggers": ["stale", "cache", "旧", "残留", "占用", "already in use", "port", "lock"],
        "verify": "检查旧进程、临时文件、缓存目录和锁文件是否干扰当前运行。",
        "fix": "清理残留状态并固定启动/停止顺序。",
    },
    {
        "key": "logic_regression",
        "title": "代码逻辑回归或条件分支错误",
        "triggers": ["unexpected", "should", "业务", "回归", "逻辑", "not work", "失败但无异常"],
        "verify": "沿调用链检查关键分支、默认值和最近改动位置。",
        "fix": "在最小影响范围内修正分支逻辑，并补验证用例。",
    },
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _case_id() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _run_cmd(cmd, timeout=15, cwd=None):
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return {
            "ok": result.returncode == 0,
            "stdout": (result.stdout or "").strip(),
            "stderr": (result.stderr or "").strip(),
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"命令超时 ({timeout}s)", "exit_code": -1}
    except FileNotFoundError:
        return {"ok": False, "error": f"命令未找到: {cmd[0]}", "exit_code": -2}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "exit_code": -3}


def _run_shell_command(command: str, timeout=30, cwd=None) -> dict:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            shell=True,
        )
        return {
            "ok": result.returncode == 0,
            "stdout": (result.stdout or "").strip(),
            "stderr": (result.stderr or "").strip(),
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"命令超时 ({timeout}s)", "exit_code": -1}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "exit_code": -3}


def _extract_keywords(issue: str) -> list[str]:
    raw = []
    raw.extend(re.findall(r"[A-Za-z_][A-Za-z0-9_\-]{2,}", issue))
    raw.extend(re.findall(r"[\u4e00-\u9fff]{2,6}", issue))
    seen = []
    for token in raw:
        norm = token.strip().lower()
        if norm in STOPWORDS or norm.isdigit():
            continue
        if norm not in seen:
            seen.append(norm)
    return seen[:10]


def _normalize_paths(items, workspace: Path) -> list[Path]:
    paths = []
    for item in items or []:
        p = Path(item)
        if not p.is_absolute():
            p = (workspace / p).resolve()
        paths.append(p)
    return paths


def _safe_read_text(path: Path, limit_lines=120, limit_chars=5000) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return f"[读取失败] {exc}"
    lines = text.splitlines()[:limit_lines]
    snippet = "\n".join(lines)
    if len(snippet) > limit_chars:
        snippet = snippet[:limit_chars] + "\n...[truncated]"
    return snippet


def _probe_file(path: Path) -> dict:
    probe = {
        "path": str(path),
        "exists": path.exists(),
        "type": "missing",
        "checks": [],
        "snippet": "",
    }
    if not path.exists():
        probe["checks"].append({"name": "exists", "ok": False, "detail": "文件或目录不存在"})
        return probe
    probe["type"] = "dir" if path.is_dir() else "file"
    if path.is_dir():
        try:
            children = sorted(p.name for p in path.iterdir())[:20]
            probe["checks"].append({"name": "list_dir", "ok": True, "detail": f"{len(children)} entries", "sample": children})
        except Exception as exc:
            probe["checks"].append({"name": "list_dir", "ok": False, "detail": str(exc)})
        return probe

    probe["snippet"] = _safe_read_text(path)
    suffix = path.suffix.lower()
    if suffix == ".py":
        compile_result = _run_cmd([sys.executable, "-m", "py_compile", str(path)], timeout=20, cwd=str(PROJECT_DIR))
        probe["checks"].append({
            "name": "py_compile",
            "ok": compile_result.get("ok", False),
            "detail": compile_result.get("stderr") or compile_result.get("error") or "ok",
        })
        try:
            ast.parse(path.read_text(encoding="utf-8", errors="replace"))
            probe["checks"].append({"name": "ast_parse", "ok": True, "detail": "AST 解析通过"})
        except Exception as exc:
            probe["checks"].append({"name": "ast_parse", "ok": False, "detail": str(exc)})
    elif suffix == ".json":
        try:
            json.loads(path.read_text(encoding="utf-8"))
            probe["checks"].append({"name": "json_parse", "ok": True, "detail": "JSON 解析通过"})
        except Exception as exc:
            probe["checks"].append({"name": "json_parse", "ok": False, "detail": str(exc)})
    elif suffix == ".toml" and tomllib is not None:
        try:
            tomllib.loads(path.read_text(encoding="utf-8"))
            probe["checks"].append({"name": "toml_parse", "ok": True, "detail": "TOML 解析通过"})
        except Exception as exc:
            probe["checks"].append({"name": "toml_parse", "ok": False, "detail": str(exc)})
    else:
        probe["checks"].append({"name": "read_text", "ok": True, "detail": "已抓取文本片段"})
    return probe


def _iter_search_files(workspace: Path, focus_files: Optional[list[Path]] = None):
    if focus_files:
        for path in focus_files:
            if path.exists() and path.is_file() and path.suffix.lower() in TEXT_EXTS:
                yield path
        return
    if not workspace.exists():
        return
    for root, dirs, files in os.walk(workspace):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            if name.startswith("."):
                continue
            path = Path(root) / name
            if path.suffix.lower() in TEXT_EXTS:
                yield path


def _search_workspace(workspace: Path, keywords: list[str], limit=20, focus_files: Optional[list[Path]] = None) -> list[dict]:
    lowered = [k.lower() for k in keywords if k.strip()]
    if not lowered:
        return []
    hits = []
    for path in _iter_search_files(workspace, focus_files):
        try:
            rel = str(path.relative_to(workspace))
        except ValueError:
            rel = str(path)
        try:
            for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                line_lower = line.lower()
                matched = [kw for kw in lowered if kw in line_lower]
                if matched:
                    hits.append({
                        "file": rel,
                        "line": lineno,
                        "match": matched[0],
                        "text": line.strip()[:220],
                    })
                    if len(hits) >= limit:
                        return hits
        except Exception:
            continue
    return hits


def _collect_self_diagnostic() -> dict:
    try:
        sandbox_dir = PROJECT_DIR / "sandbox"
        if str(sandbox_dir) not in sys.path:
            sys.path.insert(0, str(sandbox_dir))
        from capability_protocol import get_engine  # pylint: disable=import-error

        engine = get_engine()
        return engine.call("self_diagnostic", "quick", {})
    except Exception as exc:
        return {"ok": False, "error": f"self_diagnostic 调用失败: {exc}"}


def _collect_git_snapshot(workspace: Path) -> dict:
    status = _run_cmd(["git", "status", "--short"], timeout=10, cwd=str(workspace))
    branch = _run_cmd(["git", "branch", "--show-current"], timeout=10, cwd=str(workspace))
    return {
        "branch": branch.get("stdout", ""),
        "dirty": bool(status.get("stdout")),
        "status_lines": status.get("stdout", "").splitlines()[:20],
    }


def _run_repro(command: str, workspace: Path, attempts: int = 1, timeout_sec: int = 30) -> dict:
    runs = []
    stable = "unknown"
    ok_count = 0
    fail_count = 0
    for idx in range(1, max(1, attempts) + 1):
        result = _run_shell_command(command, timeout=timeout_sec, cwd=str(workspace))
        entry = {
            "attempt": idx,
            "ok": result.get("ok", False),
            "exit_code": result.get("exit_code"),
            "stdout": (result.get("stdout") or "")[:2000],
            "stderr": (result.get("stderr") or result.get("error") or "")[:2000],
        }
        runs.append(entry)
        if entry["ok"]:
            ok_count += 1
        else:
            fail_count += 1
    if ok_count and fail_count:
        stable = "flaky"
    elif fail_count and not ok_count:
        stable = "stable_fail"
    elif ok_count and not fail_count:
        stable = "stable_pass"
    return {
        "command": command,
        "attempts": runs,
        "summary": {
            "ok_count": ok_count,
            "fail_count": fail_count,
            "stability": stable,
            "timeout_sec": timeout_sec,
        },
    }


def _write_text(path: Path, content: str, encoding: str = "utf-8") -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)
    return str(path)


def _shell_escape_single_quotes(text: str) -> str:
    return text.replace("'", "''")


def _create_repro_bundle(case_dir: Path, workspace: Path, runtime_repro: Optional[dict], issue: str) -> dict:
    bundle = {
        "runtime_dir": "",
        "repro_ps1": "",
        "repro_cmd": "",
        "manifest_json": "",
        "attempt_logs": [],
    }
    if not runtime_repro:
        return bundle

    runtime_dir = case_dir / "runtime"
    repro_dir = case_dir / "repro"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    repro_dir.mkdir(parents=True, exist_ok=True)
    bundle["runtime_dir"] = str(runtime_dir)

    attempt_logs = []
    for item in runtime_repro.get("attempts", []):
        stem = f"runtime_attempt_{item['attempt']}"
        payload = {
            "attempt": item["attempt"],
            "ok": item["ok"],
            "exit_code": item["exit_code"],
            "stdout": item.get("stdout", ""),
            "stderr": item.get("stderr", ""),
        }
        json_path = runtime_dir / f"{stem}.json"
        txt_path = runtime_dir / f"{stem}.log"
        _write_text(json_path, json.dumps(payload, ensure_ascii=False, indent=2))
        _write_text(
            txt_path,
            f"attempt={item['attempt']}\nok={item['ok']}\nexit_code={item['exit_code']}\n\n[stdout]\n{item.get('stdout', '')}\n\n[stderr]\n{item.get('stderr', '')}\n",
        )
        attempt_logs.append({"json": str(json_path), "log": str(txt_path)})
    bundle["attempt_logs"] = attempt_logs

    command = runtime_repro.get("command", "")
    escaped_command = _shell_escape_single_quotes(command)
    ps1_content = f"""$ErrorActionPreference = 'Continue'
$workspace = '{_shell_escape_single_quotes(str(workspace))}'
$command = '{escaped_command}'
Write-Host 'GBT root cause repro'
Write-Host 'Issue: {issue}'
Write-Host "Workspace: $workspace"
Write-Host "Command: $command"
Set-Location $workspace
Invoke-Expression $command
exit $LASTEXITCODE
"""
    cmd_content = (
        "@echo off\r\n"
        f"cd /d \"{workspace}\"\r\n"
        "powershell -NoProfile -ExecutionPolicy Bypass -File \"%~dp0repro_run.ps1\"\r\n"
        "exit /b %errorlevel%\r\n"
    )
    manifest = {
        "issue": issue,
        "workspace": str(workspace),
        "command": command,
        "generated_at": _now_iso(),
        "runtime_summary": runtime_repro.get("summary", {}),
    }
    bundle["repro_ps1"] = _write_text(repro_dir / "repro_run.ps1", ps1_content, encoding="utf-8-sig")
    bundle["repro_cmd"] = _write_text(repro_dir / "repro_run.cmd", cmd_content)
    bundle["manifest_json"] = _write_text(repro_dir / "repro_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    return bundle


def _diagnostic_summary_lines(diag: dict) -> list[str]:
    for key in ("summary_lines", "issues", "checks", "items"):
        value = diag.get(key)
        if isinstance(value, list):
            return [str(item) for item in value]
    findings = diag.get("findings")
    if isinstance(findings, list):
        return [str(item) for item in findings]
    return []


def _summarize_probe_failures(file_probes: list[dict]) -> list[str]:
    evidence = []
    for probe in file_probes:
        for check in probe.get("checks", []):
            if not check.get("ok", False):
                evidence.append(f"{Path(probe['path']).name} -> {check['name']}: {check.get('detail', '')}")
    return evidence


def _build_hypotheses(issue: str, file_probes: list[dict], diag: dict, search_hits: list[dict]) -> list[dict]:
    issue_lower = issue.lower()
    evidence_text = "\n".join(_summarize_probe_failures(file_probes))
    evidence_text += "\n" + json.dumps(diag, ensure_ascii=False, default=str)
    evidence_text += "\n" + "\n".join(hit["text"] for hit in search_hits)
    evidence_lower = evidence_text.lower()

    hypotheses = []
    for rule in HYPOTHESIS_RULES:
        score = 0
        matched = []
        for trigger in rule["triggers"]:
            trigger_lower = trigger.lower()
            if trigger_lower in issue_lower:
                score += 3
                matched.append(f"问题描述命中: {trigger}")
            if trigger_lower in evidence_lower:
                score += 2
                matched.append(f"证据命中: {trigger}")
        if not score and rule["key"] == "logic_regression":
            score = 1
            matched.append("兜底逻辑假设")
        hypotheses.append({
            "key": rule["key"],
            "title": rule["title"],
            "score": score,
            "why": matched[:4],
            "verify": rule["verify"],
            "fix": rule["fix"],
        })
    hypotheses.sort(key=lambda item: item["score"], reverse=True)
    return hypotheses


def _apply_runtime_hypotheses(hypotheses: list[dict], runtime_evidence: Optional[dict]) -> list[dict]:
    if not runtime_evidence:
        return hypotheses
    summary = runtime_evidence.get("summary", {})
    stability = summary.get("stability", "")
    attempts = runtime_evidence.get("attempts", [])
    last_error_text = "\n".join(
        ((item.get("stderr") or "") + "\n" + (item.get("stdout") or "")).lower()
        for item in attempts
    )
    for item in hypotheses:
        if item["key"] == "state_or_cache" and stability == "flaky":
            item["score"] += 4
            item["why"].append("运行时重试出现时好时坏，疑似状态污染或竞态")
        if item["key"] == "network_or_connectivity" and any(k in last_error_text for k in ["timeout", "refused", "dns", "socket", "network"]):
            item["score"] += 4
            item["why"].append("运行时日志命中网络/超时关键词")
        if item["key"] == "path_or_file_missing" and any(k in last_error_text for k in ["no such file", "not found", "找不到", "不存在"]):
            item["score"] += 4
            item["why"].append("运行时日志命中找不到文件/路径")
        if item["key"] == "dependency_missing" and any(k in last_error_text for k in ["modulenotfounderror", "no module named", "not recognized"]):
            item["score"] += 4
            item["why"].append("运行时日志命中依赖或命令缺失")
    hypotheses.sort(key=lambda row: row["score"], reverse=True)
    return hypotheses


def _build_plan(issue: str, keywords: list[str], workspace: Path, files: list[Path]) -> dict:
    return {
        "question": issue,
        "workspace": str(workspace),
        "keywords": keywords,
        "investigation_plan": [
            "1. 先把问题改写成可验证的假设，而不是直接猜答案。",
            "2. 对指定文件和高相关代码片段做静态取证，记录失败点。",
            "3. 收集环境与依赖自诊断，排除环境不一致。",
            "4. 从证据里选出最可能根因，给出最小复现与修复验证步骤。",
        ],
        "target_files": [str(p) for p in files],
    }


def _write_report(case_dir: Path, report: dict) -> tuple[str, str]:
    json_path = case_dir / "report.json"
    md_path = case_dir / "report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    hypotheses_md = "\n".join(
        f"- {item['title']} | 分数 {item['score']} | 依据: {'; '.join(item['why']) or '暂无强证据'}"
        for item in report["hypotheses"][:5]
    )
    evidence_md = "\n".join(f"- {line}" for line in report["decisive_evidence"]) or "- 暂无决定性证据"
    hits_md = "\n".join(
        f"- `{hit['file']}:{hit['line']}` 命中 `{hit['match']}`: {hit['text']}"
        for hit in report["search_hits"][:12]
    ) or "- 未命中相关代码片段"
    runtime_md = "- 未执行运行时复现"
    if report.get("runtime_repro"):
        rr = report["runtime_repro"]
        runtime_md = "\n".join(
            f"- 第{item['attempt']}次 | ok={item['ok']} | exit={item['exit_code']} | stderr={item['stderr'][:160] or '--'}"
            for item in rr.get("attempts", [])
        )
    repro_bundle_md = "- 未生成复现资产"
    if report.get("repro_bundle", {}).get("repro_ps1"):
        rb = report["repro_bundle"]
        repro_bundle_md = "\n".join([
            f"- PowerShell: `{rb.get('repro_ps1', '')}`",
            f"- CMD: `{rb.get('repro_cmd', '')}`",
            f"- Manifest: `{rb.get('manifest_json', '')}`",
            f"- Runtime Dir: `{rb.get('runtime_dir', '')}`",
        ])
    verify_md = "\n".join(f"- {step}" for step in report["verification_steps"])
    md = f"""# 病因定位报告

- 案件编号: `{report['case_id']}`
- 时间: `{report['created_at']}`
- 问题: {report['issue']}
- 工作区: `{report['workspace']}`

## 调查链路
- 假设
- 取证
- 复现
- 修复
- 验证

## 最可能根因
- {report['most_likely_root_cause']}

## 假设排序
{hypotheses_md}

## 决定性证据
{evidence_md}

## 代码命中
{hits_md}

## 运行时复现
{runtime_md}

## 复现资产
{repro_bundle_md}

## 验证步骤
{verify_md}
"""
    md_path.write_text(md, encoding="utf-8")
    return str(json_path), str(md_path)


def do_plan(params: Optional[dict] = None) -> dict:
    params = params or {}
    issue = params.get("issue", params.get("prompt", params.get("question", ""))).strip()
    if not issue:
        return {"ok": False, "error": "缺少 issue/prompt/question"}
    workspace = Path(params.get("workspace", PROJECT_DIR)).resolve()
    files = _normalize_paths(params.get("files", []), workspace)
    keywords = _extract_keywords(issue)
    return {
        "ok": True,
        "mode": "plan",
        "plan": _build_plan(issue, keywords, workspace, files),
    }


def do_investigate(params: Optional[dict] = None) -> dict:
    params = params or {}
    issue = params.get("issue", params.get("prompt", params.get("question", ""))).strip()
    if not issue:
        return {"ok": False, "error": "缺少 issue/prompt/question"}

    workspace = Path(params.get("workspace", PROJECT_DIR)).resolve()
    files = _normalize_paths(params.get("files", []), workspace)
    keywords = _extract_keywords(issue)
    case_id = _case_id()
    case_dir = CASE_HOME / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    file_probes = [_probe_file(path) for path in files]
    if not file_probes and params.get("path"):
        file_probes.append(_probe_file(_normalize_paths([params["path"]], workspace)[0]))
    runtime_repro = None
    repro_command = str(params.get("cmd", "")).strip()
    if repro_command:
        runtime_repro = _run_repro(
            repro_command,
            workspace=workspace,
            attempts=int(params.get("attempts", 2) or 2),
            timeout_sec=int(params.get("timeout_sec", 30) or 30),
        )
    focus_files = [path for path in files if path.exists() and path.is_file()]
    if runtime_repro and not focus_files:
        search_hits = []
    else:
        search_hits = _search_workspace(workspace, keywords, limit=18, focus_files=focus_files or None)
    diag = _collect_self_diagnostic()
    git_snapshot = _collect_git_snapshot(workspace)
    hypotheses = _build_hypotheses(issue, file_probes, diag, search_hits)
    hypotheses = _apply_runtime_hypotheses(hypotheses, runtime_repro)

    decisive_evidence = _summarize_probe_failures(file_probes)
    if diag.get("ok"):
        summary_lines = _diagnostic_summary_lines(diag)
        for item in summary_lines[:5]:
            decisive_evidence.append(str(item))
    for hit in search_hits[:5]:
        decisive_evidence.append(f"{hit['file']}:{hit['line']} => {hit['text']}")
    if runtime_repro:
        decisive_evidence.append(
            f"运行时复现: {runtime_repro['summary']['stability']} | ok={runtime_repro['summary']['ok_count']} fail={runtime_repro['summary']['fail_count']}"
        )
        for item in runtime_repro.get("attempts", [])[:3]:
            stderr = item.get("stderr") or item.get("stdout") or "--"
            decisive_evidence.append(f"attempt#{item['attempt']} exit={item['exit_code']} => {stderr[:180]}")
    decisive_evidence = decisive_evidence[:12]

    top = hypotheses[0] if hypotheses else {
        "title": "暂未收敛到单一根因",
        "verify": "继续补日志和复现步骤。",
        "fix": "先把复现条件固定下来。",
    }
    verification_steps = [
        f"先按假设 `{top['title']}` 做最小复现。",
        top["verify"],
        "修复后重跑同一复现路径，确认错误不再出现。",
        "再做一次回归检查，确认没有引入新的环境或配置偏差。",
    ]
    repro_bundle = _create_repro_bundle(case_dir, workspace, runtime_repro, issue)
    if repro_bundle.get("repro_cmd"):
        verification_steps.insert(1, f"可直接执行 `{repro_bundle['repro_cmd']}` 复跑同一案例。")

    report = {
        "ok": True,
        "case_id": case_id,
        "created_at": _now_iso(),
        "issue": issue,
        "workspace": str(workspace),
        "keywords": keywords,
        "plan": _build_plan(issue, keywords, workspace, files),
        "git_snapshot": git_snapshot,
        "self_diagnostic": diag,
        "runtime_repro": runtime_repro,
        "repro_bundle": repro_bundle,
        "file_probes": file_probes,
        "search_hits": search_hits,
        "hypotheses": hypotheses,
        "most_likely_root_cause": top["title"],
        "decisive_evidence": decisive_evidence,
        "repair_strategy": top["fix"],
        "verification_steps": verification_steps,
    }
    json_path, md_path = _write_report(case_dir, report)
    report["report_json"] = json_path
    report["report_md"] = md_path
    (case_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


# ═══════════════════════════════════════════════════════════
#  auto_debug_loop — 监控日志中的Python traceback并自动调试
# ═══════════════════════════════════════════════════════════

HYPOTHESIS_BANK_DIR = CASE_HOME.parent / "hypothesis_bank"
TRACEBACK_PATTERN = re.compile(
    r'Traceback\s*\(most recent call last\):.*?(?=^[A-Za-z]+\w*Error:|\Z)',
    re.DOTALL | re.MULTILINE
)
ERROR_LINE_PATTERN = re.compile(r'^([A-Za-z]+\w*Error):\s*(.+)$', re.MULTILINE)
FILE_LINE_PATTERN = re.compile(r'File\s+"([^"]+)",\s*line\s+(\d+),?\s*in\s+(\S+)')


def _ensure_hypothesis_bank():
    HYPOTHESIS_BANK_DIR.mkdir(parents=True, exist_ok=True)


def _parse_traceback(text: str) -> dict | None:
    """从文本中提取Python traceback信息"""
    tb_match = TRACEBACK_PATTERN.search(text)
    if not tb_match:
        return None
    tb_text = tb_match.group(0)

    # 提取文件/行号/函数
    frames = []
    for m in FILE_LINE_PATTERN.finditer(tb_text):
        frames.append({"file": m.group(1), "line": int(m.group(2)), "function": m.group(3)})

    # 提取最终错误类型和消息
    err_match = ERROR_LINE_PATTERN.search(tb_text)
    error_type = err_match.group(1) if err_match else "UnknownError"
    error_msg = err_match.group(2).strip() if err_match else tb_text.strip().split('\n')[-1].strip()

    return {
        "error_type": error_type,
        "error_message": error_msg,
        "frames": frames,
        "full_traceback": tb_text.strip(),
        "signature": _error_signature_v2(error_type, error_msg, frames),
    }


def _error_signature_v2(error_type: str, error_msg: str, frames: list) -> str:
    """生成错误签名用于去重"""
    key_files = ":".join(f.get("file", "").split("/")[-1] for f in frames[-3:])
    msg_short = re.sub(r'\d+', 'N', error_msg[:40])
    return f"{error_type}:{msg_short}:{key_files}"


def _read_watch_logs(log_path: str, last_pos: int = 0) -> tuple[str, int]:
    """读取日志文件增量内容"""
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            if last_pos > 0:
                f.seek(last_pos)
            content = f.read()
            new_pos = f.tell()
        return content, new_pos
    except FileNotFoundError:
        return "", 0


def do_auto_debug_loop(params: Optional[dict] = None) -> dict:
    """监控日志文件中的Python traceback并自动触发调试

    params:
        log_path: 要监控的日志路径 (默认 ~/.gbt/errors.log)
        poll_interval: 轮询间隔秒数 (默认3.0)
        max_rounds: 最大轮次 (默认20, 0=无限)
        auto_fix: 是否自动尝试修复 (默认False)
        watch: 是否持续轮询 (默认True)
        last_pos: 恢复监听的字节位置
    """
    params = params or {}
    log_path = params.get("log_path", str(Path.home() / ".gbt" / "errors.log"))
    poll_interval = float(params.get("poll_interval", 3.0))
    max_rounds = int(params.get("max_rounds", 20))
    auto_fix = params.get("auto_fix", False)
    watch = params.get("watch", True)
    last_pos = int(params.get("last_pos", 0))

    _ensure_hypothesis_bank()
    resolved_sigs = set()
    debug_results = []
    round_num = 0

    while max_rounds == 0 or round_num < max_rounds:
        round_num += 1
        new_content, last_pos = _read_watch_logs(log_path, last_pos)
        if not new_content.strip():
            if not watch:
                break
            time.sleep(poll_interval)
            continue

        # 尝试从新内容中提取traceback
        tb = _parse_traceback(new_content)
        if not tb:
            if not watch:
                break
            time.sleep(poll_interval)
            continue

        sig = tb["signature"]
        if sig in resolved_sigs:
            continue  # 已处理过

        # 从假设银行检索匹配的假设
        bank_hits = do_hypothesis_bank({"action": "search", "query": sig,
                                         "error_type": tb["error_type"]})

        # 构建调查假设
        hypotheses = _build_hypotheses(
            tb["error_message"],
            [],  # file_probes — 由investigate填充
            _collect_self_diagnostic(),
            []
        )

        # 如有银行命中，合并历史假设
        if bank_hits.get("matches"):
            for m in bank_hits["matches"]:
                hypotheses.append({"source": "bank", "key": m.get("key", ""),
                                    "title": m.get("hypothesis", ""),
                                    "fix": m.get("fix", ""),
                                    "confidence": m.get("confidence", 0.5) * 0.8})

        # 按置信度排序
        hypotheses.sort(key=lambda h: h.get("confidence", 0.3), reverse=True)

        round_result = {
            "round": round_num,
            "signature": sig,
            "error_type": tb["error_type"],
            "error_message": tb["error_message"][:300],
            "frames_count": len(tb["frames"]),
            "hypotheses_count": len(hypotheses),
            "top_hypothesis": hypotheses[0]["title"] if hypotheses else "none",
            "bank_hits": len(bank_hits.get("matches", [])),
        }

        # 自动修复模式
        if auto_fix and hypotheses:
            top = hypotheses[0]
            fix_result = do_fix_attempt({
                "hypothesis_key": top.get("key", "unknown"),
                "error_type": tb["error_type"],
                "error_message": tb["error_message"],
                "frames": tb["frames"],
                "proposed_fix": top.get("fix", ""),
            })
            round_result["fix_attempt"] = fix_result

        debug_results.append(round_result)
        resolved_sigs.add(sig)

        # 将本轮假设存入银行
        for h in hypotheses[:3]:
            do_hypothesis_bank({
                "action": "store",
                "key": h.get("key", f"auto_{round_num}"),
                "hypothesis": h.get("title", ""),
                "error_type": tb["error_type"],
                "fix": h.get("fix", ""),
                "confidence": h.get("confidence", 0.5),
                "evidence": str(h.get("evidence", [])),
                "signature": sig,
            })

        if not watch:
            break
        time.sleep(poll_interval)

    return {
        "ok": True,
        "rounds": round_num,
        "tracebacks_found": len(debug_results),
        "results": debug_results,
        "last_pos": last_pos,
        "watch_mode": watch,
    }


def do_hypothesis_bank(params: Optional[dict] = None) -> dict:
    """假设银行：存储和检索过去的调试假设

    params:
        action: "store" | "search" | "list" | "stats"
        key: 假设键名 (store/search)
        hypothesis: 假设描述 (store)
        error_type: 错误类型 (store/search)
        fix: 修复建议 (store)
        confidence: 置信度 0-1 (store)
        evidence: 证据描述 (store)
        query: 搜索关键词 (search)
        signature: 错误签名 (store)
        limit: 搜索结果上限 (search, 默认10)
    """
    _ensure_hypothesis_bank()
    action = (params or {}).get("action", "search")

    if action == "store":
        key = (params or {}).get("key", "")
        if not key:
            key = datetime.now().strftime("%Y%m%d%H%M%S")

        entry = {
            "key": key,
            "hypothesis": (params or {}).get("hypothesis", ""),
            "error_type": (params or {}).get("error_type", ""),
            "fix": (params or {}).get("fix", ""),
            "confidence": float((params or {}).get("confidence", 0.5)),
            "evidence": (params or {}).get("evidence", ""),
            "signature": (params or {}).get("signature", ""),
            "stored_at": _now_iso(),
            "use_count": 0,
            "success_count": 0,
        }

        entry_path = HYPOTHESIS_BANK_DIR / f"{key}.json"
        if entry_path.exists():
            try:
                existing = json.loads(entry_path.read_text(encoding="utf-8"))
                existing["use_count"] = existing.get("use_count", 0) + 1
                existing["last_updated"] = _now_iso()
                existing["confidence"] = max(existing.get("confidence", 0.5),
                                              entry["confidence"])
                entry = existing
            except Exception:
                pass

        entry_path.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "action": "store", "key": key,
                "path": str(entry_path)}

    elif action == "search":
        query = ((params or {}).get("query", "") +
                 " " + (params or {}).get("error_type", "")).strip().lower()
        limit = int((params or {}).get("limit", 10))

        matches = []
        try:
            for f in sorted(HYPOTHESIS_BANK_DIR.glob("*.json"), key=os.path.getmtime, reverse=True):
                try:
                    entry = json.loads(f.read_text(encoding="utf-8"))
                except Exception:
                    continue
                score = 0
                searchable = (entry.get("hypothesis", "") + " " +
                               entry.get("error_type", "") + " " +
                               entry.get("signature", "")).lower()
                for word in query.split():
                    if word in searchable:
                        score += 1
                if score > 0:
                    entry["_score"] = score
                    matches.append(entry)
        except FileNotFoundError:
            pass

        matches.sort(key=lambda m: (m.get("_score", 0), m.get("confidence", 0)), reverse=True)
        matches = matches[:limit]

        return {"ok": True, "action": "search", "query": query,
                "found": len(matches), "matches": matches}

    elif action == "list":
        entries = []
        try:
            for f in sorted(HYPOTHESIS_BANK_DIR.glob("*.json"), key=os.path.getmtime, reverse=True):
                try:
                    entries.append(json.loads(f.read_text(encoding="utf-8")))
                except Exception:
                    continue
        except FileNotFoundError:
            pass
        return {"ok": True, "action": "list", "count": len(entries), "entries": entries}

    elif action == "stats":
        total = 0
        total_confidence = 0.0
        by_type = {}
        try:
            for f in HYPOTHESIS_BANK_DIR.glob("*.json"):
                try:
                    e = json.loads(f.read_text(encoding="utf-8"))
                    total += 1
                    total_confidence += e.get("confidence", 0.5)
                    et = e.get("error_type", "unknown")
                    by_type[et] = by_type.get(et, 0) + 1
                except Exception:
                    continue
        except FileNotFoundError:
            pass
        return {"ok": True, "action": "stats",
                "total": total,
                "avg_confidence": round(total_confidence / max(total, 1), 2),
                "by_error_type": by_type}

    else:
        return {"ok": False, "error": f"未知 action: {action}",
                "valid_actions": ["store", "search", "list", "stats"]}


def do_fix_attempt(params: Optional[dict] = None) -> dict:
    """提出并自动测试修复方案

    params:
        hypothesis_key: 假设键名
        error_type: 错误类型
        error_message: 错误消息
        frames: traceback帧列表 [{file, line, function}]
        proposed_fix: 提议的修复描述
        test_command: 用于验证的命令 (可选)
        dry_run: 仅提议不执行 (默认True)
    """
    params = params or {}
    hypothesis_key = params.get("hypothesis_key", "unknown")
    error_type = params.get("error_type", "")
    error_message = params.get("error_message", "")
    frames = params.get("frames", [])
    proposed_fix = params.get("proposed_fix", "")
    test_command = params.get("test_command", "")
    dry_run = params.get("dry_run", True)

    result = {
        "ok": False,
        "hypothesis_key": hypothesis_key,
        "error_type": error_type,
        "dry_run": dry_run,
        "phases": {},
    }

    # Phase 1: 分析受影响文件
    affected_files = []
    for f in frames:
        fp = Path(f.get("file", ""))
        if fp.exists():
            affected_files.append({
                "path": str(fp),
                "line": f.get("line", 0),
                "function": f.get("function", ""),
                "exists": True,
            })
        else:
            affected_files.append({
                "path": str(fp),
                "line": f.get("line", 0),
                "function": f.get("function", ""),
                "exists": False,
            })

    result["phases"]["file_analysis"] = {
        "affected_files_count": len(affected_files),
        "files": affected_files,
    }

    # Phase 2: 从假设银行检索匹配的修复方案
    bank = do_hypothesis_bank({
        "action": "search",
        "query": hypothesis_key,
        "error_type": error_type,
        "limit": 5,
    })

    prior_fixes = []
    for m in bank.get("matches", []):
        if m.get("fix"):
            prior_fixes.append({
                "key": m.get("key", ""),
                "fix": m.get("fix", ""),
                "confidence": m.get("confidence", 0.5),
                "success_count": m.get("success_count", 0),
            })

    result["phases"]["prior_knowledge"] = {
        "bank_hits": len(prior_fixes),
        "prior_fixes": prior_fixes,
    }

    # Phase 3: 生成修复计划
    fix_plan = {
        "error_type": error_type,
        "error_message": error_message[:300],
        "proposed_action": proposed_fix or "手动分析并修复",
        "target_files": [f["path"] for f in affected_files if f["exists"]],
        "strategy": "incremental",  # incremental | rollback | replacement
    }

    # 匹配HYPOTHESIS_RULES获取预置修复步骤
    error_lower = error_message.lower()
    for rule in HYPOTHESIS_RULES:
        if any(t in error_lower for t in rule.get("triggers", [])):
            fix_plan["matched_rule"] = rule["key"]
            fix_plan["verify_step"] = rule.get("verify", "")
            fix_plan["fix_guidance"] = rule.get("fix", "")
            break

    result["phases"]["fix_plan"] = fix_plan

    # Phase 4: 执行测试（如果提供了命令且非dry_run）
    if test_command and not dry_run:
        test_result = _run_shell_command(test_command, timeout=60)
        result["phases"]["verification"] = {
            "command": test_command,
            "ok": test_result.get("ok", False),
            "stdout": (test_result.get("stdout", "") or "")[:500],
            "stderr": (test_result.get("stderr", "") or "")[:500],
        }
        result["ok"] = test_result.get("ok", False)
    elif dry_run:
        result["phases"]["verification"] = {"status": "skipped (dry_run)"}
        result["ok"] = True  # dry_run 成功生成计划即为OK

    # Phase 5: 更新假设银行成功率
    if not dry_run:
        bank_entry = HYPOTHESIS_BANK_DIR / f"{hypothesis_key}.json"
        if bank_entry.exists():
            try:
                entry = json.loads(bank_entry.read_text(encoding="utf-8"))
                if result["ok"]:
                    entry["success_count"] = entry.get("success_count", 0) + 1
                entry["last_tested_at"] = _now_iso()
                bank_entry.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass

    return result


HANDLERS = {
    "plan": do_plan,
    "investigate": do_investigate,
    "auto_debug": do_auto_debug_loop,
    "hypothesis": do_hypothesis_bank,
    "fix_attempt": do_fix_attempt,
}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知动作: {action}", "available": list(HANDLERS.keys())})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
