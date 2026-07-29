# 开发者：自由的风
"""cicd/run.py — CI/CD流水线管理
=================================
运维域 ready — 构建/测试/部署流水线触发与监控
"""
import sys, json, os, re, subprocess, time, traceback, shlex
from pathlib import Path
from datetime import datetime

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_LOG = Path.home() / ".gbt" / "builds"
BUILD_LOG.mkdir(parents=True, exist_ok=True)

CLOUD_LLM = os.path.join(SANDBOX, "cloud_llm", "run.py")

# Error classification patterns for self-healing
ERROR_PATTERNS = [
    # (regex, category, fix_strategy)
    (r"ModuleNotFoundError|No module named ['\"](\w+)", "import_error", "pip_install"),
    (r"ImportError|cannot import", "import_error", "pip_install"),
    (r"SyntaxError|IndentationError", "syntax_error", "git_checkout"),
    (r"pip install|install.*(?:required|missing)|dependency", "dependency", "pip_install"),
    (r"timed out|Timeout|timeout after", "timeout", "retry"),
    (r"Permission denied|Access denied|EACCES|EPERM", "permission", "chmod_fix"),
    (r"TypeError|AttributeError|NameError|ValueError", "runtime_error", "llm_suggest"),
    (r"error|fail|exception|traceback", "unknown", "retry"),
]

def do_trigger(params):
    """触发流水线 — 捕获每步耗时与状态"""
    name = params.get("name", f"build_{int(time.time())}")
    steps = params.get("steps", [
        {"name": "lint", "cmd": "echo lint check"},
        {"name": "test", "cmd": "echo run tests"},
        {"name": "build", "cmd": "echo build artifact"},
    ])

    log_lines = [f"=== GBT CICD Pipeline: {name} ===", f"Started: {datetime.now().isoformat()}"]
    results = []
    success = True
    started_at = time.time()

    for step in steps:
        log_lines.append(f"\n--- Step: {step['name']} ---")
        t0 = time.time()
        try:
            cmd_parts = shlex.split(step["cmd"])
            r = subprocess.run(cmd_parts, capture_output=True, text=True,
                               timeout=step.get("timeout", 120), cwd=str(SANDBOX))
            elapsed_ms = int((time.time() - t0) * 1000)
            ok = r.returncode == 0
            log_lines.append(r.stdout[:500] if r.stdout else "")
            if r.stderr:
                log_lines.append(f"STDERR: {r.stderr[:200]}")
            results.append({"step": step["name"], "ok": ok, "returncode": r.returncode,
                            "elapsed_ms": elapsed_ms, "status": "passed" if ok else "failed"})
            if not ok:
                success = False
                break
        except subprocess.TimeoutExpired:
            elapsed_ms = int((time.time() - t0) * 1000)
            results.append({"step": step["name"], "ok": False, "error": "timeout",
                            "elapsed_ms": elapsed_ms, "status": "timeout"})
            success = False
            break
        except Exception as e:
            elapsed_ms = int((time.time() - t0) * 1000)
            results.append({"step": step["name"], "ok": False, "error": str(e)[:100],
                            "elapsed_ms": elapsed_ms, "status": "error"})
            success = False
            break

    total_elapsed_ms = int((time.time() - started_at) * 1000)
    log_lines.append(f"\n=== Pipeline {'PASSED' if success else 'FAILED'} ===")
    log_lines.append(f"Total elapsed: {total_elapsed_ms}ms")
    log_path = BUILD_LOG / f"{name}.log"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")

    return {"ok": True, "cap": "cicd", "action": "trigger", "domain": "运维域",
            "pipeline": name, "success": success, "steps": results,
            "log": str(log_path), "total_steps": len(steps),
            "total_elapsed_ms": total_elapsed_ms}

