# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/event_wiring.py — 事件总线全局接线
=========================================
将 GBT 所有核心事件订阅到对应的处理函数。
每个事件 topic 触发时，自动执行相应动作。

用法:
  from brain.event_wiring import wire_all
  wire_all()  # 一键订阅所有默认事件处理器
"""
import sys, os, json, logging
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

L = logging.getLogger("EventWiring")

EVENTS_ROOT = Path.home() / ".gbt" / "events"
EVENTS_ROOT.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════
#  事件处理器注册表
# ═══════════════════════════════════════════════════

_handlers = {}  # topic → [handler_fn, ...]


def on(topic: str):
    """装饰器：注册事件处理器"""
    def decorator(fn):
        _handlers.setdefault(topic, []).append(fn)
        return fn
    return decorator


def _publish_raw(topic: str, data: dict):
    """直接写事件文件（不经过 event_bus cap，避免循环依赖）"""
    topic_dir = EVENTS_ROOT / topic.replace("/", "_")
    topic_dir.mkdir(parents=True, exist_ok=True)
    event_file = topic_dir / f"{int(__import__('time').time() * 1000)}.json"
    event_file.write_text(json.dumps({
        "topic": topic, "data": data,
        "time": __import__('datetime').datetime.now().isoformat()
    }, ensure_ascii=False, default=str))


# ═══════════════════════════════════════════════════
#  默认事件处理器
# ═══════════════════════════════════════════════════

@on("heartbeat/tick")
def _on_heartbeat(data: dict):
    """心跳 tick → 记录日志"""
    L.debug(f"💓 Tick #{data.get('tick', '?')}")


@on("devourer/daily_done")
def _on_devourer_done(data: dict):
    """吞噬完成 → 触发自进化"""
    L.info("🧬 吞噬完成，触发自进化...")
    try:
        import subprocess
        subprocess.run(
            [sys.executable, str(ROOT / "caps" / "self_evolve" / "run.py"), "evolve"],
            capture_output=True, timeout=30, cwd=str(ROOT)
        )
    except Exception as e:
        L.warning(f"自进化触发失败: {e}")


@on("cap/error")
def _on_cap_error(data: dict):
    """能力模块错误 → 记录到错误日志"""
    error_log = Path.home() / ".gbt" / "errors.log"
    entry = json.dumps(data, ensure_ascii=False, default=str)
    try:
        with open(error_log, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception:
        pass


@on("task/state_change")
def _on_task_state_change(data: dict):
    """任务状态变更 → 保存会话状态"""
    try:
        from brain.session_resume import save_session
        from brain.orchestrator import get_orchestrator
        orch = get_orchestrator()
        save_session(orch)
    except Exception:
        pass


@on("session/start")
def _on_session_start(data: dict):
    """会话启动 → 恢复状态"""
    L.info("📂 会话启动，恢复状态...")
    try:
        from brain.session_resume import resume
        resume()
    except Exception as e:
        L.warning(f"会话恢复失败: {e}")


@on("session/end")
def _on_session_end(data: dict):
    """会话结束 → 保存最终状态"""
    L.info("💾 会话结束，保存状态...")
    try:
        from brain.session_resume import save_session
        from brain.orchestrator import get_orchestrator
        orch = get_orchestrator()
        save_session(orch)
    except Exception:
        pass


@on("memory/updated")
def _on_memory_updated(data: dict):
    """记忆更新 → 触发自动标签"""
    L.debug("🏷️ 记忆更新，自动标签...")


@on("health/alert")
def _on_health_alert(data: dict):
    """健康告警 → 记录并尝试自动修复"""
    L.warning(f"🚨 健康告警: {data.get('message', 'unknown')}")
    alert_log = Path.home() / ".gbt" / "alerts.log"
    entry = json.dumps(data, ensure_ascii=False, default=str)
    try:
        with open(alert_log, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception:
        pass


@on("*")
def _on_wildcard(data: dict, topic: str = ""):
    """通配符处理器 — 记录所有未匹配事件"""
    L.debug(f"📨 未处理事件: {topic}")


# ═══════════════════════════════════════════════════
#  事件分发引擎
# ═══════════════════════════════════════════════════

def dispatch(topic: str, data: dict):
    """分发事件到所有匹配的处理器（支持通配符）"""
    handlers = []
    # 精确匹配
    handlers.extend(_handlers.get(topic, []))
    # 通配符匹配：cap/*, */error 等
    for pattern, fns in _handlers.items():
        if pattern == "*":
            continue
        if pattern.endswith("/*") and topic.startswith(pattern[:-1]):
            handlers.extend(fns)
        elif pattern.startswith("*/") and topic.endswith(pattern[1:]):
            handlers.extend(fns)

    if not handlers:
        handlers = _handlers.get("*", [])

    for fn in handlers:
        try:
            fn(data)
        except Exception as e:
            L.error(f"事件处理器 {fn.__name__} 失败: {e}")


def wire_all():
    """一键接线：订阅所有默认事件处理器"""
    wired = list(_handlers.keys())
    L.info(f"🔌 事件总线接线完成: {len(wired)} 个 topic, {sum(len(v) for v in _handlers.values())} 个处理器")
    L.info(f"   Topics: {', '.join(wired)}")
    return {"ok": True, "topics": wired, "handler_count": sum(len(v) for v in _handlers.values())}


def publish(topic: str, data: dict):
    """发布事件：写入文件 + 分发处理器"""
    _publish_raw(topic, data)
    dispatch(topic, data)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
    result = wire_all()

    # 测试发布
    publish("heartbeat/tick", {"tick": 1, "test": True})
    publish("health/alert", {"message": "测试告警", "severity": "low"})
    print(json.dumps(result, ensure_ascii=False, indent=2))
