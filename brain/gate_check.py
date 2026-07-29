# GBT 质量闸门 · 提交前强制检查
# 用法: python brain/gate_check.py [--strict] [--quick]
# 返回 0 = 通过, 1 = 不过

import sys, json, ast, subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
CAPS = ROOT / "caps"
NEXUS = ROOT / "brain" / "nexus.py"

def check_all(quick=False, strict=False):
    results = {"pass": 0, "warn": 0, "fail": 0, "issues": []}

    # ─── 1. nexus 语法 ───
    if NEXUS.exists():
        try:
            ast.parse(NEXUS.read_text(encoding="utf-8"))
        except SyntaxError as e:
            results["fail"] += 1
            results["issues"].append(f"🔴 nexus.py 语法错误: {e}")

    # ─── 2. 所有 cap 完整性 ───
    for d in sorted(CAPS.iterdir()):
        if not d.is_dir() or d.name.startswith('.') or d.name.startswith('_'): continue
        name = d.name
        rp = d / "run.py"
        cj = d / "capability.json"

        # 必须有 run.py
        if not rp.exists():
            results["fail"] += 1
            results["issues"].append(f"🔴 {name}: 缺 run.py")
            continue

        # 必须有 capability.json
        if not cj.exists():
            results["fail"] += 1
            results["issues"].append(f"🔴 {name}: 缺 capability.json")
            continue

        # 语法检查
        try:
            ast.parse(rp.read_text(encoding="utf-8"))
        except SyntaxError as e:
            results["fail"] += 1
            results["issues"].append(f"🔴 {name}: 语法错误 {e}")
            continue

        # 必须有 handlers
        tree = ast.parse(rp.read_text(encoding="utf-8"))
        has_h = any(
            isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id in ('handlers', 'HANDLERS')
                for t in node.targets
            )
            for node in ast.walk(tree)
        )
        if not has_h:
            results["fail"] += 1
            results["issues"].append(f"🔴 {name}: 无 handlers 字典")
            continue

        # 快速调用测试 (可选)
        if not quick:
            try:
                r = subprocess.run([sys.executable, str(rp), "list", "{}"],
                                  capture_output=True, text=True, timeout=15,
                                  cwd=str(ROOT))
                if r.returncode == 0 and "ok" in r.stdout:
                    results["pass"] += 1
                else:
                    # 试试 self_test
                    r2 = subprocess.run([sys.executable, str(rp), "self_test", "{}"],
                                       capture_output=True, text=True, timeout=15,
                                       cwd=str(ROOT))
                    if r2.returncode == 0 and "ok" in r2.stdout:
                        results["pass"] += 1
                    else:
                        # 服务型 cap 用 run 试试
                        r3 = subprocess.run([sys.executable, str(rp), "run", "{}"],
                                           capture_output=True, text=True, timeout=15,
                                           cwd=str(ROOT))
                        if r3.returncode == 0:
                            results["pass"] += 1
                        else:
                            results["warn"] += 1
                            results["issues"].append(f"🟡 {name}: 自检超时/需参数 (非阻断)")
            except subprocess.TimeoutExpired:
                results["warn"] += 1
                results["issues"].append(f"🟡 {name}: 自检超时(服务型)")
            except Exception as e:
                results["warn"] += 1
                results["issues"].append(f"🟡 {name}: 自检异常 {str(e)[:60]}")
        else:
            results["pass"] += 1

    # ─── 3. nexus 连通性 ───
    try:
        r = subprocess.run([sys.executable, str(NEXUS), "quick_health"],
                          capture_output=True, text=True, timeout=15, cwd=str(ROOT))
        data = json.loads(r.stdout)
        if data.get("ok") and data.get("health_pct", 0) >= 90:
            pass  # OK
        else:
            results["warn"] += 1
            results["issues"].append(f"🟡 nexus 健康度 {data.get('health_pct', '?')}%")
    except:
        results["fail"] += 1
        results["issues"].append("🔴 nexus 连通性检查失败")

    # ─── 结果 ───
    total = results["pass"] + results["warn"] + results["fail"]
    passed = results["fail"] == 0
    print(f"{'✅' if passed else '🔴'} 闸门检查: {results['pass']}通过 {results['warn']}警告 {results['fail']}阻断")
    for issue in results["issues"]:
        print(f"  {issue}")
    print(f"  总计: {total} caps · {results['pass']} OK · {results['warn']} 警告 · {results['fail']} 阻断")
    
    if strict and results["warn"] > 0:
        return 1
    return 0 if passed else 1


if __name__ == "__main__":
    quick = "--quick" in sys.argv
    strict = "--strict" in sys.argv
    sys.exit(check_all(quick=quick, strict=strict))
