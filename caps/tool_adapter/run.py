# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""tool_adapter/run.py — 工具适配器·桥接HOST_BODY能力到可用工具
=================================================================
AI协作 ready — 将cap风格动作映射到实际可用的执行路径。
三层优先级: 原生OMP工具 > 本地Python库 > 子进程cap调用
"""
import sys
import json
import os
import subprocess
from pathlib import Path

CAPS_ROOT = Path(__file__).parent.parent
SANDBOX = Path(__file__).parent.parent.parent
GBT_DIR = Path.home() / ".gbt"
os.makedirs(GBT_DIR / "tool_adapter", exist_ok=True)


# ── Availability Probes ──────────────────────────────────────────

def _probe_import(module: str) -> bool:
    """检测Python模块是否可导入"""
    try:
        __import__(module)
        return True
    except ImportError:
        return False


def _probe_cap(cap_id: str) -> bool:
    """检测cap目录是否存在且含有run.py"""
    return (CAPS_ROOT / cap_id / "run.py").exists()


def _probe_env() -> dict:
    """探测当前运行环境"""
    return {
        "in_omp": os.environ.get("OMP_SESSION", "") != "" or os.environ.get("OMP_HARNESS", "") != "",
        "platform": sys.platform,
        "python": sys.version.split()[0],
    }


# ── Mapping Table ────────────────────────────────────────────────
# 每个cap风格动作 → 优先级降序的可用执行路径列表
# type: omp_tool | python_lib | cap_call

TOOL_MAP = {
    "screenshot": {
        "name": "screenshot",
        "description": "屏幕截图",
        "tiers": [
            {"type": "omp_tool", "tool": "browser", "method": "tab.screenshot", "priority": 1,
             "note": "OMP browser工具截图 — 仅限OMP harness进程内"},
            {"type": "python_lib", "module": "mss", "fallback_module": "PIL.ImageGrab",
             "priority": 2, "note": "本地Python库截图 (mss > PIL)"},
            {"type": "cap_call", "cap": "screenshot", "action": "capture",
             "priority": 3, "note": "子进程调用 caps/screenshot/run.py"},
        ]
    },
    "desktop_click": {
        "name": "desktop_click",
        "description": "桌面鼠标点击",
        "tiers": [
            {"type": "omp_tool", "tool": "browser", "method": "tab.click", "priority": 1,
             "note": "OMP browser工具点击 — 仅限浏览器内"},
            {"type": "python_lib", "module": "pyautogui", "priority": 2,
             "note": "本地pyautogui库桌面操控"},
            {"type": "cap_call", "cap": "desktop_master", "action": "click",
             "priority": 3, "note": "子进程调用 caps/desktop_master/run.py"},
        ]
    },
    "screen_ocr": {
        "name": "screen_ocr",
        "description": "屏幕文字识别",
        "tiers": [
            {"type": "omp_tool", "tool": "browser", "method": "tab.extract", "priority": 1,
             "note": "OMP browser工具提取 — 仅限浏览器内"},
            {"type": "python_lib", "module": "pytesseract", "priority": 2,
             "note": "本地pytesseract OCR"},
            {"type": "cap_call", "cap": "screen_ocr", "action": "read_all",
             "priority": 3, "note": "子进程调用 caps/screen_ocr/run.py"},
        ]
    },
    "desktop_type": {
        "name": "desktop_type",
        "description": "桌面键盘输入",
        "tiers": [
            {"type": "omp_tool", "tool": "browser", "method": "tab.type", "priority": 1,
             "note": "OMP browser工具输入 — 仅限浏览器内"},
            {"type": "python_lib", "module": "pyautogui", "priority": 2,
             "note": "本地pyautogui键盘输入"},
            {"type": "cap_call", "cap": "desktop_type", "action": "type",
             "priority": 3, "note": "子进程调用 caps/desktop_type/run.py"},
        ]
    },
    "desktop_master": {
        "name": "desktop_master",
        "description": "桌面全能操控",
        "tiers": [
            {"type": "python_lib", "module": "pyautogui", "priority": 1,
             "note": "本地pyautogui全能桌面操控"},
            {"type": "cap_call", "cap": "desktop_master", "action": "autopilot",
             "priority": 2, "note": "子进程调用 caps/desktop_master/run.py"},
        ]
    },
}


def _resolve_tool(action_name: str) -> dict | None:
    """模糊匹配动作名到TOOL_MAP条目"""
    if action_name in TOOL_MAP:
        return TOOL_MAP[action_name]
    # 别名匹配
    aliases = {
        "capture": "screenshot", "screen_capture": "screenshot",
        "click": "desktop_click", "mouse_click": "desktop_click",
        "ocr": "screen_ocr", "read_screen": "screen_ocr",
        "type": "desktop_type", "keyboard_input": "desktop_type",
        "autopilot": "desktop_master",
    }
    mapped = aliases.get(action_name, action_name)
    return TOOL_MAP.get(mapped)


# ── Actions ──────────────────────────────────────────────────────

def do_map_tool(params: dict) -> dict:
    """将cap风格的动作名映射到最佳可用工具路由决策

    params:
        cap_style_action: str — 如 "screenshot", "desktop_click", "screen_ocr", "desktop_type"
        strict: bool — 是否严格匹配 (默认false，允许别名)

    返回:
        ok, action, routing (最佳可用路径), all_tiers (全部优先级)
    """
    action_name = params.get("cap_style_action", params.get("action", ""))
    strict = params.get("strict", False)

    if not action_name:
        return {"ok": False, "error": "缺少 cap_style_action 参数"}

    entry = _resolve_tool(action_name)
    if not entry:
        if strict:
            return {"ok": False, "error": f"未知动作: {action_name}",
                    "known_actions": list(TOOL_MAP.keys())}
        return {"ok": False, "error": f"未找到 {action_name} 的映射",
                "hint": "使用 list_available 查看支持的动作"}

    # 按优先级评估每个tier的可用性
    tiers_available = []
    best = None

    for tier in entry["tiers"]:
        tier_info = dict(tier)
        if tier["type"] == "omp_tool":
            env = _probe_env()
            tier_info["available"] = env["in_omp"]
            tier_info["env"] = env
        elif tier["type"] == "python_lib":
            tier_info["available"] = _probe_import(tier["module"])
            # 部分工具支持fallback module
            if not tier_info["available"] and "fallback_module" in tier:
                tier_info["available"] = _probe_import(tier["fallback_module"])
                if tier_info["available"]:
                    tier_info["used_fallback"] = tier["fallback_module"]
        elif tier["type"] == "cap_call":
            tier_info["available"] = _probe_cap(tier["cap"])

        tiers_available.append(tier_info)
        if tier_info["available"] and best is None:
            best = tier_info

    return {
        "ok": True,
        "action": action_name,
        "description": entry["description"],
        "routing": best if best else {"type": "none", "available": False,
                                       "error": "没有可用的执行路径"},
        "all_tiers": tiers_available,
    }


def do_list_available(params: dict) -> dict:
    """扫描当前环境中实际可用的工具类型

    返回每种动作及其各优先级的可用性。
    """
    filter_action = params.get("action", params.get("cap_style_action", ""))

    results = {}
    targets = [filter_action] if filter_action else list(TOOL_MAP.keys())

    for action_name in targets:
        entry = _resolve_tool(action_name)
        if not entry:
            results[action_name] = {"known": False, "error": "未知动作"}
            continue

        tier_results = []
        best_available = None

        for tier in entry["tiers"]:
            tier_info = {"type": tier["type"], "priority": tier["priority"]}
            if tier["type"] == "omp_tool":
                tier_info["tool"] = tier.get("tool", "")
                tier_info["available"] = _probe_env()["in_omp"]
            elif tier["type"] == "python_lib":
                tier_info["module"] = tier.get("module", "")
                tier_info["available"] = _probe_import(tier["module"])
                if not tier_info["available"] and "fallback_module" in tier:
                    fb = tier["fallback_module"]
                    tier_info["available"] = _probe_import(fb)
                    if tier_info["available"]:
                        tier_info["module"] = fb
            elif tier["type"] == "cap_call":
                tier_info["cap"] = tier.get("cap", "")
                tier_info["action"] = tier.get("action", "")
                tier_info["available"] = _probe_cap(tier["cap"])

            tier_results.append(tier_info)
            if tier_info["available"] and best_available is None:
                best_available = tier_info

        results[action_name] = {
            "description": entry["description"],
            "best": best_available if best_available else {"type": "none", "available": False},
            "tiers": tier_results,
        }

    env = _probe_env()
    return {
        "ok": True,
        "environment": env,
        "actions": results,
        "total": len(results),
        "available_count": sum(1 for r in results.values()
                               if r.get("best", {}).get("available", False)),
    }


def do_call_tool(params: dict) -> dict:
    """通过适配器路由执行工具调用

    params:
        cap_style_action: str — 动作名
        tool_params: dict — 传递给目标工具的参数

    按优先级尝试执行，成功即返回。
    """
    action_name = params.get("cap_style_action", params.get("action", ""))
    tool_params = params.get("tool_params", params.get("params", {}))

    if not action_name:
        return {"ok": False, "error": "缺少 cap_style_action 参数"}

    entry = _resolve_tool(action_name)
    if not entry:
        return {"ok": False, "error": f"未知动作: {action_name}",
                "available": do_list_available({})["actions"]}

    # 按优先级尝试每条路径
    tried = []

    for tier in entry["tiers"]:
        tier_info = {"type": tier["type"], "priority": tier["priority"]}

        if tier["type"] == "omp_tool":
            if _probe_env()["in_omp"]:
                tier_info["available"] = True
                tier_info["note"] = "OMP环境已检测到, 但子进程cap无法直接调用xd://工具。" \
                                    "调用方应在OMP harness内通过browser tool执行。"
                tried.append(tier_info)
                continue
            tier_info["available"] = False
            tier_info["reason"] = "不在OMP环境中"
            tried.append(tier_info)
            continue

        elif tier["type"] == "python_lib":
            module_name = tier["module"]
            if not _probe_import(module_name):
                tier_info["available"] = False
                tier_info["reason"] = f"无法导入 {module_name}"
                tried.append(tier_info)
                continue

            tier_info["available"] = True
            tier_info["module"] = module_name
            try:
                result = _execute_python_tool(module_name, action_name, tool_params)
                if result.get("ok"):
                    result["routing"] = tier_info
                    result["tried"] = tried
                    return result
                else:
                    tier_info["result"] = result
                    tier_info["status"] = "executed_but_failed"
            except Exception as e:
                tier_info["status"] = "exception"
                tier_info["error"] = str(e)[:200]
            tried.append(tier_info)

        elif tier["type"] == "cap_call":
            cap_id = tier["cap"]
            cap_action = tier.get("action", action_name)
            if not _probe_cap(cap_id):
                tier_info["available"] = False
                tier_info["reason"] = f"cap {cap_id} 不存在"
                tried.append(tier_info)
                continue

            tier_info["available"] = True
            tier_info["cap"] = cap_id
            tier_info["action"] = cap_action
            try:
                result = _execute_cap_call(cap_id, cap_action, tool_params)
                if result.get("ok"):
                    result["routing"] = tier_info
                    result["tried"] = tried
                    return result
                else:
                    tier_info["result"] = result
                    tier_info["status"] = "executed_but_failed"
            except Exception as e:
                tier_info["status"] = "exception"
                tier_info["error"] = str(e)[:200]
            tried.append(tier_info)

    return {
        "ok": False,
        "error": f"所有执行路径均不可用或失败: {action_name}",
        "action": action_name,
        "tried": tried,
        "advice": "请检查环境依赖或安装所需Python库",
    }


# ── Execution Helpers ────────────────────────────────────────────

def _execute_python_tool(module: str, action: str, params: dict) -> dict:
    """通过Python库执行工具动作"""
    if module == "mss":
        return _exec_mss(params)
    elif module == "PIL.ImageGrab":
        return _exec_pil_grab(params)
    elif module == "pyautogui":
        return _exec_pyautogui(action, params)
    elif module == "pytesseract":
        return _exec_pytesseract(params)
    else:
        return {"ok": False, "error": f"Python库 {module} 无执行适配器"}


def _exec_mss(params: dict) -> dict:
    """mss截图"""
    try:
        import mss
        import mss.tools
        import base64
        monitor = params.get("monitor", 1)
        region = params.get("region", None)
        with mss.MSS() as sct:
            if region and len(region) == 4:
                mon = {"top": region[1], "left": region[0],
                       "width": region[2] - region[0],
                       "height": region[3] - region[1]}
                img = sct.grab(mon)
            else:
                img = sct.grab(sct.monitors[monitor])
            png = mss.tools.to_png(img.rgb, img.size)
            b64 = base64.b64encode(png).decode("ascii")
            return {"ok": True, "format": "base64_png", "width": img.width,
                    "height": img.height, "data": b64}
    except Exception as e:
        return {"ok": False, "error": f"mss截图失败: {e}"}


def _exec_pil_grab(params: dict) -> dict:
    """PIL ImageGrab截图"""
    try:
        from PIL import ImageGrab
        import base64
        import io
        region = params.get("region", None)
        img = ImageGrab.grab(bbox=tuple(region)) if region else ImageGrab.grab()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return {"ok": True, "format": "base64_png", "width": img.width,
                "height": img.height, "data": b64}
    except Exception as e:
        return {"ok": False, "error": f"PIL截图失败: {e}"}


def _exec_pyautogui(action: str, params: dict) -> dict:
    """pyautogui桌面操控"""
    try:
        import pyautogui
        pyautogui.FAILSAFE = False

        if action in ("screenshot", "capture", "screen_capture"):
            import base64, io
            region = params.get("region", None)
            img = pyautogui.screenshot(region=tuple(region)) if region else pyautogui.screenshot()
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            return {"ok": True, "format": "base64_png", "width": img.width,
                    "height": img.height, "data": b64}

        elif action in ("desktop_click", "click", "mouse_click"):
            x = params.get("x", 0)
            y = params.get("y", 0)
            button = params.get("button", "left")
            clicks = params.get("clicks", 1)
            pyautogui.click(x, y, clicks=clicks, button=button)
            pos = pyautogui.position()
            return {"ok": True, "clicked": {"x": x, "y": y},
                    "button": button, "clicks": clicks,
                    "current_position": {"x": pos.x, "y": pos.y}}

        elif action in ("desktop_type", "type", "keyboard_input"):
            text = params.get("text", params.get("content", ""))
            interval = params.get("interval", 0.05)
            pyautogui.typewrite(text, interval=interval)
            return {"ok": True, "typed": len(text), "text": text[:200]}

        elif action in ("desktop_master", "autopilot"):
            sub_action = params.get("sub_action", "click")
            if sub_action == action:
                return {"ok": False, "error": f"拒绝递归: sub_action={sub_action} == action={action}"}
            return _exec_pyautogui(sub_action, params)

        else:
            return {"ok": False, "error": f"pyautogui不支持动作: {action}"}

    except Exception as e:
        return {"ok": False, "error": f"pyautogui执行失败: {e}"}


def _exec_pytesseract(params: dict) -> dict:
    """pytesseract OCR"""
    try:
        import pytesseract
        import base64, io
        from PIL import Image

        image_b64 = params.get("image", params.get("data", ""))
        lang = params.get("lang", "chi_sim+eng")

        if image_b64:
            img_data = base64.b64decode(image_b64)
            img = Image.open(io.BytesIO(img_data))
        else:
            # 先截图再OCR
            import mss
            import mss.tools
            monitor = params.get("monitor", 1)
            with mss.mss() as sct:
                screen = sct.grab(sct.monitors[monitor])
                png = mss.tools.to_png(screen.rgb, screen.size)
                img = Image.open(io.BytesIO(png))

        text = pytesseract.image_to_string(img, lang=lang)
        return {"ok": True, "text": text.strip(), "lang": lang,
                "length": len(text)}

    except Exception as e:
        return {"ok": False, "error": f"pytesseract OCR失败: {e}"}


def _execute_cap_call(cap_id: str, action: str, params: dict) -> dict:
    """通过子进程调用其他cap"""
    run_py = CAPS_ROOT / cap_id / "run.py"
    if not run_py.exists():
        return {"ok": False, "error": f"cap {cap_id} 不存在"}

    try:
        r = subprocess.run(
            [sys.executable, str(run_py), action,
             json.dumps(params, ensure_ascii=False)],
            capture_output=True, text=True, timeout=params.get("timeout", 30),
            cwd=str(SANDBOX), encoding="utf-8", errors="replace"
        )
        raw = (r.stdout or "").strip()
        if raw:
            try:
                result = json.loads(raw)
                result["_via_cap"] = cap_id
                return result
            except json.JSONDecodeError:
                return {"ok": True, "result": raw[:500], "_via_cap": cap_id}
        return {"ok": False, "error": (r.stderr or "无输出")[:200], "_via_cap": cap_id}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"cap {cap_id} 超时", "_via_cap": cap_id}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200], "_via_cap": cap_id}


# ── Handler Dispatch ─────────────────────────────────────────────

HANDLERS = {
    "map_tool": do_map_tool,
    "list_available": do_list_available,
    "call_tool": do_call_tool,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "list_available"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else {}
    handler = HANDLERS.get(action)
    if handler:
        result = handler(params)
        print(json.dumps(result, ensure_ascii=False, default=str))
    else:
        print(json.dumps({
            "ok": False, "error": f"未知动作: {action}",
            "available": list(HANDLERS.keys())
        }, ensure_ascii=False, default=str))
