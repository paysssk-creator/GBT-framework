# 开发者：自由的风
"""omni_eye/run.py — UIA直接遍历桌面所有窗口元素
==============================================
感知域 core — 遍历Windows UI Automation树，返回结构化元素数据。
不经过截图，不经过视觉模型 — 摸到的是UI结构，不是图像。
"""
import sys, json, os

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    import uiautomation as auto
    HAS_UIA = True
except ImportError:
    HAS_UIA = False


def _element_to_dict(elem, max_depth=3, current_depth=0):
    """递归遍历UIA元素树，返回结构化字典"""
    if current_depth > max_depth:
        return None

    try:
        info = {
            "name": elem.Name[:200] if elem.Name else "",
            "type": elem.ControlTypeName,
            "class": elem.ClassName if elem.ClassName else "",
            "rect": {
                "left": int(elem.BoundingRectangle.left),
                "top": int(elem.BoundingRectangle.top),
                "width": int(elem.BoundingRectangle.width()),
                "height": int(elem.BoundingRectangle.height()),
            },
            "enabled": elem.IsEnabled,
            "visible": elem.IsOffscreen == False,
        }

        # 只在有意义时添加children
        if current_depth < max_depth - 1:
            try:
                children = elem.GetChildren()
                if children:
                    child_list = []
                    for child in children[:30]:  # 每层最多30个子元素
                        cd = _element_to_dict(child, max_depth, current_depth + 1)
                        if cd:
                            child_list.append(cd)
                    if child_list:
                        info["children"] = child_list
                        info["child_count"] = len(child_list)
            except Exception:
                pass

        return info
    except Exception:
        return None


def do_see(params):
    """遍历桌面所有顶层窗口 → 返回完整UI树"""
    if not HAS_UIA:
        return {"ok": False, "error": "uiautomation 未安装 (pip install uiautomation)",
                "available_actions": ["see", "focus"]}

    max_depth = params.get("depth", 2)
    filter_name = params.get("filter", "").lower()
    max_windows = params.get("max_windows", 20)

    try:
        root = auto.GetRootControl()
        windows = root.GetChildren()

        results = []
        visible_count = 0
        for win in windows[:max_windows]:
            name = win.Name or ""
            if filter_name and filter_name not in name.lower():
                continue
            if win.IsOffscreen:
                continue

            visible_count += 1
            elem = _element_to_dict(win, max_depth=max_depth)
            if elem:
                results.append(elem)

        return {
            "ok": True,
            "cap": "omni_eye",
            "action": "see",
            "domain": "感知域",
            "total_windows": len(windows),
            "visible_windows": visible_count,
            "returned": len(results),
            "depth": max_depth,
            "windows": results,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def do_focus(params):
    """聚焦指定窗口，返回其完整UI树"""
    if not HAS_UIA:
        return {"ok": False, "error": "uiautomation 未安装 (pip install uiautomation)"}

    name_filter = params.get("name", "").lower()
    class_filter = params.get("class", "").lower()
    depth = params.get("depth", 3)

    try:
        target = None
        for win in auto.GetRootControl().GetChildren():
            wname = (win.Name or "").lower()
            wclass = (win.ClassName or "").lower()

            if name_filter and name_filter in wname:
                target = win
                break
            if class_filter and class_filter in wclass:
                target = win
                break

        if not target:
            # 尝试精确匹配
            for win in auto.GetRootControl().GetChildren():
                if win.Name and name_filter == win.Name.lower():
                    target = win
                    break

        if not target:
            return {"ok": False, "error": f"未找到窗口: name={name_filter}, class={class_filter}"}

        elem = _element_to_dict(target, max_depth=depth)
        try:
            target.SetFocus()
            focused = True
        except Exception:
            focused = False

        return {
            "ok": True,
            "cap": "omni_eye",
            "action": "focus",
            "domain": "感知域",
            "focused": focused,
            "window_name": target.Name,
            "window_class": target.ClassName,
            "element_tree": elem,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


HANDLERS = {"see": do_see, "focus": do_focus}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "see"
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
