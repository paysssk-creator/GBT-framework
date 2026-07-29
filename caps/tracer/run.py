# 开发者：自由的风
"""tracer/run.py — 分布式追踪·span级执行追踪
============================================
基础设施 — 记录cap调用链，构建调用树，统计耗时。
追踪数据存储在 ~/.gbt/traces/ 下，按trace_id分文件。
"""
import sys, json, os, time, uuid
from pathlib import Path
from datetime import datetime, timezone

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACES_DIR = Path.home() / ".gbt" / "traces"
TRACES_DIR.mkdir(parents=True, exist_ok=True)


def _span_path(trace_id):
    return TRACES_DIR / f"{trace_id}.json"


def _load_trace(trace_id):
    sp = _span_path(trace_id)
    if not sp.exists():
        return None
    try:
        return json.loads(sp.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_trace(trace_id, data):
    sp = _span_path(trace_id)
    sp.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str),
                   encoding="utf-8")


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def do_start_trace(params):
    """开启一个追踪span。
    params: name(str), parent_trace_id(str/None), cap(str), action(str), input_summary(str)
    返回: trace_id, span_id, started_at
    """
    name = params.get("name", "unnamed")
    parent_trace_id = params.get("parent_trace_id")
    cap = params.get("cap", "")
    action = params.get("action", "")
    input_summary = params.get("input_summary", "")

    trace_id = str(uuid.uuid4())[:12]
    span_id = str(uuid.uuid4())[:8]
    now = _now_iso()

    trace = {
        "trace_id": trace_id,
        "root_span_id": span_id if not parent_trace_id else None,
        "spans": {},
        "started_at": now,
        "updated_at": now,
    }

    if parent_trace_id:
        parent = _load_trace(parent_trace_id)
        if parent:
            trace = parent
            trace_id = parent_trace_id
            trace["updated_at"] = now

    span = {
        "span_id": span_id,
        "name": name,
        "parent_span_id": parent_trace_id and trace.get("spans", {}).get(
            params.get("parent_span_id", ""), {}).get("span_id"),
        "cap": cap,
        "action": action,
        "input_summary": input_summary[:200],
        "started_at": now,
        "ended_at": None,
        "duration_ms": None,
        "status": "running",
        "children": [],
    }

    # link to parent
    parent_span_id = params.get("parent_span_id")
    if parent_span_id:
        parent_span = trace["spans"].get(parent_span_id)
        if parent_span:
            parent_span.setdefault("children", []).append(span_id)
            span["parent_span_id"] = parent_span_id

    trace["spans"][span_id] = span
    _save_trace(trace_id, trace)

    return {
        "ok": True,
        "trace_id": trace_id,
        "span_id": span_id,
        "started_at": now,
    }


def do_end_trace(params):
    """结束一个追踪span。
    params: trace_id(str), span_id(str), error(str/None), output_summary(str/None)
    返回: span耗时，trace状态
    """
    trace_id = params.get("trace_id", "")
    span_id = params.get("span_id", "")
    error = params.get("error")
    output_summary = params.get("output_summary", "")

    trace = _load_trace(trace_id)
    if not trace:
        return {"ok": False, "error": f"trace {trace_id} 不存在"}

    span = trace["spans"].get(span_id)
    if not span:
        return {"ok": False, "error": f"span {span_id} 不存在"}

    now = _now_iso()
    started = datetime.fromisoformat(span["started_at"])
    duration_ms = (datetime.now(timezone.utc) - started).total_seconds() * 1000

    span["ended_at"] = now
    span["duration_ms"] = round(duration_ms, 2)
    span["status"] = "error" if error else "ok"
    span["error"] = error[:200] if error else None
    span["output_summary"] = output_summary[:200] if output_summary else None

    trace["updated_at"] = now
    _save_trace(trace_id, trace)

    return {
        "ok": True,
        "trace_id": trace_id,
        "span_id": span_id,
        "duration_ms": round(duration_ms, 2),
        "status": span["status"],
    }


def do_get_trace(params):
    """获取完整追踪树。
    params: trace_id(str), flat(bool/默认False展平)
    返回: 树形或扁平span列表
    """
    trace_id = params.get("trace_id", "")
    flat = params.get("flat", False)

    trace = _load_trace(trace_id)
    if not trace:
        return {"ok": False, "error": f"trace {trace_id} 不存在"}

    if flat:
        return {"ok": True, "trace_id": trace_id,
                "spans": list(trace["spans"].values()),
                "total_spans": len(trace["spans"])}

    def _build_tree(span_id):
        span = trace["spans"].get(span_id)
        if not span:
            return None
        node = dict(span)
        node["children"] = [_build_tree(c) for c in span.get("children", [])]
        node["children"] = [c for c in node["children"] if c is not None]
        return node

    root_span_id = trace.get("root_span_id") or next(
        (sid for sid, s in trace["spans"].items() if not s.get("parent_span_id")),
        list(trace["spans"].keys())[0] if trace["spans"] else None)

    if not root_span_id:
        return {"ok": True, "trace_id": trace_id, "tree": None, "total_spans": 0}

    tree = _build_tree(root_span_id)
    return {
        "ok": True,
        "trace_id": trace_id,
        "tree": tree,
        "total_spans": len(trace["spans"]),
        "started_at": trace.get("started_at"),
        "updated_at": trace.get("updated_at"),
    }


HANDLERS = {
    "start_trace": do_start_trace,
    "end_trace": do_end_trace,
    "get_trace": do_get_trace,
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "用法: run.py <action> [json]",
                          "actions": list(HANDLERS.keys())}, ensure_ascii=False))
        sys.exit(1)
    action = sys.argv[1]
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    h = HANDLERS.get(action)
    print(json.dumps(h(params) if h else
          {"ok": False, "error": f"未知: {action}",
           "available": list(HANDLERS.keys())}, ensure_ascii=False, default=str))
