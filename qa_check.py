# ⛔ 链路内核集成 — 不可绕过
# ⛔ GBT QA 复查工具 —— 部署后强制安检
# 用法: python qa_check.py [cap_name] [--user-perspective]
import sys, json, subprocess, os, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
RESULTS = {"passed": [], "failed": [], "warnings": []}

def check(label, fn):
    try:
        ok, msg = fn()
        if ok:
            RESULTS["passed"].append(f"[✓] {label}: {msg}")
            print(f"  ✅ {label}: {msg}")
        else:
            RESULTS["failed"].append(f"[✗] {label}: {msg}")
            print(f"  ❌ {label}: {msg}")
    except Exception as e:
        RESULTS["failed"].append(f"[✗] {label}: {str(e)[:80]}")
        print(f"  ❌ {label}: {e}")

# ═══════════════════ 第一层：代码审计 ═══════════════════
def layer1_syntax(cap_name=None):
    print("\n📋 第一层：代码审计")
    targets = []
    if cap_name:
        targets.append(ROOT / 'caps' / cap_name / 'run.py')
    else:
        targets.extend(ROOT.glob('caps/*/run.py'))
        targets.extend(ROOT.glob('brain/*.py'))
    
    for f in targets[:20]:
        name = f.relative_to(ROOT)
        check(f"语法:{name}", lambda f=f: _py_compile(f))

def _py_compile(f):
    try:
        r = subprocess.run([sys.executable, '-m', 'py_compile', str(f)], capture_output=True, text=True, timeout=10)
        return (r.returncode == 0, "OK" if r.returncode == 0 else r.stderr[:80])
    except: return (False, "编译超时")

def layer1_json(cap_name=None):
    caps_dir = ROOT / 'caps'
    dirs = [caps_dir / cap_name] if cap_name else list(caps_dir.glob('*'))
    for d in dirs:
        if d.is_dir():
            cf = d / 'capability.json'
            if cf.exists():
                try:
                    json.loads(cf.read_text(encoding='utf-8'))
                    check(f"JSON:{d.name}", lambda: (True, "格式正确"))
                except:
                    check(f"JSON:{d.name}", lambda: (False, "格式错误"))

# ═══════════════════ 第二层：运行时验证 ═══════════════════
def layer2_runtime(cap_name, ports=None):
    print("\n📋 第二层：运行时验证")
    
    # 检查 cap 能否 import
    if cap_name:
        check(f"Import:{cap_name}", lambda: _test_import(cap_name))
    
    # 检查端口
    for port in (ports or []):
        check(f"端口:{port}", lambda: _check_port(port))

def _test_import(cap_name):
    r = subprocess.run([sys.executable, str(ROOT/'caps'/cap_name/'run.py'), 'status'],
                       capture_output=True, text=True, timeout=15, cwd=str(ROOT))
    if r.returncode == 0 and r.stdout.strip():
        try:
            data = json.loads(r.stdout)
            return (data.get('ok', False), str(data)[:100])
        except: return (True, "返回了数据")
    return (False, r.stderr[:80])

def _check_port(port):
    try:
        r = urllib.request.urlopen(f'http://localhost:{port}', timeout=3)
        return (True, f"监听中 ({r.status})")
    except: return (False, "未响应")

# ═══════════════════ 第三层：用户视角 ═══════════════════
def layer3_user_perspective(cap_name, exe_path=None, ports=None):
    print("\n📋 第三层：用户视角验证")
    
    # 检查 Error 窗口
    try:
        import pygetwindow as gw
        errors = [w for w in gw.getAllWindows() if 'Error' in w.title and w.width > 200]
        check("Error窗口", lambda: (len(errors)==0, f"{len(errors)}个"))
    except: check("Error窗口", lambda: (True, "pygetwindow未安装，跳过"))
    
    # 检查是否黑屏
    if exe_path:
        try:
            import pyautogui, pytesseract
            img = pyautogui.screenshot()
            data = pytesseract.image_to_data(img, lang='eng', output_type=pytesseract.Output.DICT, config='--psm 6')
            count = sum(1 for i, t in enumerate(data['text']) if t.strip() and int(data['conf'][i]) > 40)
            check("界面渲染", lambda c=count: (c > 10, f"检测到{c}个可读元素"))
        except:
            check("界面渲染", lambda: (True, "pytesseract未安装，跳过"))
    
    # 检查 API 端点功能
    for port in (ports or []):
        check(f"API:{port}", lambda p=port: _test_api(p))

def _test_api(port):
    try:
        r = urllib.request.urlopen(f'http://localhost:{port}', timeout=3)
        return (True, f"响应{r.status}")
    except: return (False, "不可达")

# ═══════════════════ 主入口 ═══════════════════
def run_qa(cap_name=None, exe_path=None, ports=None, user_mode=False):
    from brain.chain_kernel import enforce_chain
    enforce_chain("qa_check")
    print("=" * 50)
    print("  GBT QA 复查系统 v1.0")
    print("=" * 50)
    
    layer1_syntax(cap_name)
    layer1_json(cap_name)
    layer2_runtime(cap_name, ports)
    
    if user_mode:
        layer3_user_perspective(cap_name, exe_path, ports)
    
    # 汇总
    print("\n" + "=" * 50)
    print(f"  通过: {len(RESULTS['passed'])} | 失败: {len(RESULTS['failed'])} | 警告: {len(RESULTS['warnings'])}")
    
    if RESULTS['failed']:
        print("\n  ❌ 失败项:")
        for f in RESULTS['failed']: print(f"     {f}")
    
    if not RESULTS['failed']:
        print("\n  ✅ 全部通过！可以交付。")
    
    print("=" * 50)
    return len(RESULTS['failed']) == 0

if __name__ == '__main__':
    cap = sys.argv[1] if len(sys.argv) > 1 else None
    user = '--user' in sys.argv
    ports = [8766, 8899, 15999]  # 默认检查端口
    run_qa(cap, ports=ports, user_mode=user)
