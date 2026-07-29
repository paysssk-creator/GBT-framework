"""Final check: route table cap references vs actual files"""
import sys
sys.path.insert(0, 'C:/Users/ADMIN/GBTxiaotudouV5')
from pathlib import Path
from brain.nexus import INTENT_ROUTES, NEIGHBORHOODS

ROOT = Path('C:/Users/ADMIN/GBTxiaotudouV5')
CAPS_DIR = ROOT / "caps"
BRAIN_DIR = ROOT / "brain"

# All caps on disk (caps/ + brain/*.py brain modules)
caps_on_disk = set(d.name for d in CAPS_DIR.iterdir() if d.is_dir() and not d.name.startswith('_'))
brain_files = set(f.stem for f in BRAIN_DIR.glob("*.py") if not f.stem.startswith('_'))
# brain modules include everything in brain/*.py
all_on_disk = caps_on_disk | brain_files

# All defined caps
defined_caps = set()
for domain, info in NEIGHBORHOODS.items():
    for cap_name in info.get("caps", {}):
        defined_caps.add(cap_name)

# Route cap check
route_caps = set()
for intent, (domain, caps) in INTENT_ROUTES.items():
    for c in caps:
        route_caps.add(c)
        if c not in defined_caps:
            print(f"❌ Route {intent} references '{c}' not in any NEIGHBORHOODS domain")
        if c not in all_on_disk:
            print(f"⚠️ Route {intent} references '{c}' not found on disk (caps/{c}/ or brain/{c}.py)")

print(f"Route caps: {len(route_caps)} unique")
print(f"All on disk (caps/ + brain/*.py): {len(all_on_disk)}")
print(f"Defined in NEIGHBORHOODS: {len(defined_caps)}")

# Caps on disk but not in NEIGHBORHOODS
orphan_disk = caps_on_disk - defined_caps
if orphan_disk:
    print(f"\nOn disk but NOT in NEIGHBORHOODS ({len(orphan_disk)}):")
    for c in sorted(orphan_disk):
        print(f"  {c}")
else:
    print(f"\n✅ All caps/ directories are accounted for in NEIGHBORHOODS")
