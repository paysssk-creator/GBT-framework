"""暂态审计脚本 — 分析neighborhood拓扑、caps、路由表"""
import sys, json, time
sys.path.insert(0, 'C:/Users/ADMIN/GBTxiaotudouV5')
from pathlib import Path
from brain.nexus import NEIGHBORHOODS, INTENT_ROUTES, QUANTUM_EXTENSIONS, get_nexus

ROOT = Path('C:/Users/ADMIN/GBTxiaotudouV5')
CAPS_DIR = ROOT / "caps"

# ---------------------------------------------------------------
# 1. 邻域计数 & 重复cap检测
# ---------------------------------------------------------------
print("=" * 60)
print("1. 邻域统计")
print("=" * 60)

domain_names = list(NEIGHBORHOODS.keys())
print(f"邻域总数 (含多脑域): {len(domain_names)}")
for i, d in enumerate(domain_names, 1):
    info = NEIGHBORHOODS[d]
    caps = info.get("caps", {})
    print(f"  {i:2d}. {info.get('icon','?')} {d} — {len(caps)} caps")
    if "extends_to" in info:
        print(f"      量子延申到 {len(info['extends_to'])} 个邻域")

# 重复cap检测
all_cap_refs = {}
for domain, info in NEIGHBORHOODS.items():
    for cap_name in info.get("caps", {}):
        all_cap_refs.setdefault(cap_name, []).append(domain)

dups = {k: v for k, v in all_cap_refs.items() if len(v) > 1}
print(f"\n重复cap定义 ({len(dups)} 个cap横跨多个邻域):")
for cap, domains in dups.items():
    print(f"  ⚠ {cap}: {' → '.join(domains)}")

# ---------------------------------------------------------------
# 2. Caps目录对照
# ---------------------------------------------------------------
print("\n" + "=" * 60)
print("2. Cap目录对照 — NEIGHBORHOODS定义 vs caps/ 实际目录")
print("=" * 60)

# 从NEIGHBORHOODS收集所有cap
defined_caps = set()
cap_to_domain = {}
for domain, info in NEIGHBORHOODS.items():
    for cap_name in info.get("caps", {}):
        defined_caps.add(cap_name)
        cap_to_domain[cap_name] = domain

print(f"NEIGHBORHOODS定义的总cap数 (含多脑域): {len(defined_caps)}")

# 多脑域的特殊模块
brain_modules = set()
for domain, info in NEIGHBORHOODS.items():
    if domain == "🧠 多脑域":
        brain_modules = set(info.get("caps", {}).keys())

# 扫描实际caps目录
actual_dirs = set()
missing_run_py = []
missing_cap_json = []
orphan_dirs = []

for d in sorted(CAPS_DIR.iterdir()):
    if not d.is_dir():
        continue
    name = d.name
    actual_dirs.add(name)
    rp = d / "run.py"
    cj = d / "capability.json"
    if not rp.exists():
        missing_run_py.append(name)
    if not cj.exists():
        missing_cap_json.append(name)

print(f"caps/ 实际目录总数: {len(actual_dirs)}")

# 定义但不存在
defined_only = defined_caps - actual_dirs - brain_modules  # brain modules handled separately
if defined_only:
    print(f"\n已定义但找不到目录 ({len(defined_only)}):")
    for cap in sorted(defined_only):
        domain = cap_to_domain.get(cap, "?")
        print(f"  ❌ {cap} ({domain})")

# 存在但未定义
orphan = actual_dirs - defined_caps
if orphan:
    print(f"\n存在但未定义 (orphan caps) ({len(orphan)}):")
    for cap in sorted(orphan):
        print(f"  🗑️ {cap}")

# 缺少文件
if missing_run_py:
    print(f"\n缺少run.py ({len(missing_run_py)}):")
    for cap in sorted(missing_run_py):
        print(f"  ⚠ {cap}")
if missing_cap_json:
    print(f"\n缺少capability.json ({len(missing_cap_json)}):")
    for cap in sorted(missing_cap_json):
        print(f"  ⚠ {cap}")

# ---------------------------------------------------------------
# 3. 路由表覆盖
# ---------------------------------------------------------------
print("\n" + "=" * 60)
print("3. INTENT_ROUTES 路由表分析")
print("=" * 60)

print(f"总路由条目: {len(INTENT_ROUTES)}")

# 路由表中引用的cap vs 定义
route_caps = set()
intent_cap_mapping = {}
for intent, (domain, caps) in INTENT_ROUTES.items():
    for c in caps:
        route_caps.add(c)
        intent_cap_mapping.setdefault(c, []).append(intent)

