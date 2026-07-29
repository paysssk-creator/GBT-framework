# 开发者：自由的风
'''desktop_master/run.py — 桌面程序autopilot+AI视觉操控'''
import sys, json, os, subprocess

def do_autopilot(params):
    app = params.get("app", params.get("program", ""))
    if not app:
        return {"ok": False, "error": "缺少app参数"}
    try:
        subprocess.Popen(app, shell=True)
        return {"ok": True, "cap": "desktop_master", "action": "autopilot", "app": app, "launched": True}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}

def do_click(params):
    x, y = params.get("x", 0), params.get("y", 0)
    try:
        import pyautogui
        pyautogui.click(x, y)
        return {"ok": True, "cap": "desktop_master", "action": "click", "position": [x, y]}
    except ImportError:
        return {"ok": False, "error": "pyautogui未安装"}

def do_type(params):
    text = params.get("text", "")
    try:
        import pyautogui
        pyautogui.typewrite(text, interval=0.05)
        return {"ok": True, "cap": "desktop_master", "action": "type", "text_len": len(text)}
    except ImportError:
        return {"ok": False, "error": "pyautogui未安装"}

def do_claude_computer_use(params):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"ok": False, "error": "Claude adapter requires ANTHROPIC_API_KEY"}

    prompt = params.get("prompt", "Look at the screen and describe what you see.")
    max_steps = params.get("max_steps", 10)
    model = params.get("model", "claude-sonnet-4-20250514")
    system_prompt = params.get(
        "system",
        "You are controlling a desktop computer. Use the provided screen image and computer_20241022 tool to interact via mouse and keyboard. Plan each action carefully."
    )

    try:
        import base64, io
        import requests
        import pyautogui
        import mss
        from PIL import Image
    except ImportError as e:
        return {"ok": False, "error": f"Missing dependency: {e}"}

    log = []
    actions_taken = []

    def _take_screenshot(sct, monitor):
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    try:
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            img_b64 = _take_screenshot(sct, monitor)

            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_b64}}
                ]
            }]

            tools = [{
                "type": "computer_20241022",
                "name": "computer",
                "display_width_px": monitor.width,
                "display_height_px": monitor.height,
                "display_number": 0
            }]

            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "anthropic-beta": "computer-use-2024-10-22",
                "content-type": "application/json"
            }

            for step in range(max_steps):
                payload = {
                    "model": model,
                    "max_tokens": 4096,
                    "messages": messages,
                    "system": system_prompt,
                    "tools": tools
                }

                try:
                    resp = requests.post(
                        "https://api.anthropic.com/v1/messages",
                        json=payload, headers=headers, timeout=120
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    log.append({"step": step, "error": f"API error: {str(e)[:200]}"})
                    break

                assistant_content = []

                for block in data.get("content", []):
                    if block.get("type") == "text":
                        assistant_content.append(block)
                        log.append({"step": step, "type": "text", "text": block.get("text", "")})
                    elif block.get("type") == "tool_use":
                        assistant_content.append(block)
                        tool_input = block.get("input", {})
                        action = tool_input.get("action", "")

                        entry = {"step": step, "action": action}
                        try:
                            if action == "mouse_move":
                                coord = tool_input.get("coordinate", [0, 0])
                                if coord and len(coord) >= 2:
                                    pyautogui.moveTo(coord[0], coord[1])
                                entry["coordinate"] = coord
                            elif action == "left_click":
                                coord = tool_input.get("coordinate", [])
                                if coord and len(coord) >= 2:
                                    pyautogui.click(coord[0], coord[1])
                                entry["coordinate"] = coord
                            elif action == "right_click":
                                coord = tool_input.get("coordinate", [])
                                if coord and len(coord) >= 2:
                                    pyautogui.rightClick(coord[0], coord[1])
                                entry["coordinate"] = coord
                            elif action == "double_click":
                                coord = tool_input.get("coordinate", [])
                                if coord and len(coord) >= 2:
                                    pyautogui.doubleClick(coord[0], coord[1])
                                entry["coordinate"] = coord
                            elif action == "middle_click":
                                coord = tool_input.get("coordinate", [])
                                if coord and len(coord) >= 2:
                                    pyautogui.middleClick(coord[0], coord[1])
                                entry["coordinate"] = coord
                            elif action == "type":
                                text_to_type = tool_input.get("text", "")
                                pyautogui.typewrite(text_to_type, interval=0.05)
                                entry["text"] = text_to_type
                            elif action == "key":
                                key_text = tool_input.get("text", "")
                                pyautogui.press(key_text)
                                entry["key"] = key_text
                            elif action == "screenshot":
                                pass
                            elif action == "left_click_drag":
                                coord = tool_input.get("coordinate", [])
                                if coord and len(coord) >= 2:
                                    pyautogui.dragTo(coord[0], coord[1], button="left")
                                entry["coordinate"] = coord
                            elif action == "scroll":
                                scroll_y = tool_input.get("scroll_y", 0)
                                if scroll_y:
                                    pyautogui.scroll(scroll_y)
                                entry["scroll"] = [tool_input.get("scroll_x", 0), scroll_y]
                            elif action == "cursor_position":
                                x, y = pyautogui.position()
                                entry["position"] = [x, y]
                            elif action == "left_mouse_down":
                                pyautogui.mouseDown(button="left")
                            elif action == "left_mouse_up":
                                pyautogui.mouseUp(button="left")
                            else:
                                entry["error"] = f"Unknown action: {action}"
                        except Exception as e:
                            entry["error"] = str(e)[:100]

                        log.append(entry)
                        actions_taken.append(action)

                if assistant_content:
                    messages.append({"role": "assistant", "content": assistant_content})

                stop_reason = data.get("stop_reason", "")
                if stop_reason == "end_turn":
                    break

                if stop_reason == "tool_use":
                    img_b64 = _take_screenshot(sct, monitor)

                    tool_results = []
                    for block in data.get("content", []):
                        if block.get("type") == "tool_use":
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.get("id", ""),
                                "content": [
                                    {"type": "text", "text": "Action executed."},
                                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_b64}}
                                ]
                            })

                    if tool_results:
                        messages.append({"role": "user", "content": tool_results})
                else:
                    break

    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

    return {
        "ok": True,
        "cap": "desktop_master",
        "action": "claude_computer_use",
        "model": model,
        "steps": len(log),
        "actions": actions_taken,
        "log": log
    }

HANDLERS = {"autopilot": do_autopilot, "click": do_click, "type": do_type, "claude_computer_use": do_claude_computer_use}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "autopilot"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
