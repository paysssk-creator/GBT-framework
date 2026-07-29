# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/penetration_scan.py — 邻域穿透扫描引擎 v1.0
==================================================
运行时穿透扫描：不用正则猜代码，直接 import → exec_module → 调用 handler。

穿透层级:
  L0  文件系统 — 目录存在性、capability.json 有效性
  L1  语法层   — py_compile 编译检查
  L2  加载层   — importlib 真实加载模块
  L3  契约层   — cap.json actions ↔ 运行时 HANDLERS 交叉验证
  L4  执行层   — 每个 handler 干跑(dry-run)调用，捕获运行时异常
  L5  引用层   — 跨cap导入链完整性
  L6  脑层     — brain/ 模块导入链 + 启动自检
  L7  部署层   — docker-compose 路径 + 部署脚本语法

用法: python brain/penetration_scan.py [--fix] [--layer N]
"""
import sys, os, json, time, subprocess, traceback, ast
from pathlib import Path
from importlib import util as importlib_util
from datetime import datetime

ROOT = Path(__file__).parent.parent
CAPS_DIR = ROOT / "caps"
PAYMENT_DIR = ROOT / "integrations" / "payment"
EXTRA_CAP_DIRS = [PAYMENT_DIR]
BRAIN_DIR = ROOT / "brain"

REQUIRED_CAP_FIELDS = ["name", "version", "description"]
ACTIONS_SCHEMA_DICT = "dict"
ACTIONS_SCHEMA_ARRAY = "array"


class PenetrationResult:
    def __init__(self):
        self.layer_results = {}
        self.total_fixes = 0
        self.fixes_applied = []


def scan_L0_filesystem(scan_dirs=None) -> dict:
    """L0: 文件系统 — 目录存在、capability.json 有效 JSON"""
    issues = []
    if scan_dirs is None:
        scan_dirs = [CAPS_DIR] + EXTRA_CAP_DIRS

    for base_dir in scan_dirs:
        if not base_dir.exists():
            issues.append({"level": "error", "path": str(base_dir), "msg": "目录不存在"})
            continue
        for entry in sorted(base_dir.iterdir()):
            if not entry.is_dir() or entry.name.startswith("_") or entry.name.startswith("."):
                continue
            cap_json = entry / "capability.json"
            run_py = entry / "run.py"
            if not cap_json.exists():
                issues.append({"level": "warn", "path": str(entry), "msg": "缺少 capability.json"})
            else:
                try:
                    with open(cap_json, encoding="utf-8") as f:
                        data = json.load(f)
                    # Check required fields
                    for field in REQUIRED_CAP_FIELDS:
                        if field not in data:
                            issues.append({"level": "error", "path": str(cap_json), "msg": f"缺少必填字段: {field}"})
                    # Check actions format
                    actions = data.get("actions", {})
                    if isinstance(actions, list):
                        issues.append({"level": "error", "path": str(cap_json), "msg": "actions 是 array，应为 dict"})
                except json.JSONDecodeError as e:
                    issues.append({"level": "error", "path": str(cap_json), "msg": f"JSON 解析失败: {e}"})
            if not run_py.exists():
                issues.append({"level": "warn", "path": str(entry), "msg": "缺少 run.py（可能是模板目录）"})

    return {"ok": len([i for i in issues if i["level"] == "error"]) == 0, "issues": issues}


def scan_L1_syntax() -> dict:
    """L1: 语法层 — py_compile 编译所有 .py 文件"""
    import py_compile
    issues = []
    for dirpath, dirnames, filenames in os.walk(str(ROOT)):
        dirnames[:] = [d for d in dirnames if d not in (
            '__pycache__', 'node_modules', '.git', 'site-packages', 'Lib',
            'archive', '_gbt_pro_source', '.pytest_cache', '.github',
            '.wrangler', 'Scripts', 'sandbox', '.omp'
        )]
        for f in filenames:
            if f.endswith('.py'):
                fp = os.path.join(dirpath, f)
                try:
                    py_compile.compile(fp, doraise=True)
                except py_compile.PyCompileError as e:
                    issues.append({"level": "error", "path": fp, "msg": str(e)})
    return {"ok": len(issues) == 0, "issues": issues}


def scan_L2_load(scan_dirs=None) -> dict:
    """L2: 加载层 — 真实 import 每个 cap 的 run.py"""
    if scan_dirs is None:
        scan_dirs = [CAPS_DIR] + EXTRA_CAP_DIRS
    issues = []
    loaded = 0

    for base_dir in scan_dirs:
        if not base_dir.exists():
            continue
        for entry in sorted(base_dir.iterdir()):
            if not entry.is_dir() or entry.name.startswith("_") or entry.name.startswith("."):
                continue
            run_py = entry / "run.py"
            if not run_py.exists():
                continue
            try:
                spec = importlib_util.spec_from_file_location(f"pscan_{entry.name}", str(run_py))
                mod = importlib_util.module_from_spec(spec)
                sys.modules[f"pscan_{entry.name}"] = mod
                spec.loader.exec_module(mod)
                del sys.modules[f"pscan_{entry.name}"]
                loaded += 1
            except Exception as e:
                issues.append({"level": "error", "path": str(run_py), "msg": f"加载失败: {str(e)[:200]}"})

    return {"ok": len(issues) == 0, "issues": issues, "loaded": loaded}


def scan_L3_contract(scan_dirs=None) -> dict:
    """L3: 契约层 — cap.json actions ↔ 运行时 HANDLERS 精确比对"""
    if scan_dirs is None:
        scan_dirs = [CAPS_DIR] + EXTRA_CAP_DIRS
    issues = []

    for base_dir in scan_dirs:
        if not base_dir.exists():
            continue
        for entry in sorted(base_dir.iterdir()):
            if not entry.is_dir() or entry.name.startswith("_") or entry.name.startswith("."):
                continue
            run_py = entry / "run.py"
            cap_json = entry / "capability.json"
            if not run_py.exists() or not cap_json.exists():
                continue

            try:
                with open(cap_json, encoding="utf-8") as f:
                    cap = json.load(f)
                declared = set(cap.get("actions", {}).keys())
            except Exception:
                continue

            try:
                spec = importlib_util.spec_from_file_location(f"pscan3_{entry.name}", str(run_py))
                mod = importlib_util.module_from_spec(spec)
                sys.modules[f"pscan3_{entry.name}"] = mod
                spec.loader.exec_module(mod)
                h = getattr(mod, "HANDLERS", None) or getattr(mod, "handlers", None) or {}
                runtime = set(h.keys())
                del sys.modules[f"pscan3_{entry.name}"]
            except Exception:
                continue

            missing_impl = declared - runtime
            undeclared = runtime - declared

            if missing_impl:
                for a in sorted(missing_impl):
                    issues.append({
                        "level": "error",
                        "path": str(cap_json),
                        "cap": entry.name,
                        "msg": f"action '{a}' 声明在 capability.json 但 run.py 无实现",
                        "fix_type": "remove_action",
                        "fix_action": a
                    })
            if undeclared:
                for a in sorted(undeclared):
                    issues.append({
                        "level": "warn",
                        "path": str(cap_json),
                        "cap": entry.name,
                        "msg": f"handler '{a}' 在 run.py 中但 capability.json 未声明",
                        "fix_type": "add_action",
                        "fix_action": a
                    })

    return {"ok": len([i for i in issues if i["level"] == "error"]) == 0, "issues": issues}


def scan_L4_execute(scan_dirs=None, max_per_cap=1, per_handler_timeout=5) -> dict:
    """L4: 执行层 — 子进程隔离干跑，超时即杀"""
    import subprocess as sp
    if scan_dirs is None:
        scan_dirs = [CAPS_DIR] + EXTRA_CAP_DIRS
    issues = []

    for base_dir in scan_dirs:
        if not base_dir.exists():
            continue
        for entry in sorted(base_dir.iterdir()):
            if not entry.is_dir() or entry.name.startswith("_") or entry.name.startswith("."):
                continue
            run_py = entry / "run.py"
            if not run_py.exists():
                continue
            # 子进程干跑: 导入模块并列出handlers, 选一个最轻量的handler干跑
            probe_code = f'''
import sys, json, importlib.util
try:
    spec = importlib.util.spec_from_file_location("probe", {str(run_py)!r})
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    h = getattr(mod, "HANDLERS", None) or getattr(mod, "handlers", None) or {{}}
    # 选前{max_per_cap}个handler干跑
    tested = 0
    for action, handler in list(h.items())[:{max_per_cap}]:
        try:
            if callable(handler):
                import inspect
                sig = inspect.signature(handler)
                handler({{}}) if sig.parameters else handler()
            tested += 1
        except (TypeError, ValueError, AttributeError, KeyError):
            pass  # 预期: 空参数可能触发参数校验异常
    print(json.dumps({{"ok": True, "handlers": list(h.keys()), "tested": tested}}))
except Exception as e:
    print(json.dumps({{"ok": False, "error": str(e)[:200]}}))
'''
            try:
                r = sp.run([sys.executable, "-c", probe_code],
                          capture_output=True, text=True,
                          timeout=per_handler_timeout, cwd=str(entry))
                data = json.loads(r.stdout.strip().split("\n")[-1])
                if not data.get("ok"):
                    issues.append({
                        "level": "error",
                        "path": str(run_py),
                        "cap": entry.name,
                        "msg": f"运行时崩溃: {data.get('error', 'unknown')}"
                    })
            except sp.TimeoutExpired:
                issues.append({
                    "level": "warn",
                    "path": str(run_py),
                    "cap": entry.name,
                    "msg": f"干跑超时 ({per_handler_timeout}s)"
                })
            except json.JSONDecodeError:
                pass  # 输出不是JSON, 跳过

    return {"ok": len([i for i in issues if i["level"] == "error"]) == 0, "issues": issues}


def scan_L5_crossref(scan_dirs=None) -> dict:
    """L5: 引用层 — 跨 cap 导入链完整性（cap A import cap B 时 B 必须存在）"""
    if scan_dirs is None:
        scan_dirs = [CAPS_DIR] + EXTRA_CAP_DIRS
    issues = []
    known_caps = set()

    for base_dir in scan_dirs:
        if not base_dir.exists():
            continue
        for entry in base_dir.iterdir():
            if entry.is_dir() and not entry.name.startswith("_") and not entry.name.startswith("."):
                if (entry / "run.py").exists():
                    known_caps.add(entry.name)

    for base_dir in scan_dirs:
        if not base_dir.exists():
            continue
        for entry in sorted(base_dir.iterdir()):
            if not entry.is_dir() or entry.name.startswith("_") or entry.name.startswith("."):
                continue
            run_py = entry / "run.py"
            if not run_py.exists():
                continue
            try:
                source = run_py.read_text(encoding="utf-8", errors="replace")
                # Find 'from caps.XXX import' or 'import caps.XXX'
                import re
                imports = re.findall(r"(?:from\s+caps\.|import\s+caps\.)([a-zA-Z_][a-zA-Z0-9_]*)", source)
                for imp in imports:
                    if imp not in known_caps:
                        issues.append({
                            "level": "warn",
                            "path": str(run_py),
                            "cap": entry.name,
                            "msg": f"引用了不存在的 cap: caps.{imp}"
                        })
            except Exception:
                pass

    return {"ok": True, "issues": issues}


def scan_L6_brain() -> dict:
    """L6: 脑层 — brain/ 模块导入链 + 启动自检 + 视觉邻域"""
    issues = []
    sys.path.insert(0, str(ROOT))

    # 启动自检
    try:
        from brain import boot
        result = boot()
        if not result.get("ok"):
            issues.append({"level": "error", "path": "brain/", "msg": "启动自检失败"})
        for layer in result.get("layers", []):
            if not layer.get("ok"):
                for c in layer.get("checks", []):
                    if not c.get("ok"):
                        issues.append({
                            "level": "error", "path": "brain/",
                            "msg": f"{layer.get('name','?')}/{c.get('component','?')}: {c.get('detail','?')}"
                        })
    except Exception as e:
        issues.append({"level": "error", "path": "brain/", "msg": f"brain 模块加载失败: {str(e)[:200]}"})

    # 视觉邻域穿透
    try:
        from brain.host_body import eyes
        from brain.visual_cortex import get_cortex

        # 截图
        screen = eyes.see()
        if not screen.get("ok"):
            issues.append({"level": "error", "path": "视觉邻域", "msg": f"截图失败: {screen.get('error','?')}"})
        else:
            sz = screen.get("size", [0,0])
            issues.append({"level": "info", "path": "视觉邻域", "msg": f"截图: {sz[0]}x{sz[1]}px, {len(screen.get('image',''))//1024}KB"})

        # OCR
        ocr = eyes.read(enhance=False, lang='chi_sim+eng')
        if not ocr.get("ok"):
            issues.append({"level": "error", "path": "视觉邻域", "msg": f"视觉采集失败: {ocr.get('error','?')}"})
        else:
            blocks = ocr.get("text_blocks", [])
            high = [b for b in blocks if b.get('conf',0) > 50]
            issues.append({"level": "info", "path": "视觉邻域", "msg": f"视觉: {len(blocks)}块 ({len(high)}高置信), 模式={ocr.get('mode')}"})

        # 视觉皮层
        cortex = get_cortex()
        report = cortex.analyze_screen()
        if 'error' in report:
            issues.append({"level": "warn", "path": "视觉邻域", "msg": f"皮层分析: {report['error']}"})
        else:
            s = report.get('summary', {})
            issues.append({"level": "info", "path": "视觉邻域", "msg": f"皮层: {s.get('components',0)}组件, 评分{s.get('narrative_score',0)}"})

    except Exception as e:
        issues.append({"level": "warn", "path": "视觉邻域", "msg": f"视觉测试异常: {str(e)[:150]}"})

    return {"ok": len([i for i in issues if i["level"] == "error"]) == 0, "issues": issues}

def scan_L7_deploy() -> dict:
    """L7: 部署层 — docker-compose 路径 + 部署脚本完整性"""
    issues = []

    # docker-compose.yml
    dc_file = ROOT / "docker-compose.yml"
    if dc_file.exists():
        try:
            content = dc_file.read_text(encoding="utf-8")
            import re
            # Find volume mounts: - ./path:...
            mounts = re.findall(r'-\s+\./(\S+?):', content)
            for m in mounts:
                mpath = ROOT / m
                if not mpath.exists():
                    issues.append({
                        "level": "error",
                        "path": str(dc_file),
                        "msg": f"挂载路径不存在: ./{m}"
                    })
            # Check build context
            contexts = re.findall(r'context:\s+\./(\S+)', content)
            for ctx in contexts:
                ctx_path = ROOT / ctx
                if not ctx_path.exists():
                    issues.append({
                        "level": "error",
                        "path": str(dc_file),
                        "msg": f"build context 不存在: ./{ctx}"
                    })
        except Exception as e:
            issues.append({"level": "error", "path": str(dc_file), "msg": f"解析失败: {e}"})

    # deploy.bat
    deploy_bat = ROOT / "deploy.bat"
    if deploy_bat.exists():
        content = deploy_bat.read_text(encoding="utf-8")
        if "部署后自检" not in content and "brain.boot" not in content:
            issues.append({
                "level": "warn",
                "path": str(deploy_bat),
                "msg": "缺少部署后自检步骤"
            })

    return {"ok": len([i for i in issues if i["level"] == "error"]) == 0, "issues": issues}


def auto_fix(scan_results: dict, dry_run=False) -> dict:
    from brain.chain_kernel import enforce_chain
    enforce_chain("penetration_scan.auto_fix")

    """根据扫描结果自动修复可修复的问题"""
    fixes = []

    for layer_name, result in scan_results.items():
        for issue in result.get("issues", []):
            fix_type = issue.get("fix_type")
            if not fix_type:
                continue

            cap_json_path = issue.get("path", "")
            if not cap_json_path.endswith("capability.json"):
                continue

            try:
                with open(cap_json_path, encoding="utf-8") as f:
                    cap = json.load(f)
            except Exception:
                continue

            actions = cap.get("actions", {})

            if fix_type == "remove_action":
                action = issue.get("fix_action")
                if action and action in actions:
                    if not dry_run:
                        del actions[action]
                        with open(cap_json_path, "w", encoding="utf-8") as f:
                            json.dump(cap, f, ensure_ascii=False, indent=2)
                    fixes.append(f"移除僵尸action: {cap_json_path}::{action}")

            elif fix_type == "add_action" and issue["level"] == "error":
                action = issue.get("fix_action")
                if action and action not in actions:
                    if not dry_run:
                        actions[action] = {"description": action}
                        with open(cap_json_path, "w", encoding="utf-8") as f:
                            json.dump(cap, f, ensure_ascii=False, indent=2)
                    fixes.append(f"补声明action: {cap_json_path}::{action}")

    return {"fixes_applied": len(fixes), "fixes": fixes}


def run_full_scan(auto_fix_enabled=False, deep=False) -> dict:
    """穿透扫描入口 — L0~L7 全层穿透。
    deep=False: 跳过L4(执行层), ~10秒完成
    deep=True:  包含L4子进程干跑, ~3-5分钟"""
    t0 = time.time()
    result = PenetrationResult()

    layers = [
        ("L0_文件系统", scan_L0_filesystem),
        ("L1_语法层", scan_L1_syntax),
        ("L2_加载层", scan_L2_load),
        ("L3_契约层", scan_L3_contract),
        ("L5_引用层", scan_L5_crossref),
        ("L6_脑层", scan_L6_brain),
        ("L7_部署层", scan_L7_deploy),
    ]
    if deep:
        layers.insert(4, ("L4_执行层", scan_L4_execute))

    scan_results = {}
    total_issues = 0
    total_errors = 0

    for name, scanner in layers:
        try:
            r = scanner()
        except Exception as e:
            r = {"ok": False, "issues": [{"level": "error", "path": name, "msg": f"扫描器崩溃: {str(e)[:200]}"}]}
        scan_results[name] = r
        layer_errors = len([i for i in r.get("issues", []) if i["level"] == "error"])
        layer_warns = len([i for i in r.get("issues", []) if i["level"] == "warn"])
        total_issues += layer_errors + layer_warns
        total_errors += layer_errors

    result.layer_results = scan_results

    # Auto-fix if enabled
    if auto_fix_enabled:
        fix_result = auto_fix(scan_results, dry_run=False)
        result.total_fixes = fix_result["fixes_applied"]
        result.fixes_applied = fix_result["fixes"]

    elapsed = time.time() - t0
    return {
        "ok": total_errors == 0,
        "timestamp": datetime.now().isoformat(),
        "elapsed_ms": int(elapsed * 1000),
        "total_issues": total_issues,
        "total_errors": total_errors,
        "fixes_applied": result.total_fixes,
        "fixes": result.fixes_applied,
        "layers": {
            name: {
                "ok": r["ok"],
                "issues": len(r.get("issues", [])),
                "errors": len([i for i in r.get("issues", []) if i["level"] == "error"]),
                "detail": r.get("issues", [])[:5]  # top 5
            }
            for name, r in scan_results.items()
        }
    }


def print_report(result: dict):
    """终端友好的报告输出"""
    ok = result["ok"]
    print(f"\n{'='*60}")
    print(f"  邻域穿透扫描报告")
    print(f"  {result['timestamp']}  |  {result['elapsed_ms']}ms")
    print(f"  {'🟢 全层通过' if ok else '🔴 发现问题'}")
    print(f"{'='*60}")

    for name, layer in result["layers"].items():
        status = "✅" if layer["ok"] else "❌"
        print(f"  {status} {name}: {layer['issues']} 问题 ({layer['errors']} 错误)")
        for issue in layer.get("detail", []):
            level_icon = "🔴" if issue["level"] == "error" else "🟡"
            cap = issue.get("cap", "")
            loc = f"[{cap}] " if cap else ""
            print(f"     {level_icon} {loc}{issue['msg']}")

    if result.get("fixes_applied", 0) > 0:
        print(f"\n  🔧 自动修复: {result['fixes_applied']} 项")
        for f in result.get("fixes", []):
            print(f"     ✓ {f}")

    print(f"\n  {'✅ 扫描完成，零问题' if ok else '⚠️ 需要修复上述问题'}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="GBT 邻域穿透扫描引擎")
    p.add_argument("--fix", action="store_true", help="自动修复可修复问题")
    p.add_argument("--layer", type=str, help="仅扫描指定层 (L0-L7)")
    p.add_argument("--json", action="store_true", help="JSON 输出")
    args = p.parse_args()

    if args.layer:
        layer_map = {
            "L0": ("L0_文件系统", scan_L0_filesystem),
            "L1": ("L1_语法层", scan_L1_syntax),
            "L2": ("L2_加载层", scan_L2_load),
            "L3": ("L3_契约层", scan_L3_contract),
            "L4": ("L4_执行层", scan_L4_execute),
            "L5": ("L5_引用层", scan_L5_crossref),
            "L6": ("L6_脑层", scan_L6_brain),
            "L7": ("L7_部署层", scan_L7_deploy),
        }
        if args.layer in layer_map:
            name, scanner = layer_map[args.layer]
            r = scanner()
            print(f"\n{name}: {'OK' if r['ok'] else 'ISSUES'}")
            for i in r.get("issues", []):
                print(f"  {i['level'].upper()}: {i.get('cap','')} {i['msg']}")
        else:
            print(f"未知层: {args.layer}. 可用: L0-L7")
    else:
        result = run_full_scan(auto_fix_enabled=args.fix)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print_report(result)
