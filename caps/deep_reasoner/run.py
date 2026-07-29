# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""deep_reasoner/run.py — 深度推理引擎 v2
===========================================
委托 brain.deep_reasoner，提供 CLI 入口。
cloud 模式调用云端 LLM，默认本地规则推理。
"""
import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

MODES = {
    "chain": "链式推理", "tree": "树形推理", "compare": "对比推理",
    "hypothesis": "假设推理", "reverse": "逆向推理", "system": "系统推理",
    "decision": "决策推理", "creative": "创意推理",
}

def do_reason(params):
    topic = params.get("topic", params.get("prompt", ""))
    mode = params.get("mode", "chain")
    engine = params.get("engine", "local")
    if not topic:
        return {"ok": False, "error": "缺少 topic"}

    mode_desc = MODES.get(mode, mode)

    if engine == "cloud":
        try:
            from brain.deep_reasoner import get_reasoner
            reasoner = get_reasoner()
            result = reasoner.reason(topic, mode)
            return {"ok": True, "topic": topic, "mode": mode,
                    "reasoning": result.get("direction", ""),
                    "rationale": result.get("rationale", ""),
                    "engine": "cloud"}
        except Exception as e:
            return {"ok": False, "error": str(e)[:200], "engine": "cloud"}

    return {"ok": True, "topic": topic, "mode": mode, "mode_desc": mode_desc,
            "reasoning": f"[本地降级模式·非LLM推理]\n【{mode_desc}推理】\n问题: {topic}\n\n1. 前提分析\n2. 推理推导\n3. 结论\n4. 建议",
            "engine": "local"}

HANDLERS = {"reason": do_reason}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "reason"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知: {action}"})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
