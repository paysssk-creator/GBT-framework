# 开发者：自由的风
"""circuit_breaker/run.py — 熔断器·cap执行断路器

状态: CLOSED─[N次失败/M秒]▶OPEN─[超时]▶HALF_OPEN─[成功]▶CLOSED
       HALF_OPEN─[探测失败]▶OPEN
"""
import sys, json, os, time
from pathlib import Path

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THRESHOLD = 3
WINDOW = 60
HALF_OPEN_AFTER = 30
BREAKERS = Path.home() / ".gbt" / "circuit_breakers.json"


def _load():
    if not BREAKERS.exists(): return {}
    try: return json.loads(BREAKERS.read_text())
    except: return {}


def _save(s):
    BREAKERS.parent.mkdir(parents=True, exist_ok=True)
    BREAKERS.write_text(json.dumps(s, indent=2, default=str))


def _cap(params):
    return params.get("cap", params.get("cap_id", ""))


def _state(now, cap):
    st = cap.get("state", "closed")
    fs = cap.get("failures", [])
    recent = [f for f in fs if f > now - WINDOW]
    if st == "open":
        return ("half_open" if now - cap.get("opened_at", 0) >= HALF_OPEN_AFTER
                else "open"), recent
    if st == "half_open": return "half_open", recent
    return ("open" if len(recent) >= THRESHOLD else "closed"), recent


def do_check(params):
    cid = _cap(params)
    if not cid: return {"ok": False, "error": "缺少cap参数"}
    data = _load(); now = time.time(); cap = data.get(cid, {})
    state, recent = _state(now, cap)
    if params.get("success") and state == "half_open":
        cap.update(state="closed", failures=[]); cap.pop("opened_at", None)
        data[cid] = cap; _save(data); state = "closed"; recent = []
    return {"ok": True, "cap": cid, "state": state,
            "recent_failures": len(recent), "threshold": THRESHOLD, "window_s": WINDOW}


def do_fail(params):
    cid = _cap(params)
    if not cid: return {"ok": False, "error": "缺少cap参数"}
    data = _load(); now = time.time(); cap = data.get(cid, {})
    fs = cap.get("failures", []); fs.append(now)
    cap["failures"] = [f for f in fs if f > now - WINDOW * 2]
    if cap.get("state") == "half_open":
        cap["state"] = "open"; cap["opened_at"] = now
    else:
        cap.pop("manual_state", None)
    state, recent = _state(now, cap)
    if state == "open" and cap.get("state") != "open":
        cap["state"] = "open"; cap["opened_at"] = cap.get("opened_at", now)
    data[cid] = cap; _save(data)
    return {"ok": True, "cap": cid, "state": state,
            "recent_failures": len(recent), "tripped": state == "open"}


def do_trip(params):
    cid = _cap(params)
    if not cid: return {"ok": False, "error": "缺少cap参数"}
    data = _load(); now = time.time()
    old_fs = data.get(cid, {}).get("failures", [])
    data[cid] = {"state": "open", "opened_at": now, "manual_state": "open", "failures": old_fs}
    _save(data)
    return {"ok": True, "cap": cid, "state": "open", "manual": True}


def do_reset(params):
    cid = _cap(params)
    if not cid: return {"ok": False, "error": "缺少cap参数"}
    data = _load(); data[cid] = {"state": "closed", "failures": []}; _save(data)
    return {"ok": True, "cap": cid, "state": "closed", "reset": True}


def do_status(params):
    data = _load(); now = time.time(); out = {}
    for cid, cap in data.items():
        state, _ = _state(now, cap)
        fs = cap.get("failures", [])
        out[cid] = {"state": state, "recent_failures": len([f for f in fs if f > now - WINDOW]),
                    "total_failures": len(fs), "opened_at": cap.get("opened_at")}
    return {"ok": True, "total": len(out), "breakers": out}


def do_enforce_before_call(params):
    """检查断路器状态，返回是否允许调用"""
    cid = params.get("cap_name", _cap(params))
    if not cid:
        return {"ok": False, "error": "缺少 cap_name"}
    data = _load()
    now = time.time()
    cap = data.get(cid, {})
    state, recent = _state(now, cap)
    return {"ok": True, "cap": cid, "state": state,
            "allowed": state != "open",
            "recent_failures": len(recent), "threshold": THRESHOLD,
            "window_s": WINDOW, "half_open_after_s": HALF_OPEN_AFTER}


def do_report_result(params):
    """上报cap执行结果，驱动状态机转换"""
    cid = params.get("cap_name", _cap(params))
    if not cid:
        return {"ok": False, "error": "缺少 cap_name"}
    success = params.get("success", False)
    data = _load()
    now = time.time()
    cap = data.get(cid, {})
    eff_state, recent = _state(now, cap)

    if success:
        if eff_state == "half_open":
            cap["state"] = "closed"
            cap["failures"] = []
            cap.pop("opened_at", None)
            new_state = "closed"
        else:
            new_state = eff_state
    else:
        fs = cap.get("failures", [])
        fs.append(now)
        recent = [f for f in fs if f > now - WINDOW]
        cap["failures"] = fs
        if eff_state == "half_open":
            cap["state"] = "open"
            cap["opened_at"] = now
            new_state = "open"
        elif len(recent) >= THRESHOLD:
            cap["state"] = "open"
            cap["opened_at"] = now
            new_state = "open"
        else:
            new_state = "closed"

    data[cid] = cap
    _save(data)
    return {"ok": True, "cap": cid, "state": new_state,
            "success_reported": success,
            "recent_failures": len(recent)}


def do_global_status(params):
    """返回所有断路器状态"""
    data = _load(); now = time.time(); out = {}
    for cid, cap in data.items():
        state, recent = _state(now, cap)
        out[cid] = {"state": state, "recent_failures": len(recent),
                     "threshold": THRESHOLD, "window_s": WINDOW}
    return {"ok": True, "total": len(out), "breakers": out}


HANDLERS = {
    "check": do_check, "fail": do_fail, "trip": do_trip,
    "reset": do_reset, "status": do_status,
    "enforce_before_call": do_enforce_before_call,
    "report_result": do_report_result,
    "global_status": do_global_status,
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
