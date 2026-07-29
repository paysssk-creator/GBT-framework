# 开发者：自由的风
"""event_bus/run.py — 事件总线·文件背板pub/sub
===============================================
基础设施 — 基于 ~/.gbt/events/ 目录的文件背板事件系统。
每个topic一个目录，事件以JSON文件存储，订阅规则以subs.json管理。
"""
import sys, json, os, time, uuid
from pathlib import Path
from datetime import datetime

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVENTS_ROOT = Path.home() / ".gbt" / "events"
SUBS_FILE = EVENTS_ROOT / "_subscriptions.json"


def _ensure_dirs():
    EVENTS_ROOT.mkdir(parents=True, exist_ok=True)


def _load_subs():
    _ensure_dirs()
    if not SUBS_FILE.exists():
        return {}
    try:
        return json.loads(SUBS_FILE.read_text())
    except:
        return {}


def _save_subs(subs):
    _ensure_dirs()
    SUBS_FILE.write_text(json.dumps(subs, indent=2, default=str))


def _sanitize_topic(topic):
    """清洗topic名 — 仅保留字母数字下划线连字符"""
    import re
    return re.sub(r"[^\w\-]", "_", topic.strip().lower())[:64]


def do_publish(params):
    """发布事件到topic — 事件写入文件，匹配订阅规则"""
    topic = _sanitize_topic(params.get("topic", ""))
    if not topic:
        return {"ok": False, "error": "缺少 topic 参数"}
    event_type = params.get("type", params.get("event_type", "default"))
    payload = params.get("payload", params.get("data", {}))
    event_id = uuid.uuid4().hex[:12]
    ts = datetime.now().isoformat()

    _ensure_dirs()
    topic_dir = EVENTS_ROOT / topic
    topic_dir.mkdir(parents=True, exist_ok=True)

    event = {
        "id": event_id,
        "topic": topic,
        "type": event_type,
        "timestamp": ts,
        "payload": payload
    }
    event_file = topic_dir / f"{int(time.time() * 1_000_000)}_{event_id}.json"
    event_file.write_text(json.dumps(event, indent=2, default=str))

    # 检查订阅规则匹配
    subs = _load_subs()
    matched = []
    for sub_id, rule in subs.items():
        if rule.get("topic") != topic:
            continue
        if rule.get("event_type") and rule["event_type"] != event_type:
            continue
        matched.append({"subscriber_id": sub_id, "handler": rule.get("handler", ""),
                       "caps": rule.get("caps", [])})

    return {"ok": True, "event_id": event_id, "topic": topic, "type": event_type,
            "matched_subscribers": len(matched), "subscribers": matched}


def do_subscribe(params):
    """订阅topic — 注册一个处理规则"""
    topic = _sanitize_topic(params.get("topic", ""))
    if not topic:
        return {"ok": False, "error": "缺少 topic 参数"}
    handler = (params.get("handler") or "").strip()
    event_type = params.get("event_type", params.get("type", ""))
    caps = params.get("caps", params.get("actions", []))

    subs = _load_subs()
    sub_id = f"sub_{uuid.uuid4().hex[:8]}"
    subs[sub_id] = {
        "topic": topic,
        "handler": handler,
        "event_type": event_type or None,
        "caps": caps if isinstance(caps, list) else [caps],
        "created_at": datetime.now().isoformat()
    }
    _save_subs(subs)

    _ensure_dirs()
    (EVENTS_ROOT / topic).mkdir(parents=True, exist_ok=True)

    return {"ok": True, "subscriber_id": sub_id, "topic": topic, "handler": handler}


def do_unsubscribe(params):
    """取消订阅"""
    sub_id = (params.get("subscriber_id") or params.get("id") or "").strip()
    if not sub_id:
        return {"ok": False, "error": "缺少 subscriber_id 参数"}
    subs = _load_subs()
    if sub_id not in subs:
        return {"ok": False, "error": f"订阅不存在: {sub_id}"}
    removed = subs.pop(sub_id)
    _save_subs(subs)
    return {"ok": True, "removed": {"subscriber_id": sub_id, "topic": removed["topic"],
                                     "handler": removed["handler"]}}


def do_list_topics(params):
    """列出所有topic及订阅者"""
    _ensure_dirs()
    topics = {}
    for d in sorted(EVENTS_ROOT.iterdir()):
        if not d.is_dir():
            continue
        if d.name.startswith("_"):
            continue
        event_files = sorted(d.glob("*.json"))
        latest = None
        if event_files:
            try:
                latest_data = json.loads(event_files[-1].read_text())
                latest = {"id": latest_data.get("id"), "type": latest_data.get("type"),
                          "timestamp": latest_data.get("timestamp")}
            except:
                latest = None
        topics[d.name] = {"event_count": len(event_files), "latest": latest}

    subs = _load_subs()
    subscribers_by_topic = {}
    for sub_id, rule in subs.items():
        t = rule["topic"]
        if t not in subscribers_by_topic:
            subscribers_by_topic[t] = []
        subscribers_by_topic[t].append({
            "subscriber_id": sub_id, "handler": rule["handler"],
            "event_type": rule.get("event_type")
        })

    return {"ok": True, "topics": topics, "subscribers": subscribers_by_topic,
            "total_topics": len(topics), "total_subscribers": len(subs)}


HANDLERS = {"publish": do_publish, "subscribe": do_subscribe,
            "unsubscribe": do_unsubscribe, "list_topics": do_list_topics}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "list_topics"
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except:
            params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知动作: {action}",
                                          "available": list(HANDLERS.keys())})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
