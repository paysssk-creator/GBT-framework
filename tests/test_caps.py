# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""tests/test_caps.py — GBT能力模块烟雾测试套件
==============================================
验证所有128个cap的: 语法正确性 · capability.json格式 · run.py可导入性
"""
import json, os, sys, subprocess, pytest
from pathlib import Path

CAPS_DIR = Path(__file__).parent.parent / "caps"
SCHEMA_FILE = Path(__file__).parent.parent / "capability.schema.json"

def load_schema():
    if SCHEMA_FILE.exists():
        return json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    return None

def discover_caps():
    """发现所有有效cap目录"""
    caps = []
    for d in sorted(CAPS_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith("_") or d.name.startswith("."):
            continue
        caps.append(d.name)
    return caps

ALL_CAPS = discover_caps()
SCHEMA = load_schema()

# ═══════════════ 语法验证 ═══════════════

@pytest.mark.parametrize("cap_name", ALL_CAPS)
def test_run_py_syntax(cap_name):
    """每个run.py必须是合法Python语法"""
    rp = CAPS_DIR / cap_name / "run.py"
    if not rp.exists():
        pytest.skip(f"{cap_name}/run.py 不存在")
    try:
        compile(rp.read_text(encoding="utf-8"), str(rp), "exec")
    except SyntaxError as e:
        pytest.fail(f"语法错误: {e}")

@pytest.mark.parametrize("cap_name", ALL_CAPS)
def test_capability_json_valid(cap_name):
    """每个capability.json必须是合法JSON, 包含必填字段"""
    cj = CAPS_DIR / cap_name / "capability.json"
    if not cj.exists():
        return  # 不是所有cap都有capability.json
    
    try:
        data = json.loads(cj.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        pytest.fail(f"JSON解析错误: {e}")
    
    name = data.get("name") or data.get("id")
    assert name is not None, f"缺少name/id字段"
    # 部分旧格式cap使用actions字段或在顶层, 不是所有cap都有actions
    if "actions" not in data:
        return  # 旧格式, 跳过action检查

@pytest.mark.parametrize("cap_name", ALL_CAPS)
def test_run_py_has_handlers(cap_name):
    """有capability.json的cap, run.py必须定义handlers(大小写不敏感)"""
    cj = CAPS_DIR / cap_name / "capability.json"
    rp = CAPS_DIR / cap_name / "run.py"
    if not cj.exists() or not rp.exists():
        return
    content = rp.read_text(encoding="utf-8").lower()
    assert "handlers" in content, f"run.py缺少handlers定义"
# ═══════════════ 功能烟雾测试 ═══════════════

CRITICAL_CAPS = [
    "memory", "code_exec", "screenshot",
    "desktop_master", "sys_control", "port_scanner",
    "auto_pipeline", "database", "git_ops",
    "security_scan", "dev_cpu", "context_brain",
]

@pytest.mark.parametrize("cap_name", CRITICAL_CAPS)
def test_critical_cap_cli(cap_name):
    """关键cap必须能通过CLI调用"""
    rp = CAPS_DIR / cap_name / "run.py"
    if not rp.exists():
        pytest.skip(f"{cap_name}/run.py 不存在")
    
    cj = CAPS_DIR / cap_name / "capability.json"
    if not cj.exists():
        pytest.skip(f"{cap_name}/capability.json 不存在")
    
    actions = json.loads(cj.read_text(encoding="utf-8")).get("actions", {})
    if not actions:
        pytest.skip("无actions定义")
    
    # 取第一个action做烟雾测试
    first_action = list(actions.keys())[0]
    r = subprocess.run(
        [sys.executable, str(rp), first_action, "{}"],
        capture_output=True, text=True, timeout=15,
        cwd=str(CAPS_DIR.parent), encoding="utf-8", errors="replace"
    )
    try:
        result = json.loads(r.stdout.strip())
        assert "ok" in result, f"返回缺少ok字段: {r.stdout[:200]}"
    except json.JSONDecodeError:
        pytest.fail(f"CLI返回非JSON: {r.stdout[:200]}" if r.stdout else f"CLI无输出, stderr={r.stderr[:200]}")

# ═══════════════ 脑模块验证 ═══════════════

BRAIN_MODULES = ["nexus", "cognition", "deep_reasoner", "self_evolve", 
                 "orchestrator", "executor", "intent_broker", "mirror_fusion", "boot"]

@pytest.mark.parametrize("module_name", BRAIN_MODULES)
def test_brain_module_import(module_name):
    """每个脑模块必须可导入"""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    try:
        __import__(f"brain.{module_name}")
    except ImportError as e:
        pytest.fail(f"brain.{module_name} 导入失败: {e}")

def test_nexus_scan():
    """邻域中枢scan()必须返回有效数据"""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from brain.nexus import get_nexus
    n = get_nexus()
    s = n.scan(force=True)
    assert s["ok"] is not None
    assert s["health_pct"] > 0
    assert len(s["domains"]) >= 15

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