def do_status(params):
    """查看构建状态"""
    builds = sorted(BUILD_LOG.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    recent = []
    for b in builds[:10]:
        content = b.read_text(encoding="utf-8")[:200]
        passed = "PASSED" in content
        recent.append({"name": b.stem, "passed": passed, "modified": datetime.fromtimestamp(b.stat().st_mtime).isoformat()})
    return {"ok": True, "builds": recent, "total": len(builds)}

def do_deploy(params):
    import sys; sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from brain.chain_kernel import enforce_chain
    enforce_chain("cicd.deploy")
    remote = params.get("remote", "origin")
    branch = params.get("branch", "main")
    restart_cmd = params.get("restart_cmd", "sudo systemctl restart gbt")
    steps = []

    # Step 1: git push
    push_cmd = ["git", "push", remote, branch]
    push = subprocess.run(push_cmd, capture_output=True, text=True, timeout=120)
    steps.append({
        "step": "git_push",
        "cmd": " ".join(push_cmd),
        "exit_code": push.returncode,
        "stdout": push.stdout.strip()[:2000],
        "stderr": push.stderr.strip()[:2000],
    })
    if push.returncode != 0:
        return {"ok": False, "cap": "cicd", "action": "deploy", "target": target,
                "error": "git push failed", "steps": steps}

    # Step 2: remote restart via SSH or local deploy script
    remote_host = os.environ.get("REMOTE_HOST", "")
    sandbox = Path(SANDBOX)
    deploy_sh = sandbox / "deploy.sh"
    deploy_ps1 = sandbox / "deploy.ps1"

    restart_step = None
    if remote_host:
        ssh_cmd = ["ssh", remote_host, restart_cmd]
        ssh = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=60)
        restart_step = {
            "step": "ssh_restart",
            "cmd": " ".join(ssh_cmd),
            "exit_code": ssh.returncode,
            "stdout": ssh.stdout.strip()[:2000],
            "stderr": ssh.stderr.strip()[:2000],
        }
    elif deploy_sh.exists():
        local = subprocess.run(["bash", str(deploy_sh), target], capture_output=True, text=True, timeout=120)
        restart_step = {
            "step": "local_deploy_sh",
            "cmd": f"bash {deploy_sh} {target}",
            "exit_code": local.returncode,
            "stdout": local.stdout.strip()[:2000],
            "stderr": local.stderr.strip()[:2000],
        }
    elif deploy_ps1.exists():
        local = subprocess.run(["powershell", "-File", str(deploy_ps1), "-Target", target],
                               capture_output=True, text=True, timeout=120)
        restart_step = {
            "step": "local_deploy_ps1",
            "cmd": f"powershell -File {deploy_ps1} -Target {target}",
            "exit_code": local.returncode,
            "stdout": local.stdout.strip()[:2000],
            "stderr": local.stderr.strip()[:2000],
        }
    else:
        restart_step = {"step": "no_restart", "note": "no REMOTE_HOST or deploy script found"}

    steps.append(restart_step)
    all_ok = all(s.get("exit_code", 0) == 0 for s in steps if "exit_code" in s)
    return {"ok": all_ok, "cap": "cicd", "action": "deploy", "target": target,
            "remote": remote, "branch": branch, "steps": steps}


def _parse_error(stderr: str, stdout: str = "") -> dict:
    """Classify error from combined stderr+stdout output."""
    combined = (stderr + "\n" + stdout).lower()
    for pattern, category, strategy in ERROR_PATTERNS:
        m = re.search(pattern, combined, re.IGNORECASE)
        if m:
            return {"category": category, "strategy": strategy,
                    "matched": m.group(0), "missing_module": m.group(1) if m.lastindex else None}
    return {"category": "unknown", "strategy": "retry", "matched": ""}


