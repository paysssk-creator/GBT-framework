# 开发者：自由的风
"""entanglement_bridge/run.py — 纠缠桥接·跨邻域数据量子通道
===========================================================
量子邻域 core — 将A邻域的发现即时"纠缠"到B邻域,
一个邻域的突破瞬间触发关联邻域的响应。
"""
import sys, json, os, subprocess
from pathlib import Path

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPS_DIR = Path(SANDBOX) / "caps"

NEIGHBORHOOD_CAPS = {
    "AI推理": ["deep_reasoner","task_mind","cloud_brain"],
    "AI记忆": ["memory","self_evolve","cognition"],
    "AI编程": ["programming","code_scanner","auto_fix"],
    "感知域": ["omni_eye","screenshot","screen_ocr"],
    "侦察域": ["port_scanner","subdomain_enum","dir_buster"],
    "攻击域": ["strix","sqli_tester","anti_track"],
}

def do_bridge(params):
    source = params.get("source", "侦察域")
    target = params.get("target", "攻击域")
    finding = params.get("finding", {})

    src_caps = NEIGHBORHOOD_CAPS.get(source, [])
    tgt_caps = NEIGHBORHOOD_CAPS.get(target, [])

    bridge = {
        "source_domain": source, "target_domain": target,
        "source_finding": finding,
        "entangled": f"发现({source})已纠缠到({target})",
        "recommended_actions": [
            f"调用{target}.{cap}验证{source}的发现" for cap in tgt_caps[:3]
        ],
    }

    return {
        "ok": True, "cap": "entanglement_bridge", "action": "bridge", "domain": "量子邻域",
        "bridge": bridge,
        "note": f"量子纠缠: {source}的发现→即时关联到{target}",
    }

HANDLERS = {"bridge": do_bridge}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "bridge"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
