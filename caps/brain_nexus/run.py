# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
caps/brain_nexus/run.py — 邻域中枢 CLI入口
============================================
委托到 brain.nexus (集中式神经系统)。
"""
import sys, json, os

# 确保brain/在path中
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent.parent))

from brain.nexus import get_nexus, scan, route, topology, diagnose, quick_health

nexus = get_nexus()

def do_map(p):    return {"ok": True, "action": "map", **topology()}
def do_route(p):  return {"ok": True, "action": "route", **route(p.get("intent",""), p.get("query",""))}
def do_audit(p):  return {"ok": True, "action": "audit", **diagnose()}
def do_boot(p):   return {"ok": True, "action": "boot", **scan(force=True)}
def do_bridge(p): return nexus.bridge(p.get("from",""), p.get("to",""), p.get("data",{}))
def do_neighborhoods(p): return {"ok": True, "action": "neighborhoods", "topology": nexus.topology_text(), "summary": topology()}

HANDLERS = {
    "map": do_map, "route": do_route, "audit": do_audit,
    "boot": do_boot, "bridge": do_bridge, "neighborhoods": do_neighborhoods,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "map"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except json.JSONDecodeError: params = {"query": sys.argv[2]}
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知: {action}"}
    print(json.dumps(result, ensure_ascii=False, default=str, indent=2))
