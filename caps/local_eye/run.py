# 开发者：自由的风
"""local_eye/run.py — 本地视觉感知引擎，无需远端模型
==================================================
感知域 ready — 结合截图+UIA+OCR，提供本地综合分析。
不依赖任何外部API或视觉模型。
"""
import sys, json, os, subprocess

def _native_scan():
    try:
        import sys; sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from brain.host_body import eyes
        result = eyes.read_all()
        return result.get('results', result.get('text_blocks', []))
    except: return []

def _native_ocr():
    try:
        import sys; sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from brain.host_body import eyes
        result = eyes.read_all()
        return result.get('text_blocks', result.get('results', []))
    except: return []

def _native_screenshot():
    try:
        import sys; sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from brain.host_body import eyes
        result = eyes.see()
        return result.get('image', '')
    except: return ''

from pathlib import Path

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPS_DIR = Path(SANDBOX)


def _call_cap(cap_id, action, params, timeout=15):
    """调用同级cap"""
    run_py = CAPS_DIR / cap_id / "run.py"
    if not run_py.exists():
        return {"ok": False, "error": f"cap {cap_id} 不存在"}

    try:
        r = subprocess.run(
            [sys.executable, str(run_py), action, json.dumps(params, ensure_ascii=False)],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(SANDBOX), encoding="utf-8", errors="replace"
        )
        return json.loads((r.stdout or "{}").strip())
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"{cap_id}.{action} 超时"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}


def do_scan(params):
    """综合扫描 — 同时获取UIA + OCR + 截图预览"""
    results = {}

    # ① UIA遍历
    uia_result = _call_cap("omni_eye", "see", {"depth": 2, "max_windows": 20})
    if uia_result.get("ok"):
        results["uia"] = {
            "windows": uia_result.get("visible_windows", 0),
            "top_windows": [
                {"name": w.get("name", "")[:60], "type": w.get("type", ""),
                 "rect": w.get("rect", {})}
                for w in uia_result.get("windows", [])[:10]
            ]
        }
    else:
        results["uia"] = {"error": uia_result.get("error", "unknown")}

    # ② OCR扫描
    ocr_result = _call_cap("screen_ocr", "read_all", {"lang": "chi_sim+eng", "psm": 3})
    if ocr_result.get("ok"):
        text_sample = ocr_result.get("text", "")[:500]
        results["ocr"] = {
            "line_count": ocr_result.get("line_count", 0),
            "block_count": ocr_result.get("block_count", 0),
            "text_sample": text_sample,
        }
    else:
        results["ocr"] = {"error": ocr_result.get("error", "unknown")}

    # ③ 截图快照
    ss_result = _call_cap("screenshot", "capture", {"monitor": 1, "quality": 30})
    if ss_result.get("ok"):
        results["screenshot"] = {
            "resolution": f"{ss_result.get('width', '?')}x{ss_result.get('height', '?')}",
            "size_kb": round(ss_result.get("size_bytes", 0) / 1024, 1),
        }
    else:
        results["screenshot"] = {"error": ss_result.get("error", "unknown")}

    overall_ok = any(v.get("windows") or v.get("line_count") or v.get("resolution") for v in results.values())

    return {
        "ok": overall_ok,
        "cap": "local_eye",
        "action": "scan",
        "domain": "感知域",
        "results": results,
    }


def do_diff(params):
    """对比两次扫描的变化"""
    interval = params.get("interval", 1.0)
    import time

    before = do_scan({})
    time.sleep(interval)
    after = do_scan({})

    changes = []
    if before.get("ok") and after.get("ok"):
        b_win = set(w["name"][:40] for w in before.get("results", {}).get("uia", {}).get("top_windows", []))
        a_win = set(w["name"][:40] for w in after.get("results", {}).get("uia", {}).get("top_windows", []))
        new_wins = a_win - b_win
        gone_wins = b_win - a_win
        if new_wins:
            changes.append(f"新窗口: {new_wins}")
        if gone_wins:
            changes.append(f"关闭窗口: {gone_wins}")

        b_text = before.get("results", {}).get("ocr", {}).get("text_sample", "")
        a_text = after.get("results", {}).get("ocr", {}).get("text_sample", "")
        if b_text != a_text:
            changes.append("屏幕文字已变化")

    return {
        "ok": True,
        "cap": "local_eye",
        "action": "diff",
        "domain": "感知域",
        "interval_sec": interval,
        "changes": changes,
        "change_count": len(changes),
    }


HANDLERS = {"scan": do_scan, "diff": do_diff}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "scan"
    params_str = sys.argv[2] if len(sys.argv) > 2 else "{}"
    try:
        params = json.loads(params_str)
    except Exception:
        params = {}
    handler = HANDLERS.get(action)
    if handler:
        result = handler(params)
        print(json.dumps(result, ensure_ascii=False, default=str))
    else:
        print(json.dumps({"ok": False, "error": f"未知动作: {action}", "available": list(HANDLERS.keys())}, ensure_ascii=False))
