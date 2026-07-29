# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
# ⛔ 链路内核集成 — 不可绕过
"""
brain/neighborhood_vision.py — 触手邻域视觉 · 统一视觉中枢
============================================================
打开邻域视觉 = 看到一切。

融合四大视觉系统到一个实时面板:
  ① tentacle_transmission → 触手穿透传输, 原始画面直接到大脑
  ② vision_tentacle     → 10通道采集(剪贴板/URL/摄像头/文件/窗口)
  ③ visual_cortex       → 3层结构分析
  ④ visual_memory       → 视觉历史时间线

输出: JSON状态快照 → neighborhood-vision.html 实时渲染
     + 桌面悬浮窗(可选)

特性:
  - 边操作边看所有画面和数据
  - 排查过程全程可见,避免遗漏
  - 对话面板不变,视觉面板独立
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

STATE_FILE = Path.home() / ".gbt" / "neighborhood_vision_state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════
#  邻域视觉中枢
# ═══════════════════════════════════════════════════════════

class NeighborhoodVision:
    """触手邻域视觉 — 你看到的一切在这里汇总"""

    def __init__(self):
        from brain.chain_kernel import enforce_chain
        enforce_chain("neighborhood_vision.init")
        self._panels = {}
        self._active = False
        self._snapshot_count = 0
        self._log: list[dict] = []

    # ── 面板采集 ──────────────────────────────

    def _capture_screen(self) -> dict:
        """面板1: 屏幕视觉 — 触手穿透传输, 无OCR"""
        try:
            from brain.host_body import eyes
            screen = eyes.see()  # 原始画面, 不OCR
            return {
                "panel": "screen",
                "image_ok": screen.get("ok", False),
                "image_size": len(screen.get("image", "")),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"panel": "screen", "error": str(e)[:200]}

    def _capture_tentacles(self) -> dict:
        try:
            from brain.vision_tentacle import get_vision
            v = get_vision()
            # 快速检查各通道
            channels = {}
            for ch in ["screen", "clipboard", "camera"]:
                try:
                    r = getattr(v, f"from_{ch}")()
                    channels[ch] = {"ok": r.get("ok", False), "image_size": len(r.get("image_b64", ""))}
                except Exception as e:
                    channels[ch] = {"ok": False, "error": str(e)[:100]}
            return {
                "panel": "tentacles",
                "channels": channels,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"panel": "tentacles", "error": str(e)[:200]}

    def _capture_cortex(self) -> dict:
        """面板3: 皮层分析"""
        try:
            from brain.visual_cortex import get_cortex
            c = get_cortex()
            r = c.analyze_screen()
            return {
                "panel": "cortex",
                "analysis": r,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"panel": "cortex", "error": str(e)[:200]}

    def _capture_memory(self) -> dict:
        """面板4: 视觉记忆"""
        try:
            from brain.visual_memory import get_memory
            m = get_memory()
            now = m.what_i_see_now()
            today = m.today_summary()
            return {
                "panel": "memory",
                "now": now,
                "today": today,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"panel": "memory", "error": str(e)[:200]}

    def _capture_debug(self) -> dict:
        """面板5: 调试/排查日志"""
        return {
            "panel": "debug",
            "logs": self._log[-50:],  # 最近50条
            "snapshot_count": self._snapshot_count,
            "active": self._active,
            "timestamp": datetime.now().isoformat(),
        }

    # ── 全量快照 ──────────────────────────────

    def snapshot(self, full: bool = False) -> dict:
        """采集一次全量邻域视觉快照

        full=True: 包含屏幕截图base64（用于实时画面传输）
        full=False: 仅OCR文本+状态（轻量，用于快速轮询）
        """
        t0 = time.time()
        self._snapshot_count += 1

        panels = {}
        panels["screen"] = self._capture_screen()
        panels["tentacles"] = self._capture_tentacles()
        panels["debug"] = self._capture_debug()

        if full:
            panels["cortex"] = self._capture_cortex()
            panels["memory"] = self._capture_memory()

        snapshot = {
            "ok": True,
            "snapshot_id": self._snapshot_count,
            "active": self._active,
            "panels": panels,
            "elapsed_ms": round((time.time() - t0) * 1000),
            "timestamp": datetime.now().isoformat(),
        }

        # 持久化到状态文件 → dashboard读取
        self._save_state(snapshot)

        self._log.append({
            "type": "snapshot",
            "id": self._snapshot_count,
            "elapsed_ms": snapshot["elapsed_ms"],
            "timestamp": snapshot["timestamp"],
        })
        # 保持日志在1000条以内
        if len(self._log) > 1000:
            self._log = self._log[-500:]

        return snapshot

    def _save_state(self, snapshot: dict):
        """保存状态到JSON文件 → neighborhood-vision.html读取"""
        try:
            # 精简版: 去掉过大的base64图片
            slim = json.loads(json.dumps(snapshot, default=str))
            if "screen" in slim.get("panels", {}):
                img = slim["panels"]["screen"].get("image_b64", "")
                if len(img) > 100000:  # >100KB截断
                    slim["panels"]["screen"]["image_b64"] = img[:100] + f"...[{len(img)} bytes truncated]"
            STATE_FILE.write_text(json.dumps(slim, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    # ── 日志 ──────────────────────────────────

    def log(self, event: str, detail: dict = None):
        self._log.append({
            "event": event,
            "detail": detail or {},
            "timestamp": datetime.now().isoformat(),
        })
        if len(self._log) > 1000:
            self._log = self._log[-500:]

    # ── 激活/停用 ─────────────────────────────

    def activate(self):
        """激活邻域视觉 — 开始持续采集"""
        self._active = True
        self.log("neighborhood_vision_activated")
        return {"ok": True, "status": "activated"}

    def deactivate(self):
        """停用邻域视觉"""
        self._active = False
        self.log("neighborhood_vision_deactivated")
        return {"ok": True, "status": "deactivated"}

    def status(self) -> dict:
        return {
            "active": self._active,
            "snapshots": self._snapshot_count,
            "logs": len(self._log),
            "state_file": str(STATE_FILE),
        }


# ═══════════════════════════════════════════════════════════
#  全局
# ═══════════════════════════════════════════════════════════

_nv: NeighborhoodVision | None = None

def get_nv() -> NeighborhoodVision:
    global _nv
    if _nv is None:
        _nv = NeighborhoodVision()
    return _nv

def nv_snapshot(full: bool = False) -> dict:
    return get_nv().snapshot(full=full)

def nv_activate() -> dict:
    return get_nv().activate()

def nv_deactivate() -> dict:
    return get_nv().deactivate()

def nv_status() -> dict:
    return get_nv().status()

def nv_log(event: str, detail: dict = None):
    get_nv().log(event, detail)


# ═══════════════════════════════════════════════════════════
#  自测
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  触手邻域视觉 · 自测")
    print("=" * 60)

    nv = get_nv()
    nv.activate()

    # 轻量快照
    snap = nv.snapshot(full=False)
    for _name, panel in snap["panels"].items():
        status = "✅" if panel.get("ok", True) and "error" not in panel else "❌"
        print(f"    {status} {panel['panel']}: {list(panel.keys())[:5]}")

    print(f"\n  状态: {nv.status()}")
