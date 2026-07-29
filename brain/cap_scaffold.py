# GBT cap 脚手架 — 新建能力模块并自动接入神经系统
# 用法: python brain/cap_scaffold.py <name> <domain> <description>
import sys, json, os
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
CAPS = ROOT / "caps"
NEXUS_PY = ROOT / "brain" / "nexus.py"

DOMAINS = {
    "AI推理": "🧠", "AI记忆": "💾", "AI知识": "📚", "AI编程": "💻",
    "AI创作": "🎨", "AI协作": "🤝", "感知域": "🖐️", "攻击域": "⚔️",
    "侦察域": "🔍", "桌面域": "🖥️", "运维域": "🔧", "信息域": "📡",
    "媒体域": "🎬", "安全域": "🛡️", "特殊域": "📦", "金融域": "📈",
    "设备感知层": "🫀", "量子邻域": "⚛️",
}

def scaffold(name: str, domain: str, desc: str, risk: str = "safe", status: str = "ready"):
    from brain.chain_kernel import enforce_chain
    enforce_chain("cap_scaffold.scaffold", mirror_target=str(NEXUS_PY))

    if domain not in DOMAINS:
        print(f"❌ 未知领域: {domain}")
        print(f"   可用: {', '.join(DOMAINS.keys())}")
        return False

    cap_dir = CAPS / name
    if cap_dir.exists():
        print(f"❌ cap 已存在: {cap_dir}")
        return False

    # 1. 创建目录
    cap_dir.mkdir(parents=True)

    # 2. capability.json
    cap_json = {
        "name": name,
        "version": "1.0.0",
        "description": desc,
        "language": "python",
        "risk_level": risk,
        "auto_exec": risk == "safe",
        "category": domain,
        "tier": status,
        "actions": {
            "run": {"description": f"执行 {desc}"}
        }
    }
    (cap_dir / "capability.json").write_text(
        json.dumps(cap_json, ensure_ascii=False, indent=2), encoding="utf-8")

    # 3. run.py (含 handlers)
    run_py = f'''# GBT cap: {name} — {desc}
import sys, json
from pathlib import Path

CAP_DIR = Path(__file__).parent

def do_run(params: dict) -> dict:
    """默认执行入口"""
    return {{
        "ok": True,
        "cap": "{name}",
        "domain": "{domain}",
        "params": params,
        "message": "{desc} — 就绪"
    }}

handlers = {{
    "run": do_run,
}}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "run"
    raw = sys.argv[2] if len(sys.argv) > 2 else "{{}}"
    try:
        params = json.loads(raw)
    except Exception:
        params = {{"raw": raw}}
    h = handlers.get(action, lambda p: {{"ok": False, "error": f"未知:{{action}}"}})
    print(json.dumps(h(params), ensure_ascii=False, indent=2))
'''
    (cap_dir / "run.py").write_text(run_py, encoding="utf-8")

    # 4. 自动注册到 nexus.py
    if NEXUS_PY.exists():
        nexus_src = NEXUS_PY.read_text(encoding="utf-8")
        icon = DOMAINS.get(domain, "📦")
        
        # 找到对应领域在 NEIGHBORHOODS 中的位置
        domain_key = f'"{domain}":'
        if domain_key in nexus_src:
            # 在领域的 caps 字典末尾插入新条目
            cap_entry = f'\n            "{name}": ("{desc}", "{risk}", "{status}"),'
            
            # 找到领域块的 caps 结束位置 (最后一个 "xxx" 条目后的换行)
            domain_start = nexus_src.index(domain_key)
            # 找到下一个领域或结束
            next_domain_idx = len(nexus_src)
            for d in DOMAINS:
                if d != domain:
                    idx = nexus_src.find(f'"{d}":', domain_start + len(domain_key))
                    if idx != -1 and idx < next_domain_idx:
                        next_domain_idx = idx
            
            domain_block = nexus_src[domain_start:next_domain_idx]
            # 在最后一个 cap 条目后插入
            last_cap_end = domain_block.rfind('",')
            if last_cap_end == -1:
                last_cap_end = domain_block.rfind('")')
            
            if last_cap_end != -1:
                insert_pos = domain_start + last_cap_end + 2
                new_nexus = nexus_src[:insert_pos] + cap_entry + nexus_src[insert_pos:]
                NEXUS_PY.write_text(new_nexus, encoding="utf-8")
                print(f"  ✅ 已注册到 nexus.py → {domain}")
            else:
                print(f"  ⚠️ nexus 注入位置未找到，需手动注册")
        else:
            print(f"  ⚠️ 领域 {domain} 在 nexus 中未找到")

    # 5. 验证
    import subprocess
    r = subprocess.run(
        [sys.executable, str(cap_dir / "run.py"), "run", "{}"],
        capture_output=True, text=True, timeout=10, cwd=str(ROOT)
    )
    if r.returncode == 0:
        try:
            result = json.loads(r.stdout.strip().split('\n')[-1])
            if result.get("ok"):
                print(f"✅ cap [{name}] 创建成功 + 验证通过")
                print(f"   领域: {domain} {icon}")
                print(f"   路径: {cap_dir}")
                print(f"   调用: python caps/{name}/run.py run '{{}}'")
                return True
        except:
            pass
    print(f"⚠️ cap 已创建但验证失败: {r.stderr[:100] if r.stderr else r.stdout[:100]}")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法: python brain/cap_scaffold.py <name> <domain> <description> [risk] [status]")
        print(f"领域: {', '.join(DOMAINS.keys())}")
        sys.exit(1)
    
    name = sys.argv[1]
    domain = sys.argv[2]
    desc = sys.argv[3]
    risk = sys.argv[4] if len(sys.argv) > 4 else "safe"
    status = sys.argv[5] if len(sys.argv) > 5 else "ready"
    
    ok = scaffold(name, domain, desc, risk, status)
    sys.exit(0 if ok else 1)
