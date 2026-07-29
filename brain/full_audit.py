# GBT 全框架连通性激活审计
# 遍历每个 cap，检查: run.py 存在、JSON schema 有效、import 无错、handler 注册完整
import json, sys, os, importlib.util, traceback
from pathlib import Path

ROOT = Path(__file__).parent.parent
CAPS = ROOT / "caps"
RESULTS = {"total": 0, "pass": 0, "fail": 0, "broken": [], "missing_handler": []}

if not CAPS.exists():
    print(json.dumps({"error": "caps/ directory not found"}))
    sys.exit(1)

dirs = sorted([d for d in CAPS.iterdir() if d.is_dir() and not d.name.startswith(".") and not d.name.startswith("_")])

for d in dirs:
    name = d.name
    run_py = d / "run.py"
    cap_json = d / "capability.json"
    RESULTS["total"] += 1
    issues = []

    # 1. run.py 存在?
    if not run_py.exists():
        issues.append("MISSING: run.py")
        RESULTS["fail"] += 1
        RESULTS["broken"].append({"cap": name, "issues": issues})
        continue

    # 2. 语法检查 (compile)
    try:
        src = run_py.read_text(encoding="utf-8", errors="replace")
        compile(src, str(run_py), "exec")
    except SyntaxError as e:
        issues.append(f"SYNTAX: {e}")
        RESULTS["fail"] += 1
        RESULTS["broken"].append({"cap": name, "issues": issues})
        continue

    # 3. 尝试导入模块
    try:
        spec = importlib.util.spec_from_file_location(f"caps.{name}", str(run_py))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        else:
            issues.append("IMPORT: cannot create spec")
    except Exception as e:
        issues.append(f"IMPORT: {type(e).__name__}: {str(e)[:100]}")

    # 4. 检查 handler 注册
    try:
        spec = importlib.util.spec_from_file_location(f"caps.{name}", str(run_py))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        has_handler = any(
            hasattr(mod, h) and callable(getattr(mod, h))
            for h in ["do_run", "do_execute", "main", "run", "handle", "execute", "invoke"]
        )
        if not has_handler:
            issues.append("NO_HANDLER: no do_run/run/handle found")
            RESULTS["missing_handler"].append(name)
        else:
            handlers = [h for h in ["do_run", "do_execute", "main", "run", "handle", "execute", "invoke"]
                       if hasattr(mod, h) and callable(getattr(mod, h))]
            if not issues:
                RESULTS["pass"] += 1
    except Exception as e:
        issues.append(f"HANDLER_CHECK: {type(e).__name__}: {str(e)[:100]}")

    if issues:
        RESULTS["fail"] += 1
        RESULTS["broken"].append({"cap": name, "issues": issues})


# ═══════════════ brain/ 模块审计 ═══════════════
BRAIN = ROOT / "brain"
brain_results = {"total": 0, "pass": 0, "fail": 0, "broken": []}

if BRAIN.exists():
    brain_files = sorted([f for f in BRAIN.glob("*.py") if not f.name.startswith("_")])
    for bf in brain_files:
        name = bf.stem
        brain_results["total"] += 1
        try:
            src = bf.read_text(encoding="utf-8", errors="replace")
            compile(src, str(bf), "exec")
            brain_results["pass"] += 1
        except SyntaxError as e:
            brain_results["fail"] += 1
            brain_results["broken"].append({"module": name, "issue": f"SYNTAX: {e}"})
        except Exception as e:
            brain_results["fail"] += 1
            brain_results["broken"].append({"module": name, "issue": f"READ: {e}"})

RESULTS["brain"] = brain_results

# Summary
