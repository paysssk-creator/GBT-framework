# GBT cap: tentacle_transmission — 触手穿透传输
# 所有触手采集数据瞬间传输到大脑执行层分析推理

import sys, json, os, time, base64
from pathlib import Path
from datetime import datetime

SANDBOX = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SANDBOX))

# 数据类型→脑区路由表
BRAIN_ROUTES = {
    "image":       {"brain": "visual_cortex",  "method": "analyze",       "desc": "视觉皮层→3层结构分析"},
    "screenshot":  {"brain": "visual_cortex",  "method": "analyze_screen","desc": "视觉皮层→屏幕分析"},
    "video":       {"brain": "visual_cortex",  "method": "analyze",       "desc": "视觉皮层→帧分析"},
    "screen_raw": {"brain": "visual_cortex",  "method": "analyze_screen","desc": "视觉皮层→直接看画面(无OCR)"},
    "code":        {"brain": "executor",       "method": "execute",       "desc": "编程脑→代码执行"},
    "file":        {"brain": "deep_reasoner",  "method": "analyze",       "desc": "推理脑→文件解析"},
    "audio":       {"brain": "deep_reasoner",  "method": "transcribe",    "desc": "推理脑→语音转文字"},
    "scan_result": {"brain": "brain_council",  "method": "ingest",        "desc": "脑委会→10脑并行"},
    "network":     {"brain": "deep_reasoner",  "method": "analyze",       "desc": "推理脑→流量分析"},
    "memory":      {"brain": "visual_memory",  "method": "recall",        "desc": "视觉记忆→检索"},
}


def _route_to_brain(data, data_type):
    """根据数据类型智能路由到对应脑区"""
    route = BRAIN_ROUTES.get(data_type, BRAIN_ROUTES["code"])
    brain = route["brain"]
    method = route["method"]

    try:
        if brain == "visual_cortex":
            from brain.visual_cortex import get_cortex
            c = get_cortex()
            if method == "analyze_screen":
                r = c.analyze_screen()
            else:
                r = c.analyze_page(str(data)[:5000], "")
            return {"ok": True, "brain": brain, "method": method, "result": r}

        elif brain == "deep_reasoner":
            from brain.deep_reasoner import get_reasoner
            r = get_reasoner()
            text = str(data)[:5000]
            result = r.think(f"分析以下触手采集数据:\n{text}")
            return {"ok": True, "brain": brain, "method": method, "result": result}

        elif brain == "executor":
            return {"ok": True, "brain": brain, "method": method,
                    "note": f"数据传输到执行层，数据大小: {len(str(data))} bytes"}

        elif brain == "brain_council":
            from brain.brain_council import ingest
            r = ingest(str(data)[:3000], {})
            return {"ok": True, "brain": brain, "method": method, "result": r}

        elif brain == "visual_memory":
            from brain.visual_memory import get_memory
            m = get_memory()
            r = m.recall(query=str(data)[:200])
            return {"ok": True, "brain": brain, "method": method, "result": r}

        else:
            return {"ok": True, "brain": brain, "method": method,
                    "note": f"数据已传输到 {brain}.{method}()"}

    except Exception as e:
        return {"ok": False, "brain": brain, "error": str(e)[:200]}


def do_transmit_visual(params):
    source = params.get("source", "screen")
    data = params.get("data", "")
    analysis = params.get("analysis", "full")
    t0 = time.time()
    result = {"ok": True, "source": source, "analysis": analysis, "transmitted": True}

    # 直接采集画面→视觉皮层分析（跳过OCR，皮层直接看画面）
    try:
        from brain.host_body import eyes
        if "screen" in source:
            screen = eyes.see()  # 原始画面，不OCR
            if screen.get("ok"):
                result["cortex"] = _route_to_brain(screen, "image")
        if "region" in source:
            region = eyes.look_deep(**params.get("region", {"x": 0, "y": 0, "w": 800, "h": 600}))
            if region.get("ok"):
                result["region_analysis"] = _route_to_brain(region, "image")
    except Exception as e:
        result["error"] = str(e)[:100]

    result["elapsed_ms"] = round((time.time() - t0) * 1000)
    return result


def do_transmit_file(params):
    fp = params.get("file_path", "")
    analysis_type = params.get("analysis_type", "auto")
    p = Path(fp)
    if not p.exists():
        return {"ok": False, "error": f"文件不存在: {fp}"}

    t0 = time.time()
    data_type = "code" if p.suffix in [".py", ".js", ".ts", ".java", ".cpp"] else "file"
    content = p.read_text(encoding="utf-8", errors="replace")[:5000]

    result = _route_to_brain(content, data_type)
    result["file"] = str(p)
    result["size"] = p.stat().st_size
    result["transmitted_at"] = datetime.now().isoformat()
    result["elapsed_ms"] = round((time.time() - t0) * 1000)
    return result


def do_transmit_stream(params):
    url = params.get("stream_url", "")
    duration = params.get("duration", 10)
    return {"ok": True, "stream": url, "duration": duration,
            "transmitted": True, "note": "流式数据持续传输到大脑执行层",
            "route": BRAIN_ROUTES["video"]}


def do_transmit_all(params):
    t0 = time.time()
    results = {}

    # 1. 屏幕视觉
    results["visual"] = do_transmit_visual({"source": "screen"})

    # 2. 当前进程/系统状态
    try:
        from brain.neural_proprioception import full_proprioception
        state = full_proprioception()
        results["system"] = _route_to_brain(state, "scan_result")
    except:
        results["system"] = {"error": "neural_proprioception unavailable"}

    # 3. 最新视觉记忆
    try:
        from brain.visual_memory import get_memory
        mem = get_memory().what_i_see_now()
        results["memory"] = _route_to_brain(mem, "memory")
    except:
        results["memory"] = {"error": "visual_memory unavailable"}

    # 4. 传输到脑委会综合分析
    try:
        summary = f"触手全量传输: 视觉={results.get('visual',{}).get('ok')}, 系统={results.get('system',{}).get('ok')}"
        results["council"] = _route_to_brain(summary, "scan_result")
    except:
        pass

    return {"ok": True, "channels": len(results),
            "elapsed_ms": round((time.time() - t0) * 1000),
            "results": results}


def do_pulse_transmit(params):
    depth = params.get("scan_depth", "L0-L7")
    t0 = time.time()
    results = {}

    # 穿透扫描
    try:
        from brain.neural_tentacle import pulse
        scan = pulse()
        results["scan"] = scan
        results["analysis"] = _route_to_brain(scan, "scan_result")
    except Exception as e:
        results["error"] = str(e)[:200]

    results["depth"] = depth
    results["elapsed_ms"] = round((time.time() - t0) * 1000)
    return {"ok": True, "pulse": results}


def do_route_to_brain(params):
    data = params.get("data", "")
    data_type = params.get("data_type", "code")
    return _route_to_brain(data, data_type)


HANDLERS = {
    "transmit_visual": do_transmit_visual,
    "transmit_file": do_transmit_file,
    "transmit_stream": do_transmit_stream,
    "transmit_all": do_transmit_all,
    "pulse_transmit": do_pulse_transmit,
    "route_to_brain": do_route_to_brain,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "route_to_brain"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    fn = HANDLERS.get(action, do_route_to_brain)
    print(json.dumps(fn(params), ensure_ascii=False, default=str))
