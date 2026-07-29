# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
# ⛔ 链路内核集成 — 不可绕过
"""
brain/vision_dispatch.py — 统一视觉调度器 · 场景路由
======================================================
一个入口 gbt_see("我想看什么") → 自动路由到正确的视觉系统
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

SCENE_ROUTES = {
    "screen_see": {"triggers": ["看屏幕", "屏幕上有什么", "看看", "screenshot", "截屏"], "method": "eyes_read_all", "system": "eyes", "description": "全屏OCR文字识别"},
    "screen_find": {"triggers": ["找", "在哪里", "位置", "定位", "find", "locate"], "method": "eyes_find", "system": "eyes", "description": "在屏幕上查找文字并返回坐标"},
    "screen_wait": {"triggers": ["等", "等待出现", "等到", "wait for", "until appears"], "method": "eyes_wait_for", "system": "eyes", "description": "等待屏幕出现指定文字"},
    "screen_wait_gone": {"triggers": ["消失", "不见了", "关闭了", "wait until gone"], "method": "eyes_wait_until_gone", "system": "eyes", "description": "等待屏幕上指定文字消失"},
    "screen_region": {"triggers": ["这个区域", "放大看", "zoom", "region"], "method": "eyes_look_deep", "system": "eyes", "description": "深度分析屏幕指定区域"},
    "screen_save": {"triggers": ["截图保存", "保存截图", "save screenshot"], "method": "eyes_to_image", "system": "eyes", "description": "截图保存到文件"},
    "screen_record": {"triggers": ["录屏", "录制", "record screen"], "method": "eyes_movie", "system": "eyes", "description": "录制屏幕视频"},
    "screen_watch": {"triggers": ["监控", "持续看", "盯着", "monitor", "watch"], "method": "eyes_watch", "system": "eyes", "description": "周期性监控屏幕变化"},
    "screen_compare": {"triggers": ["对比", "变化", "不同", "compare", "diff"], "method": "eyes_compare", "system": "eyes", "description": "对比两个区域是否相同"},
    "screen_color": {"triggers": ["颜色", "什么色", "color", "pixel"], "method": "eyes_colors_at", "system": "eyes", "description": "获取像素点颜色"},
    "screen_browse": {"triggers": ["浏览", "分析这个页面", "browse", "describe"], "method": "eyes_browse", "system": "eyes", "description": "用视觉LLM浏览和分析屏幕内容"},
    "screen_stable": {"triggers": ["稳定了", "不动了", "stable"], "method": "eyes_wait_stable", "system": "eyes", "description": "等待屏幕稳定"},
    "tentacle_url": {"triggers": ["下载图片", "在线图片", "download image", "from url"], "method": "tentacle_url", "system": "tentacle", "description": "从URL下载并分析远程图片"},
    "tentacle_clipboard": {"triggers": ["剪贴板", "clipboard", "pasted image"], "method": "tentacle_clipboard", "system": "tentacle", "description": "读取剪贴板中的图片"},
    "tentacle_file": {"triggers": ["打开图片", "图片文件", "open image"], "method": "tentacle_file", "system": "tentacle", "description": "读取本地图片文件"},
    "tentacle_camera": {"triggers": ["摄像头", "拍照", "camera", "webcam"], "method": "tentacle_camera", "system": "tentacle", "description": "打开摄像头拍照"},
    "tentacle_window": {"triggers": ["指定窗口", "窗口截图", "window capture"], "method": "tentacle_window", "system": "tentacle", "description": "截取指定应用窗口"},
    "tentacle_video": {"triggers": ["视频帧", "video frame"], "method": "tentacle_video", "system": "tentacle", "description": "从视频中提取帧"},
    "cortex_page": {"triggers": ["分析网页", "网页结构", "page structure", "web design"], "method": "cortex_analyze_page", "system": "cortex", "description": "三层结构分析网页"},
    "cortex_health": {"triggers": ["视觉健康", "界面检查", "visual health"], "method": "cortex_patrol", "system": "cortex", "description": "视觉健康巡检"},
    "memory_recall": {"triggers": ["之前看到", "记得看到", "previously saw", "history"], "method": "memory_recall", "system": "memory", "description": "从视觉记忆中搜索"},
    "memory_now": {"triggers": ["现在看到什么", "what do I see", "current view"], "method": "memory_now", "system": "memory", "description": "查询当前最新视觉记忆"},
    "memory_today": {"triggers": ["今天看到", "今日视觉", "today visual"], "method": "memory_today", "system": "memory", "description": "汇总今天的视觉历史"},
}


class VisionDispatch:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_init"):
            return
        self._init = True
        from brain.chain_kernel import enforce_chain
        enforce_chain("vision_dispatch.init")
        self._last_scene = None
        self._call_count = 0

    def match_scene(self, text):
        text_lower = text.lower()
        best_match = None
        best_score = 0
        for scene_id, scene in SCENE_ROUTES.items():
            score = 0
            for trigger in scene["triggers"]:
                if trigger.lower() in text_lower:
                    score = max(score, len(trigger))
            if score > best_score:
                best_score = score
                best_match = {"scene_id": scene_id, **scene, "match_score": score}
        return best_match or {"scene_id": "screen_see", "method": "eyes_read_all", "system": "eyes", "description": "默认: 全屏OCR识别", "match_score": 0, "triggers": []}

    def execute(self, scene, **kwargs):
        method = scene["method"]
        t0 = time.time()
        result = {"ok": False, "scene": scene["scene_id"], "method": method, "system": scene["system"]}
        try:
            if method == "eyes_read_all":
                from brain.host_body import eyes
                r = eyes.read_all()
                result.update(r)
            elif method == "eyes_find":
                from brain.host_body import eyes
                text = kwargs.get("text", kwargs.get("query", ""))
                if not text:
                    return {"ok": False, "error": "eyes_find need text param"}
                r = eyes.find(text)
                result.update(r)
            elif method == "eyes_wait_for":
                from brain.host_body import eyes
                text = kwargs.get("text", kwargs.get("query", ""))
                timeout = kwargs.get("timeout", 30)
                r = eyes.wait_for(text, timeout=timeout)
                result.update({"ok": r is not None, "found": r is not None, "position": r})
            elif method == "eyes_wait_until_gone":
                from brain.host_body import eyes
                text = kwargs.get("text", "")
                r = eyes.wait_until_gone(text, timeout=kwargs.get("timeout", 30))
                result.update({"ok": True, "gone": r})
            elif method == "eyes_look_deep":
                from brain.host_body import eyes
                r = eyes.look_deep(x=kwargs.get("x", 0), y=kwargs.get("y", 0), w=kwargs.get("w", 1920), h=kwargs.get("h", 1080))
                result.update(r)
            elif method == "eyes_to_image":
                from brain.host_body import eyes
                r = eyes.to_image(filepath=kwargs.get("filepath"))
                result.update(r)
            elif method == "eyes_movie":
                from brain.host_body import eyes
                r = eyes.movie(duration=kwargs.get("duration", 10), fps=kwargs.get("fps", 30))
                result.update(r)
            elif method == "eyes_watch":
                from brain.host_body import eyes
                eyes.watch(interval=kwargs.get("interval", 2), duration=kwargs.get("duration", 60))
                result.update({"ok": True, "status": "watching"})
            elif method == "eyes_compare":
                from brain.host_body import eyes
                r = eyes.compare(region1=kwargs.get("region1", {}), region2=kwargs.get("region2", {}))
                result.update(r)
            elif method == "eyes_colors_at":
                from brain.host_body import eyes
                r = eyes.colors_at(x=kwargs.get("x", 0), y=kwargs.get("y", 0))
                result.update(r)
            elif method == "eyes_browse":
                from brain.host_body import eyes
                r = eyes.browse_screen(question=kwargs.get("question", kwargs.get("query", "What is on screen?")))
                result.update(r)
            elif method == "eyes_wait_stable":
                from brain.host_body import eyes
                r = eyes.wait_for_stable(timeout=kwargs.get("timeout", 5))
                result.update(r)
            elif method == "tentacle_url":
                from brain.vision_tentacle import get_vision
                r = get_vision().from_url(kwargs.get("url", kwargs.get("query", "")))
                result.update(r)
            elif method == "tentacle_clipboard":
                from brain.vision_tentacle import get_vision
                r = get_vision().from_clipboard()
                result.update(r)
            elif method == "tentacle_file":
                from brain.vision_tentacle import get_vision
                r = get_vision().from_file(kwargs.get("path", kwargs.get("query", "")))
                result.update(r)
            elif method == "tentacle_camera":
                from brain.vision_tentacle import get_vision
                r = get_vision().from_camera(camera_index=kwargs.get("camera_index", 0))
                result.update(r)
            elif method == "tentacle_window":
                from brain.vision_tentacle import get_vision
                r = get_vision().from_window(window_title=kwargs.get("window_title", ""))
                result.update(r)
            elif method == "tentacle_video":
                from brain.vision_tentacle import get_vision
                r = get_vision().from_video_frame(video_path=kwargs.get("video_path", ""), frame_index=kwargs.get("frame_index", 0))
                result.update(r)
            elif method == "cortex_analyze_page":
                from brain.visual_cortex import get_cortex
                html = kwargs.get("html", "")
                url = kwargs.get("url", "")
                r = get_cortex().analyze_screen() if not html else get_cortex().analyze_page(html, url)
                result.update(r)
            elif method == "cortex_patrol":
                from brain.visual_cortex import get_cortex
                r = get_cortex().patrol_visual_health()
                result.update(r)
            elif method == "memory_recall":
                from brain.visual_memory import get_memory
                r = get_memory().recall(query=kwargs.get("query", ""), limit=kwargs.get("limit", 10))
                result.update({"ok": True, "memories": r})
            elif method == "memory_now":
                from brain.visual_memory import get_memory
                r = get_memory().what_i_see_now()
                result.update(r)
            elif method == "memory_today":
                from brain.visual_memory import get_memory
                r = get_memory().today_summary()
                result.update(r)
        except Exception as e:
            result.update({"ok": False, "error": str(e)[:200]})
        result["elapsed_ms"] = round((time.time() - t0) * 1000)
        self._last_scene = scene
        self._call_count += 1
        return result

    def status(self):
        return {"last_scene": self._last_scene["scene_id"] if self._last_scene else None, "call_count": self._call_count}

    def list_scenes(self):
        return [{"scene_id": sid, "system": s["system"], "description": s["description"]} for sid, s in SCENE_ROUTES.items()]


_dispatch = None

def get_dispatch():
    global _dispatch
    if _dispatch is None:
        _dispatch = VisionDispatch()
    return _dispatch

def gbt_see(query="", **kwargs):
    d = get_dispatch()
    scene = d.match_scene(query)
    return d.execute(scene, query=query, **kwargs)

def vision_status():
    return get_dispatch().status()

def vision_scenes():
    return get_dispatch().list_scenes()
