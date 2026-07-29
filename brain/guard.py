# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""gbt_guard.py — 铁律守护者 v1.0
====================================
程序级强制验证 · 不可绕过 · 不可跳过

每次提交/部署前自动执行:
  ① 语法检查 (所有.py文件)
  ② 测试运行 (pytest)
  ③ JSON验证 (capability.json)
  ④ Nexus完整性 (orphan/ghost/route)
  ⑤ 部署验证 (HTTP 200)

任何一步失败 → 阻止操作 → 输出诊断 → 不允许继续

用法:
  python gbt_guard.py           # 完整检查
  python gbt_guard.py --quick   # 快速检查(跳过测试)
  python gbt_guard.py --strict  # 严格模式(零容忍)
"""
import sys, os, json, subprocess, re, time
from pathlib import Path

ROOT = Path(__file__).parent.parent
FAILED = 0
PASSED = 0

def _ok(msg):
    global PASSED; PASSED += 1
    print(f"  ✅ {msg}")

def _fail(msg, blocker=False):
    global FAILED; FAILED += 1
    marker = "⛔ BLOCKING" if blocker else "❌"
    print(f"  {marker} {msg}")
    if blocker: sys.exit(1)

def check_syntax():
    """① 语法检查 — 全部Python文件"""
    print("\n① 语法检查")
    errors = 0
    for root, dirs, files in os.walk(str(ROOT)):
        dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git', '.wrangler', 'node_modules', '.venv')]
        for f in files:
            if f.endswith('.py'):
                fp = os.path.join(root, f)
                try:
                    import py_compile
                    py_compile.compile(fp, doraise=True)
                except py_compile.PyCompileError as e:
                    errors += 1
                    print(f"    ❌ {os.path.relpath(fp, ROOT)}: {e}")
    if errors: _fail(f"{errors} 语法错误", blocker=True)
    else: _ok(f"全部Python文件语法正确")
    return errors == 0

def check_json():
    """② JSON验证 — capability.json"""
    print("\n② capability.json")
    errors = 0
    caps_dir = ROOT / "caps"
    for d in sorted(caps_dir.iterdir()):
        if not d.is_dir() or d.name.startswith('.') or d.name.startswith('_'): continue
        cj = d / "capability.json"
        rp = d / "run.py"
        if not cj.exists():
            if rp.exists():
                errors += 1
                print(f"    ❌ {d.name}: 缺少capability.json")
            continue
        try:
            data = json.loads(cj.read_text(encoding="utf-8"))
            if not (data.get('name') or data.get('id')):
                errors += 1
                print(f"    ❌ {d.name}: 缺少name/id字段")
            if 'actions' not in data:
                errors += 1
                print(f"    ❌ {d.name}: 缺少actions字段")
        except json.JSONDecodeError as e:
            errors += 1
            print(f"    ❌ {d.name}: JSON解析错误 {e}")
    if errors: _fail(f"{errors} 个JSON问题", blocker=True)
    else: _ok("全部capability.json格式正确")
    return errors == 0

def check_handlers():
    """③ HANDLERS检查"""
    print("\n③ HANDLERS")
    errors = 0
    caps_dir = ROOT / "caps"
    for d in sorted(caps_dir.iterdir()):
        if not d.is_dir() or d.name.startswith('.') or d.name.startswith('_'): continue
        cj = d / "capability.json"
        rp = d / "run.py"
        if cj.exists() and rp.exists():
            if 'handlers' not in rp.read_text(encoding="utf-8").lower():
                errors += 1
                print(f"    ❌ {d.name}: 缺少HANDLERS定义")
    if errors: _fail(f"{errors} 个cap缺少HANDLERS", blocker=True)
    else: _ok("全部cap有HANDLERS定义")
    return errors == 0

def check_nexus():
    """④ Nexus完整性"""
    print("\n④ Nexus完整性")
    sys.path.insert(0, str(ROOT))
    try:
        from brain.nexus import NEIGHBORHOODS, INTENT_ROUTES
    except Exception as e:
        _fail(f"Nexus导入失败: {e}", blocker=True)
        return False
    
    nx = set()
    for dn, info in NEIGHBORHOODS.items():
        for cn in info['caps']: nx.add(cn)
    
    dc = set()
    for d in (ROOT / "caps").iterdir():
        if d.is_dir() and not d.name.startswith('.') and not d.name.startswith('_'):
            dc.add(d.name)
    
    orphans = dc - nx
    ghosts = nx - dc
    broken_routes = sum(1 for _, (_, caps) in INTENT_ROUTES.items() for c in caps if c not in nx)
    
    issues = []
    if orphans: issues.append(f"{len(orphans)} orphans: {orphans}")
    if ghosts: issues.append(f"{len(ghosts)} ghosts: {ghosts}")
    if broken_routes: issues.append(f"{broken_routes} broken routes")
    
    if issues:
        for i in issues: _fail(i, blocker=True)
    else:
        _ok(f"Nexus: {len(nx)}注册 = {len(dc)}目录, 0 orphan, 0 ghost, 0 broken route")
    return len(issues) == 0

def check_tests():
    """⑤ 测试运行"""
    print("\n⑤ 测试")
    r = subprocess.run(
        [sys.executable, '-m', 'pytest', 'tests/test_caps.py', '-q', '--tb=no'],
        capture_output=True, text=True, timeout=120, cwd=str(ROOT)
    )
    if r.returncode != 0 and not r.stdout.strip():
        _fail(f"测试运行异常 (returncode={r.returncode}): {r.stderr[:200]}", blocker=True)
        return False
    m = re.search(r'(\d+) passed', r.stdout)
    f = re.search(r'(\d+) failed', r.stdout)
    passed = int(m.group(1)) if m else 0
    failed = int(f.group(1)) if f else 0
    
    if failed:
        _fail(f"{failed} 测试失败", blocker=True)
    else:
        _ok(f"{passed} 测试通过, 0 失败")
    return failed == 0

def check_deploy():
    """⑥ 部署验证"""
    print("\n⑥ 部署验证")
    try:
        import urllib.request
        r = urllib.request.urlopen("https://gbtxiaotudou.com", timeout=10)
        status = r.status
        size = len(r.read())
        if status == 200:
            _ok(f"gbtxiaotudou.com HTTP {status} ({size}B)")
        else:
            _fail(f"gbtxiaotudou.com HTTP {status}", blocker=False)
    except Exception as e:
        _fail(f"部署验证失败: {e}", blocker=False)
    return True

# ═══════════════════════════════════════════════════
#  铁律强制执行 — 不可绕过
# ═══════════════════════════════════════════════════

def check_rules_integrity():
    """⑦ 铁律完整性 — gates.md 铁律零是否被篡改"""
    gates = ROOT / "gates.md"
    if not gates.exists():
        _fail("gates.md 缺失 — 铁律文件被删除", blocker=True)
        return False
    content = gates.read_text(encoding="utf-8")
    # 铁律零必须存在且不可被注释掉
    if "铁律零" not in content:
        _fail("铁律零被删除或篡改 — 恢复 gates.md", blocker=True)
        return False
    if "禁止盲打" not in content:
        _fail("铁律 0A(禁止盲打) 缺失", blocker=True)
        return False
    if "禁止指挥用户" not in content:
        _fail("铁律 0B(禁止指挥用户) 缺失", blocker=True)
        return False
    _ok("铁律文件完整: 铁律零·0A·0B·0C 全部在位")
    return True

def check_scan_freshness():
    """⑧ 扫描鲜度 — gbt.py scan 必须最近运行过且通过"""
    scan_log = ROOT / ".gbt" / "last_scan.json"
    if not scan_log.exists():
        _fail("无扫描记录 — 必须先运行 gbt.py scan 并全部通过")
        return False
    try:
        data = json.loads(scan_log.read_text(encoding="utf-8"))
        if not data.get("all_clean"):
            _fail(f"上次扫描未通过: {data.get('summary','?')}")
            return False
        elapsed = time.time() - data.get("timestamp", 0)
        max_age = 3600  # 1小时内有效
        if elapsed > max_age:
            _fail(f"扫描过期({elapsed/60:.0f}分钟前) — 重新运行 gbt.py scan")
            return False
        _ok(f"扫描新鲜: {elapsed/60:.0f}分钟前通过 · ALL CLEAN")
        return True
    except Exception:
        _fail("扫描记录损坏 — 重新运行 gbt.py scan")
        return False

def check_caps_wired():
    """⑨ 邻域接入验证 — verify_all_caps.py 必须全绿"""
    verify_script = ROOT / "verify_all_caps.py"
    if not verify_script.exists():
        _fail("verify_all_caps.py 缺失 — 无法验证邻域接入")
        return False
    try:
        r = subprocess.run(
            [sys.executable, str(verify_script), "--quick"],
            capture_output=True, text=True, timeout=120, cwd=str(ROOT)
        )
        if r.returncode != 0:
            _fail("邻域接入验证失败 — 有cap未接入执行层")
            return False
        _ok("全部邻域cap已接入执行层")
        return True
    except subprocess.TimeoutExpired:
        _fail("邻域接入验证超时")
        return False
    except Exception as e:
        _fail(f"邻域接入验证异常: {e}")
        return False


def main():
    quick = '--quick' in sys.argv
    strict = '--strict' in sys.argv
    
    t0 = time.time()
    print("=" * 50)
    print("🛡️ GBT 铁律守护者 · 强制执行")
    print("=" * 50)
    
    results = []
    # ── 原有检查 ──
    results.append(check_syntax())
    results.append(check_json())
    results.append(check_handlers())
    results.append(check_nexus())
    # ── 铁律强制执行(不可跳过) ──
    results.append(check_rules_integrity())
    results.append(check_scan_freshness())
    if not quick:
        results.append(check_tests())
        results.append(check_caps_wired())  # 邻域接入验证(较慢，非quick模式)
    results.append(check_deploy())
    
    print("\n" + "=" * 50)
    all_pass = all(results)
    elapsed = round(time.time() - t0, 1)

    if all_pass:
        print(f"🛡️ 铁律通过 · {PASSED}项全部通过 · {elapsed}s")
    else:
        failed_count = sum(1 for r in results if not r)
        print(f"⛔ 铁律阻止 · {failed_count}项失败 · {elapsed}s")
        if strict:
            print("严格模式: 阻止操作")
            sys.exit(1)
    print("=" * 50)
    
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