print(f"路由表中引用的不同cap: {len(route_caps)}")

# 路由引用了未定义的cap
undefined_in_routes = route_caps - defined_caps
if undefined_in_routes:
    print(f"\n路由表引用了未定义cap ({len(undefined_in_routes)}):")
    for cap in sorted(undefined_in_routes):
        print(f"  ❌ {cap} (在意图: {intent_cap_mapping[cap]})")

# 路由引用了不存在的目录cap (非多脑域)
nonexistent_route = route_caps - actual_dirs - brain_modules
if nonexistent_route:
    print(f"\n路由表引用了不存在目录的cap ({len(nonexistent_route)}):")
    for cap in sorted(nonexistent_route):
        print(f"  ⚠ {cap} (在意图: {intent_cap_mapping[cap]})")

# 路由表的domain vs 实际NEIGHBORHOODS
unknown_domains_in_routes = set()
for intent, (domain, caps) in INTENT_ROUTES.items():
    if domain not in NEIGHBORHOODS:
        unknown_domains_in_routes.add((intent, domain))
if unknown_domains_in_routes:
    print(f"\n路由表引用了未知domain ({len(unknown_domains_in_routes)}):")
    for intent, domain in sorted(unknown_domains_in_routes):
        print(f"  ⚠ {intent} → {domain}")

# ---------------------------------------------------------------
# 4. 量子延申拓扑
# ---------------------------------------------------------------
print("\n" + "=" * 60)
print("4. QUANTUM_EXTENSIONS 分析")
print("=" * 60)

print(f"量子cap总数: {len(QUANTUM_EXTENSIONS)}")
all_targets = set()
for cap, targets in QUANTUM_EXTENSIONS.items():
    all_targets.update(targets)
    print(f"  ⚛️ {cap} → {targets}")

# 量子目标在NEIGHBORHOODS存在?
for cap, targets in QUANTUM_EXTENSIONS.items():
    for t in targets:
        if t not in NEIGHBORHOODS:
            print(f"  ❌ {cap}的目标'{t}'不在NEIGHBORHOODS中")

# 量子cap定义但不存在的目录
for cap in QUANTUM_EXTENSIONS:
    # check if in NEIGHBORHOODS definitions
    in_neighborhoods = cap in defined_caps
    on_disk = cap in actual_dirs or cap in brain_modules
    if not on_disk:
        print(f"  ⚠ 量子cap '{cap}' (定义于量子邻域) 在caps/无对应目录")

# ---------------------------------------------------------------
# 5. 多脑域 vs caps/ 一致性
# ---------------------------------------------------------------
print("\n" + "=" * 60)
print("5. 🧠 多脑域一致性检查")
print("=" * 60)

brain_def = NEIGHBORHOODS.get("🧠 多脑域", {}).get("caps", {})
print(f"多脑域定义: {len(brain_def)} 个脑模块")

brain_dir_files = set()
brain_module_path = ROOT / "brain"
for f in sorted(brain_module_path.glob("*.py")):
    name = f.stem
    if not name.startswith("_"):
        brain_dir_files.add(name)

# 多脑域cap也存在于caps/目录?
for cap_name in brain_def:
    in_caps = cap_name in actual_dirs
    in_brain = cap_name in brain_dir_files
    status = "🟢" if in_brain else ("🟡 caps/目录存在" if in_caps else "❌ 找不到")
    print(f"  {cap_name}: brain={in_brain}, caps_dir={in_caps} {status}")

# 额外: caps/中也有brain模块的目录?
for cap_name in sorted(actual_dirs & brain_dir_files):
    print(f"  注: {cap_name} 同时存在于 caps/ 和 brain/ (多脑域)")

# ---------------------------------------------------------------
# 6. 汇总
# ---------------------------------------------------------------
print("\n" + "=" * 60)
print("6. 汇总")
print("=" * 60)

hub = get_nexus()
h = hub.quick_health()
print(f"Quick health: ok={h['ok']}, issues={h['core_issues']}")
print(f"Health%: {h['health_pct']}")

# Cross-reference check
xref = hub._check_cross_references()
print(f"\n交叉引用检查:")
print(f"  定义: {xref['defined']}, 实际: {xref['actual']}")
print(f"  缺失(定义但不存在): {len(xref['missing'])}")
for m in xref['missing']:
    print(f"    ❌ {m}")
print(f"  Orphan(存在但未定义): {len(xref['orphans'])}")
for o in xref['orphans']:
    print(f"    🗑️ {o}")