def _attempt_fix(step: dict, error_info: dict) -> dict:
    """Attempt to auto-fix based on error classification. Returns fix result."""
    strategy = error_info["strategy"]
    fix_log = []

    if strategy == "pip_install":
        mod = error_info.get("missing_module") or ""
        if mod:
            cmd = f"{sys.executable} -m pip install {mod}"
        else:
            cmd = f"{sys.executable} -m pip install -r requirements.txt" if os.path.exists("requirements.txt") else "echo no-requirements"
        fix_log.append({"action": "pip_install", "cmd": cmd})
        try:
            r = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=60, cwd=str(SANDBOX))
            fix_log[-1]["returncode"] = r.returncode
            fix_log[-1]["output"] = r.stdout[:200]
        except Exception as e:
            fix_log[-1]["error"] = str(e)[:100]

    elif strategy == "git_checkout":
        fix_log.append({"action": "git_checkout", "note": "reverting uncommitted changes in sandbox"})
        try:
            # shell=True safe: static command string with no user input
            r = subprocess.run("git checkout -- .", shell=True, capture_output=True, text=True, timeout=30, cwd=str(SANDBOX))
            fix_log[-1]["returncode"] = r.returncode
        except Exception as e:
            fix_log[-1]["error"] = str(e)[:100]

    elif strategy == "chmod_fix":
        target = step.get("cmd", "").split()[0] if step.get("cmd") else ""
        if target and os.path.exists(target):
            cmd = f"chmod +x {target}" if sys.platform != "win32" else f"icacls {target} /grant Everyone:F"
        else:
            cmd = "echo no-target"
        fix_log.append({"action": "chmod_fix", "cmd": cmd})
        try:
            r = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=15, cwd=str(SANDBOX))
            fix_log[-1]["returncode"] = r.returncode
        except Exception as e:
            fix_log[-1]["error"] = str(e)[:100]

    elif strategy == "retry":
        fix_log.append({"action": "retry", "note": "waiting 2s then pure retry"})
        time.sleep(2)

    elif strategy == "llm_suggest":
        fix_log.append({"action": "llm_suggest", "note": "deferred to AI analysis"})

    else:
        fix_log.append({"action": "noop", "note": f"unhandled strategy: {strategy}"})

    return {"strategy": strategy, "fixes": fix_log}


def do_self_heal(params: dict) -> dict:
    """AI自愈流水线 — 失败自动诊断+修复+重试, 最多3次"""
    name = params.get("name", f"heal_{int(time.time())}")
    steps = params.get("steps", [
        {"name": "lint", "cmd": "echo lint check"},
        {"name": "test", "cmd": "echo run tests"},
    ])
    max_retries = params.get("max_retries", 3)

    heal_log = []
    results = []
    final_success = True

    heal_log.append(f"=== GBT CICD Self-Heal Pipeline: {name} ===")
    heal_log.append(f"Started: {datetime.now().isoformat()}")
    heal_log.append(f"Steps: {len(steps)}, Max retries per step: {max_retries}")

    for step in steps:
        step_name = step["name"]
        step_ok = False
        step_attempts = []

        for attempt in range(1, max_retries + 2):  # +1 initial + max_retries
            t0 = time.time()
            attempt_entry = {"attempt": attempt, "step": step_name}

            try:
                r = subprocess.run(shlex.split(step["cmd"]), capture_output=True, text=True,
                                   timeout=step.get("timeout", 120), cwd=str(SANDBOX))
                elapsed_ms = int((time.time() - t0) * 1000)
                ok = r.returncode == 0

                attempt_entry["ok"] = ok
                attempt_entry["returncode"] = r.returncode
                attempt_entry["elapsed_ms"] = elapsed_ms
                attempt_entry["stdout_tail"] = r.stdout[-300:] if r.stdout else ""
                attempt_entry["stderr_tail"] = r.stderr[-300:] if r.stderr else ""

                if ok:
                    step_ok = True
                    heal_log.append(f"  [{step_name}] attempt {attempt}: PASSED ({elapsed_ms}ms)")
                    break

                # Failure — classify and attempt fix
                error_info = _parse_error(r.stderr, r.stdout)
                attempt_entry["error_category"] = error_info["category"]
                heal_log.append(f"  [{step_name}] attempt {attempt}: FAILED — {error_info['category']}")

                if attempt <= max_retries:
                    fix = _attempt_fix(step, error_info)
                    attempt_entry["fix_applied"] = fix
                    heal_log.append(f"    → Fix: {fix['strategy']}")
                else:
                    attempt_entry["fix_applied"] = {"strategy": "exhausted", "fixes": []}
                    heal_log.append(f"    → Retries exhausted for {step_name}")

            except subprocess.TimeoutExpired:
                elapsed_ms = int((time.time() - t0) * 1000)
                attempt_entry["ok"] = False
                attempt_entry["error"] = "timeout"
                attempt_entry["elapsed_ms"] = elapsed_ms
                attempt_entry["error_category"] = "timeout"
                heal_log.append(f"  [{step_name}] attempt {attempt}: TIMEOUT ({elapsed_ms}ms)")

                if attempt <= max_retries:
                    fix = _attempt_fix(step, {"strategy": "retry", "category": "timeout"})
                    attempt_entry["fix_applied"] = fix

            except Exception as e:
                elapsed_ms = int((time.time() - t0) * 1000)
                attempt_entry["ok"] = False
                attempt_entry["error"] = str(e)[:100]
                attempt_entry["elapsed_ms"] = elapsed_ms
                attempt_entry["error_category"] = "exception"
                heal_log.append(f"  [{step_name}] attempt {attempt}: EXCEPTION — {str(e)[:80]}")

            step_attempts.append(attempt_entry)

        results.append({"step": step_name, "ok": step_ok, "attempts": step_attempts})
        if not step_ok:
            final_success = False
            break

    heal_log.append(f"\n=== Self-Heal Pipeline {'PASSED' if final_success else 'FAILED'} ===")

    return {"ok": True, "cap": "cicd", "action": "self_heal", "domain": "运维域",
            "pipeline": name, "success": final_success, "steps": results,
            "heal_log": heal_log, "max_retries": max_retries}


