# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""cognition/run.py — 委托到 brain.cognition"""
import sys,json,os
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..",".."))
from brain.cognition import get_cognition
from pathlib import Path
from datetime import datetime, timezone
c = get_cognition()
CAPS_DIR = Path(__file__).parent.parent
INNOVATION_LOG = Path.home() / ".gbt" / "memory" / "innovation_log.json"

def do_self_audit(params):
    """Scan all caps for stale/duplicate/broken modules."""
    duplicates = []
    broken = []
    unused = []
    seen_handlers = {}
    all_caps = []

    for cap_dir in sorted(CAPS_DIR.iterdir()):
        if not cap_dir.is_dir() or cap_dir.name.startswith("."):
            continue
        rp = cap_dir / "run.py"
        if not rp.exists():
            broken.append({"cap": cap_dir.name, "reason": "missing run.py"})
            continue
        all_caps.append(cap_dir.name)
        try:
            src = rp.read_text(encoding="utf-8")
        except Exception as e:
            broken.append({"cap": cap_dir.name, "reason": f"read error: {e}"})
            continue
        # Syntax check
        try:
            compile(src, str(rp), "exec")
        except SyntaxError as e:
            broken.append({"cap": cap_dir.name, "reason": f"syntax error: {e}"})

        # Extract HANDLERS keys
        import re
        handler_match = re.search(r'HANDLERS\s*=\s*\{(.*?)\}', src, re.DOTALL)
        if handler_match:
            body = handler_match.group(1)
            keys = re.findall(r'"([^"]+)"', body)
            if not keys:
                unused.append({"cap": cap_dir.name, "reason": "HANDLERS dict empty"})
            for k in keys:
                if k in seen_handlers:
                    duplicates.append({
                        "handler": k,
                        "caps": [seen_handlers[k], cap_dir.name]
                    })
                else:
                    seen_handlers[k] = cap_dir.name
        else:
            # Check for alternative entry patterns (caps protocol)
            if "if __name__" not in src and "def " not in src:
                unused.append({"cap": cap_dir.name, "reason": "no HANDLERS and no clear entry point"})

    recommendations = []
    if duplicates:
        recommendations.append(f"⚠️ {len(duplicates)} duplicate handler(s) found across caps — consider namespacing")
    if broken:
        recommendations.append(f"🔴 {len(broken)} broken cap(s) — fix syntax or missing files")
    if unused:
        recommendations.append(f"🟡 {len(unused)} cap(s) appear unused — review for cleanup")
    if not duplicates and not broken and not unused:
        recommendations.append("✅ All {0} caps healthy".format(len(all_caps)))

    return {
        "ok": True,
        "total_caps": len(all_caps),
        "duplicates": duplicates,
        "broken": broken,
        "unused": unused,
        "recommendations": recommendations,
    }

def do_innovation_log(params):
    """Record a new capability discovery with timestamp and source."""
    topic = (params or {}).get("topic", "")
    description = (params or {}).get("description", "")
    source = (params or {}).get("source", "manual")
    evidence = (params or {}).get("evidence", "")
    tags = (params or {}).get("tags", [])

    if not topic:
        return {"ok": False, "error": "topic is required"}

    entry = {
        "topic": topic,
        "description": description,
        "source": source,
        "evidence": evidence,
        "tags": tags,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ts_epoch": datetime.now(timezone.utc).timestamp(),
    }

    # Persist to innovation log
    entries = []
    if INNOVATION_LOG.exists():
        try:
            entries = json.loads(INNOVATION_LOG.read_text(encoding="utf-8"))
        except Exception:
            entries = []
    entries.append(entry)
    INNOVATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    INNOVATION_LOG.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")

    # Also record via cognition engine
    c.record_discovery(topic, description, source, evidence, tags)

    return {
        "ok": True,
        "entry": entry,
        "total_innovations": len(entries),
        "log_file": str(INNOVATION_LOG),
    }

HANDLERS = {
  "whoami": lambda p: c.who_am_i(),
  "stats": lambda p: c.stats(),
  "discover": lambda p: c.record_discovery(p.get("topic",""),p.get("description",""),p.get("source",""),p.get("evidence",""),p.get("tags",[])),
  "self_audit": do_self_audit,
  "innovation_log": do_innovation_log,
}
if __name__ == "__main__":
  a = sys.argv[1] if len(sys.argv)>1 else "whoami"
  p = json.loads(sys.argv[2]) if len(sys.argv)>2 else {}
  r = HANDLERS.get(a, lambda x: {"error":"unknown action","available":list(HANDLERS.keys())})(p)
  print(json.dumps(r, ensure_ascii=False, default=str))
