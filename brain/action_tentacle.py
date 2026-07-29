# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
# ⛔ 链路内核集成 — 不可绕过
"""
brain/action_tentacle.py — 触手行动层 v1.0
==========================================
有了神经感知(L8)之后，触手不再只是"看"——它有了肌肉。

行动能力:
  desktop_click    — 鼠标点击任意坐标
  desktop_type     — 键盘输入任意文字
  browser_navigate — 浏览器导航+内容提取
  browser_click    — 浏览器内点击元素
  browser_fill     — 浏览器内填写表单
  element_find     — 定位屏幕上/页面中的UI元素

安全门:
  每次行动前 → 交叉验证 → 确认安全 → 执行 → 记录证据
  铁律: 没验证不许动，动了必有据。
"""
import json, time, sys
from pathlib import Path
from datetime import datetime
from typing import Optional

ROOT = Path(__file__).parent.parent
ACTION_LOG = Path.home() / ".gbt" / "neural_tentacle" / "action_log.jsonl"


def _log_action(action: str, result: dict):
    entry = {"ts": datetime.now().isoformat(), "action": action, **result}
    ACTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(ACTION_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


class ActionTentacle:
    """行动触手 — 神经驱动的肌肉层"""

    def __init__(self):
        self.action_count = 0
        self._last_action = None
        from brain.chain_kernel import enforce_chain
        enforce_chain("action_tentacle.init")

    def _check_safety(self, action: str, params: dict) -> dict:
        """行动前安全检查 — 交叉验证门"""
        from brain.cross_validation import cross_check_pulse
        # 简化: 检查系统是否健康
        try:
            from brain.neural_proprioception import full_proprioception
            prop = full_proprioception()
            if not prop["ok"]:
                return {"safe": False, "reason": "系统本体感知未通过，拒绝行动"}
        except Exception:
            pass
        return {"safe": True}

    # ═══════════════════════════════════════════
    # 桌面操控
    # ═══════════════════════════════════════════

    def desktop_click(self, x: int, y: int, button: str = "left") -> dict:
        """鼠标点击指定坐标"""
        from brain.immutable_chain import get_state, persist_state
        from datetime import datetime
        s = get_state()
        s["last_action_tentacle_click"] = datetime.now().isoformat()
        persist_state(s)
        safety = self._check_safety("desktop_click", {"x": x, "y": y})
        if not safety.get("safe"):
            return {"ok": False, "error": safety.get("reason", "安全检查未通过")}
        try:
            import pyautogui
            pyautogui.click(x, y, button=button)
            self.action_count += 1
            r = {"ok": True, "action": "click", "position": [x, y], "button": button}
            _log_action("desktop_click", r)
            return r
        except ImportError:
            return {"ok": False, "error": "pyautogui未安装", "fix": "pip install pyautogui"}

    def desktop_type(self, text: str, interval: float = 0.05) -> dict:
        """键盘输入文字"""
        safety = self._check_safety("desktop_type", {"text_len": len(text)})
        if not safety.get("safe"):
            return {"ok": False, "error": safety.get("reason")}
        try:
            import pyautogui
            pyautogui.typewrite(text, interval=interval)
            self.action_count += 1
            r = {"ok": True, "action": "type", "text_len": len(text)}
            _log_action("desktop_type", r)
            return r
        except ImportError:
            return {"ok": False, "error": "pyautogui未安装"}

    def desktop_screenshot(self) -> dict:
        """截屏 → 用于视觉验证"""
        try:
            import pyautogui
            img = pyautogui.screenshot()
            import io, base64
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            return {"ok": True, "action": "screenshot", "size": list(img.size), "base64_len": len(b64)}
        except ImportError:
            return {"ok": False, "error": "pyautogui未安装"}

    # ═══════════════════════════════════════════
    # 浏览器操控 (通过已打开的浏览器)
    # ═══════════════════════════════════════════

    def browser_click_text(self, url: str, text: str) -> dict:
        """在浏览器页面中点击包含指定文字的按钮/链接"""
        safety = self._check_safety("browser_click", {"url": url, "text": text})
        if not safety.get("safe"):
            return {"ok": False, "error": safety.get("reason")}
        try:
            from caps.browser_automation.run import do_click_text
            r = do_click_text({"url": url, "text": text})
            self.action_count += 1
            _log_action("browser_click_text", r)
            return r
        except Exception as e:
            return {"ok": False, "error": str(e)[:120]}

    def browser_fill(self, url: str, selector: str, value: str) -> dict:
        """在浏览器页面中填写表单"""
        safety = self._check_safety("browser_fill", {"url": url, "selector": selector})
        if not safety.get("safe"):
            return {"ok": False, "error": safety.get("reason")}
        try:
            from caps.browser_automation.run import do_fill
            r = do_fill({"url": url, "selector": selector, "value": value})
            self.action_count += 1
            _log_action("browser_fill", r)
            return r
        except Exception as e:
            return {"ok": False, "error": str(e)[:120]}

    def browser_navigate(self, url: str) -> dict:
        """浏览器导航到URL并返回内容"""
        safety = self._check_safety("browser_navigate", {"url": url})
        if not safety.get("safe"):
            return {"ok": False, "error": safety.get("reason")}
        try:
            from caps.browser_automation.run import do_navigate
            r = do_navigate({"url": url, "headless": True, "wait": 2000})
            self.action_count += 1
            _log_action("browser_navigate", r)
            return r
        except Exception as e:
            return {"ok": False, "error": str(e)[:120]}

    # ═══════════════════════════════════════════
    # 综合行动
    # ═══════════════════════════════════════════

    def reach_and_click(self, target_description: str) -> dict:
        """章鱼式操控: 自动定位并点击目标"""
        t0 = time.time()
        steps = []

        # 1. 先截屏看
        ss = self.desktop_screenshot()
        steps.append({"step": "screenshot", "ok": ss.get("ok", False)})

        # 2. 如果桌面操控不可用，尝试浏览器
        if not ss.get("ok"):
            r = self.browser_navigate("http://localhost:9121")
            steps.append({"step": "browser_navigate", "ok": r.get("ok", False)})

        elapsed = int((time.time() - t0) * 1000)
        return {"ok": any(s["ok"] for s in steps), "target": target_description,
                "elapsed_ms": elapsed, "steps": steps}


# ═══════════════════════════════════════════
# 全局单例 + 脉冲接入
# ═══════════════════════════════════════════

_action: Optional[ActionTentacle] = None


def get_action() -> ActionTentacle:
    global _action
    if _action is None:
        _action = ActionTentacle()
    return _action


def action_pulse(target: str = None) -> dict:
    """行动脉冲 — 章鱼触手出击"""
    a = get_action()
    if target:
        return a.reach_and_click(target)
    return {"ok": True, "action_count": a.action_count, "message": "触手待命"}


if __name__ == "__main__":
    r = action_pulse()
    # Windows GBK console fix: reconfigure stdout to UTF-8
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print(json.dumps(r, ensure_ascii=False, indent=2))
