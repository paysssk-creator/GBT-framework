"""Check if scan_all has brain domain special handling like scan() does"""
import sys
sys.path.insert(0, 'C:/Users/ADMIN/GBTxiaotudouV5')
from brain.nexus import get_nexus

hub = get_nexus()
# scan_all would look for brain modules as if they were caps/ dirs
# Let's call it and see what 多脑域 shows
result = hub.scan_all(force=True)
neighborhoods = result.get("neighborhoods", {})
mb = neighborhoods.get("🧠 多脑域", {})
if mb:
    caps = mb.get("caps", {})
    for name, info in caps.items():
        print(f"  {name}: exists={info.get('exists')}, healthy={info.get('healthy')}, issues={info.get('issues', [])}")
    print(f"  found: {mb.get('found')}/{mb.get('total')}")

sa = hub.scan(force=True)
mb2 = sa.get("domains", {}).get("🧠 多脑域", {})
if mb2:
    caps2 = mb2.get("caps", {})
    for name, info in caps2.items():
        print(f"  [scan] {name}: exists={info.get('exists')}")
    print(f"  [scan] found: {mb2.get('found')}/{mb2.get('total')}")