def do_analyze_failure(params: dict) -> dict:
    """AI故障分析 — 调用cloud_llm对错误日志生成修复建议"""
    error_log = params.get("error_log", "")
    step_name = params.get("step_name", "unknown")

    if not error_log:
        return {"ok": False, "error": "缺少error_log参数"}

    prompt = (
        f"你是DevOps故障分析专家。以下CI/CD步骤「{step_name}」执行失败，请分析根因并给出修复建议。\n\n"
        f"错误日志:\n```\n{error_log[:3000]}\n```\n\n"
        f"请返回JSON格式，包含：\n"
        f'{{"root_cause": "根因描述", "fix_suggestion": "具体修复命令或步骤", '
        f'"severity": "critical|high|medium|low", "auto_fixable": true|false}}\n'
        f"只输出JSON，不要markdown包裹。"
    )

    try:
        r = subprocess.run(
            [sys.executable, CLOUD_LLM, "ask",
             json.dumps({"prompt": prompt, "max_tokens": 1024, "temperature": 0.3}, ensure_ascii=False)],
            capture_output=True, text=True, timeout=90,
            cwd=SANDBOX, encoding="utf-8", errors="replace"
        )
        raw = (r.stdout or "").strip()
        if raw:
            try:
                llm_result = json.loads(raw)
                llm_reply = llm_result.get("reply", "") or llm_result.get("content", "") or raw
            except json.JSONDecodeError:
                llm_reply = raw[:500]

            # Try to parse structured JSON from LLM reply
            try:
                analysis = json.loads(llm_reply)
            except json.JSONDecodeError:
                m = re.search(r'\{[^{}]*"root_cause"[^{}]*\}', llm_reply, re.DOTALL)
                if m:
                    try:
                        analysis = json.loads(m.group(0))
                    except json.JSONDecodeError:
                        analysis = {"raw_analysis": llm_reply[:1000]}
                else:
                    analysis = {"raw_analysis": llm_reply[:1000]}

            return {"ok": True, "cap": "cicd", "action": "analyze_failure", "domain": "运维域",
                    "step": step_name, "analysis": analysis,
                    "llm_provider": llm_result.get("provider", "unknown") if isinstance(llm_result, dict) else "unknown"}
        else:
            return {"ok": False, "error": f"cloud_llm无输出: {r.stderr[:200]}"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "cloud_llm调用超时(90s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


DEPLOY_LOG = Path.home() / ".gbt" / "deployments"
DEPLOY_LOG.mkdir(parents=True, exist_ok=True)
DEPLOY_STATE = DEPLOY_LOG / "state.json"


def _load_deploy_state() -> dict:
    if DEPLOY_STATE.exists():
        try:
            return json.loads(DEPLOY_STATE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"history": [], "current": None}


def _save_deploy_state(state: dict):
    DEPLOY_STATE.write_text(json.dumps(state, ensure_ascii=False, default=str), encoding="utf-8")


def do_auto_deploy_loop(params: dict) -> dict:
    """Watch git repo for changes and auto-deploy on new commits."""
    import sys; sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from brain.chain_kernel import enforce_chain
    enforce_chain("cicd.auto_deploy")
    repo_path = params.get("repo_path", str(SANDBOX))
    branch = params.get("branch", "main")
    poll_seconds = int(params.get("poll_seconds", 30))
    max_iterations = int(params.get("max_iterations", 60))
    deploy_action = params.get("deploy_action", {"remote": "origin", "branch": branch, "target": "production"})

    # Ensure we have latest
    subprocess.run(["git", "fetch", "origin", branch], capture_output=True, text=True,
                    timeout=30, cwd=repo_path)

    # Get current HEAD commit before starting
    last_commit = subprocess.run(
        ["git", "rev-parse", f"origin/{branch}"], capture_output=True, text=True, timeout=10, cwd=repo_path
    ).stdout.strip()

    deploy_log = []
    deployments = 0
    last_seen = last_commit

    deploy_log.append(f"=== Auto Deploy Loop: watching {repo_path}@{branch} ===")
    deploy_log.append(f"Start commit: {last_seen[:12]}")
    deploy_log.append(f"Poll interval: {poll_seconds}s, Max iterations: {max_iterations}")

    for i in range(max_iterations):
        time.sleep(poll_seconds)
        r = subprocess.run(
            ["git", "fetch", "origin", branch], capture_output=True, text=True, timeout=30, cwd=repo_path
        )
        latest = subprocess.run(
            ["git", "rev-parse", f"origin/{branch}"], capture_output=True, text=True, timeout=10, cwd=repo_path
        ).stdout.strip()

        if latest != last_seen:
            deployments += 1
            entry = {"iteration": i + 1, "prev_commit": last_seen[:12], "new_commit": latest[:12],
                     "time": datetime.now().isoformat()}
            deploy_log.append(f"  [{i+1}] Change detected: {last_seen[:12]} -> {latest[:12]}")

            # Trigger deploy
            dep_result = do_deploy(deploy_action)
            entry["deploy_ok"] = dep_result.get("ok", False)
            entry["deploy_steps"] = dep_result.get("steps", [])
            deploy_log.append(f"  [{i+1}] Deploy: {'OK' if entry['deploy_ok'] else 'FAILED'}")
            last_seen = latest
            deploy_log.append(json.dumps(entry, ensure_ascii=False))
        else:
            if (i + 1) % 5 == 0:
                deploy_log.append(f"  [{i+1}] No changes (last: {last_seen[:12]})")

    deploy_log.append(f"=== Loop complete: {deployments} deploys over {max_iterations} iterations ===")
    return {"ok": True, "cap": "cicd", "action": "auto_deploy_loop", "domain": "运维域",
            "repo": repo_path, "branch": branch, "iterations": max_iterations,
            "deployments_triggered": deployments, "final_commit": last_seen[:12],
            "log_lines": deploy_log[-20:]}


def do_rollback(params: dict) -> dict:
    """Revert to previous deployment state on failure."""
    target = params.get("target", "production")
    steps_custom = params.get("steps", None)

    state = _load_deploy_state()
    history = state.get("history", [])

    if not history:
        return {"ok": False, "cap": "cicd", "action": "rollback", "domain": "运维域",
                "target": target, "error": "no deployment history to rollback"}

    # Pop current, revert to previous
    current = history.pop()
    previous = history[-1] if history else None

    rollback_steps = []

    if steps_custom:
        # Custom rollback steps provided
        for step in steps_custom:
            t0 = time.time()
            try:
                r = subprocess.run(shlex.split(step["cmd"]), capture_output=True, text=True,
                                   timeout=step.get("timeout", 60), cwd=str(SANDBOX))
                elapsed_ms = int((time.time() - t0) * 1000)
                rollback_steps.append({
                    "step": step.get("name", "rollback_step"),
                    "ok": r.returncode == 0,
                    "returncode": r.returncode,
                    "elapsed_ms": elapsed_ms,
                    "output": (r.stdout or r.stderr)[:500]
                })
            except Exception as e:
                rollback_steps.append({"step": step.get("name", "rollback_step"), "ok": False, "error": str(e)[:200]})
    else:
        # Default rollback: git reset to previous commit + restart
        if previous and previous.get("commit"):
            prev_commit = previous["commit"]
            t0 = time.time()
            r = subprocess.run(["git", "reset", "--hard", prev_commit], capture_output=True, text=True,
                               timeout=30, cwd=str(SANDBOX))
            elapsed_ms = int((time.time() - t0) * 1000)
            rollback_steps.append({
                "step": "git_reset", "commit": prev_commit[:12],
                "ok": r.returncode == 0, "returncode": r.returncode,
                "elapsed_ms": elapsed_ms, "output": (r.stdout or r.stderr)[:500]
            })

            # Run restart command if configured
            restart_cmd = params.get("restart_cmd", "")
            if restart_cmd:
                t0 = time.time()
                r2 = subprocess.run(shlex.split(restart_cmd), capture_output=True, text=True, timeout=60)
                elapsed_ms = int((time.time() - t0) * 1000)
                rollback_steps.append({
                    "step": "restart", "cmd": restart_cmd,
                    "ok": r2.returncode == 0, "returncode": r2.returncode,
                    "elapsed_ms": elapsed_ms
                })
        else:
            rollback_steps.append({"step": "noop", "note": "no previous commit to rollback to"})

    # Record rollback in state
    rollback_entry = {
        "action": "rollback",
        "from": current.get("commit", "unknown")[:12] if current else "unknown",
        "to": previous.get("commit", "unknown")[:12] if previous else "unknown",
        "time": datetime.now().isoformat(),
        "target": target,
    }
    history.append(rollback_entry)
    state["history"] = history
    state["current"] = previous
    _save_deploy_state(state)

    all_ok = all(s.get("ok", True) for s in rollback_steps)
    return {"ok": all_ok, "cap": "cicd", "action": "rollback", "domain": "运维域",
            "target": target, "rollback_steps": rollback_steps,
            "rolled_back_to": previous.get("commit", "unknown")[:12] if previous else None}


def do_canary_release(params: dict) -> dict:
    """Canary release: deploy to subset, monitor, then promote or rollback."""
    canary_target = params.get("canary_target", "canary")
    full_target = params.get("full_target", "production")
    health_url = params.get("health_url", "")
    monitor_seconds = int(params.get("monitor_seconds", 60))
    canary_steps = params.get("canary_steps", [
        {"name": "deploy_canary", "cmd": f"echo deploy to {canary_target}"},
    ])
    full_steps = params.get("full_steps", [
        {"name": "deploy_full", "cmd": f"echo deploy to {full_target}"},
    ])

    phases = []
    canary_ok = True

    # Phase 1: Deploy to canary
    phase1_results = []
    for step in canary_steps:
        t0 = time.time()
        try:
            r = subprocess.run(shlex.split(step["cmd"]), capture_output=True, text=True,
                               timeout=step.get("timeout", 120), cwd=str(SANDBOX))
            elapsed_ms = int((time.time() - t0) * 1000)
            ok = r.returncode == 0
            phase1_results.append({
                "step": step["name"], "ok": ok, "returncode": r.returncode,
                "elapsed_ms": elapsed_ms, "output": (r.stdout or r.stderr)[:500]
            })
            if not ok:
                canary_ok = False
                break
        except Exception as e:
            phase1_results.append({"step": step["name"], "ok": False, "error": str(e)[:200]})
            canary_ok = False
            break

    phases.append({"phase": "canary_deploy", "ok": canary_ok, "steps": phase1_results})

    if not canary_ok:
        return {"ok": False, "cap": "cicd", "action": "canary_release", "domain": "运维域",
                "canary_target": canary_target, "full_target": full_target,
                "phases": phases, "error": "canary deploy failed, rollout aborted"}

    # Phase 2: Monitor canary
    phase2 = {"phase": "monitor", "monitor_seconds": monitor_seconds, "health_checks": []}
    monitor_start = time.time()
    healthy = True

    if health_url:
        check_interval = max(5, monitor_seconds // 6)
        while time.time() - monitor_start < monitor_seconds:
            try:
                hr = subprocess.run(
                    ["curl", "-sf", "-o", "/dev/null", "-w", "%{http_code}", health_url],
                    capture_output=True, text=True, timeout=10
                )
                http_code = hr.stdout.strip()
                is_ok = hr.returncode == 0 and http_code.startswith("2")
                phase2["health_checks"].append({
                    "time": datetime.now().isoformat(),
                    "http_code": http_code,
                    "healthy": is_ok
                })
                if not is_ok:
                    healthy = False
            except Exception as e:
                phase2["health_checks"].append({
                    "time": datetime.now().isoformat(),
                    "error": str(e)[:100],
                    "healthy": False
                })
                healthy = False
            time.sleep(check_interval)
    else:
        # No health URL, just wait
        time.sleep(monitor_seconds)
        phase2["note"] = "no health_url, slept for monitor period"

    phases.append(phase2)

    if not healthy:
        # Rollback canary
        rollback_r = subprocess.run(["git", "revert", "--no-edit", "HEAD"], capture_output=True, text=True,
                                    timeout=30, cwd=str(SANDBOX))
        phases.append({"phase": "rollback_canary", "ok": rollback_r.returncode == 0,
                        "output": (rollback_r.stdout or rollback_r.stderr)[:500]})
        return {"ok": False, "cap": "cicd", "action": "canary_release", "domain": "运维域",
                "canary_target": canary_target, "full_target": full_target,
                "phases": phases, "error": "canary health check failed, rolled back"}

    # Phase 3: Promote to full
    phase3_results = []
    for step in full_steps:
        t0 = time.time()
        try:
            r = subprocess.run(shlex.split(step["cmd"]), capture_output=True, text=True,
                               timeout=step.get("timeout", 120), cwd=str(SANDBOX))
            elapsed_ms = int((time.time() - t0) * 1000)
            ok = r.returncode == 0
            phase3_results.append({
                "step": step["name"], "ok": ok, "returncode": r.returncode,
                "elapsed_ms": elapsed_ms, "output": (r.stdout or r.stderr)[:500]
            })
            if not ok:
                phases.append({"phase": "full_deploy", "ok": False, "steps": phase3_results})
                return {"ok": False, "cap": "cicd", "action": "canary_release", "domain": "运维域",
                        "canary_target": canary_target, "full_target": full_target,
                        "phases": phases, "error": "full deploy failed after canary success"}
        except Exception as e:
            phase3_results.append({"step": step["name"], "ok": False, "error": str(e)[:200]})
            phases.append({"phase": "full_deploy", "ok": False, "steps": phase3_results})
            return {"ok": False, "cap": "cicd", "action": "canary_release", "domain": "运维域",
                    "canary_target": canary_target, "full_target": full_target,
                    "phases": phases, "error": "full deploy exception after canary success"}

    phases.append({"phase": "full_deploy", "ok": True, "steps": phase3_results})

    # Record deployment for rollback tracking
    state = _load_deploy_state()
    current_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10, cwd=str(SANDBOX)
    ).stdout.strip()
    state["history"].append({
        "commit": current_commit,
        "action": "canary_release",
        "canary_target": canary_target,
        "full_target": full_target,
        "time": datetime.now().isoformat(),
    })
    state["current"] = state["history"][-1]
    _save_deploy_state(state)

    return {"ok": True, "cap": "cicd", "action": "canary_release", "domain": "运维域",
            "canary_target": canary_target, "full_target": full_target,
            "phases": phases, "monitored_seconds": monitor_seconds}


HANDLERS = {"trigger": do_trigger, "status": do_status, "deploy": do_deploy,
            "self_heal": do_self_heal, "analyze_failure": do_analyze_failure,
            "auto_deploy_loop": do_auto_deploy_loop, "rollback": do_rollback,
            "canary_release": do_canary_release}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "status"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
