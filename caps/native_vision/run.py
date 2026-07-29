# ⛔ 开发者：自由的风 · 永久钢印
"""caps/native_vision/run.py — 原生视觉邻域
==============================================
GBT的眼睛和手 — 邻域原生能力，不依赖子进程。
所有邻域通过nexus路由即可调用视觉能力。

用法:
  python run.py see                    → 截全屏base64
  python run.py see '{"x":0,"y":0,"w":400,"h":300}'
  python run.py read '{"x":0,"y":0,"w":1920,"h":1080}'
  python run.py find '{"text":"登录"}'
  python run.py click '{"x":500,"y":300}'
  python run.py type '{"text":"hello"}'
  python run.py press '{"key":"enter"}'
  python run.py hotkey '{"keys":["ctrl","c"]}'
  python run.py scroll '{"amount":3}'
  python run.py analyze '{"question":"屏幕上有什么?"}'
"""

import sys, json, os, io
import subprocess, base64, time
from pathlib import Path
from datetime import datetime

# 抑制BetterCam导入时的stdout噪声(子进程调用时保持JSON干净)
_real_stdout = sys.stdout
sys.stdout = io.StringIO()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from brain.host_body import eyes, hands
sys.stdout = _real_stdout



# ── 路径与持久化 ─────────────────────────
ROOT = Path(__file__).parent.parent.parent
CAPS_DIR = ROOT / "caps"
GBT_DIR = ROOT / ".gbt"
SCREENSHOTS_DIR = GBT_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


# ── 统一视觉引擎 · 多层回退 ──────────────

def _screenshot(region=None):
    """截屏 — 三层回退: pyautogui → mss → screenshot cap子进程
    返回 (PIL.Image | None, method: str, error: str | None)
    """
    # 规范化region格式: {"x","y","w","h"} → (left, top, width, height)
    py_region = None
    mss_region = None
    if region:
        left = region.get("left", region.get("x", 0))
        top = region.get("top", region.get("y", 0))
        width = region.get("width", region.get("w", 1920))
        height = region.get("height", region.get("h", 1080))
        py_region = (left, top, width, height)
        mss_region = {"left": left, "top": top, "width": width, "height": height}

    # Layer 1: pyautogui (本地直接截图)
    try:
        import pyautogui
        img = pyautogui.screenshot(region=py_region) if py_region else pyautogui.screenshot()
        if img is not None:
            return img, "pyautogui", None
    except Exception as e:
        pass

    # Layer 2: mss + PIL (原生截屏库)
    try:
        import mss
        from PIL import Image
        with mss.mss() as sct:
            if mss_region:
                sct_img = sct.grab(mss_region)
            else:
                sct_img = sct.grab(sct.monitors[0])
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            return img, "mss", None
    except Exception as e:
        pass

    # Layer 3: 子进程调用 caps/screenshot/run.py
    try:
        action = "capture_region" if region else "capture"
        params_json = json.dumps(region or {}, ensure_ascii=False)
        r = subprocess.run(
            [sys.executable, str(CAPS_DIR / "screenshot" / "run.py"), action, params_json],
            capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace"
        )
        if r.returncode == 0 and r.stdout.strip():
            data = json.loads(r.stdout)
            if data.get("ok") and data.get("base64"):
                from PIL import Image as PILImage
                img_bytes = base64.b64decode(data["base64"])
                img = PILImage.open(io.BytesIO(img_bytes))
                return img, "screenshot_cap", None
    except Exception:
        pass

    return None, "unavailable", "桌面不可用: 所有截图方式均失败 (pyautogui/mss/子进程)"


def _ocr(img):
    """OCR — 三层回退: pytesseract → easyocr → screen_ocr cap子进程
    返回 (blocks: list, method: str, error: str | None)
    blocks: [{"text": str, "confidence": float, "rect": {"left","top","width","height"}}, ...]
    """
    # Layer 1: pytesseract (直连OCR引擎)
    try:
        import pytesseract
        # 尝试获取详细数据(含位置)
        data = pytesseract.image_to_data(img, lang="chi_sim+eng", output_type=pytesseract.Output.DICT)
        blocks = []
        for i in range(len(data["text"])):
            txt = data["text"][i].strip()
            if txt and int(data["conf"][i]) > 0:
                blocks.append({
                    "text": txt,
                    "confidence": int(data["conf"][i]),
                    "rect": {
                        "left": data["left"][i],
                        "top": data["top"][i],
                        "width": data["width"][i],
                        "height": data["height"][i],
                    }
                })
        if blocks:
            return blocks, "pytesseract", None
    except Exception:
        pass

    # Layer 2: easyocr (深度学习OCR)
    try:
        import easyocr
        reader = easyocr.Reader(["ch_sim", "en"], gpu=False)
        results = reader.readtext(img_array(img), detail=1)
        blocks = []
        for (bbox, text, conf) in results:
            # bbox: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
            left = int(min(p[0] for p in bbox))
            top = int(min(p[1] for p in bbox))
            width = int(max(p[0] for p in bbox) - left)
            height = int(max(p[1] for p in bbox) - top)
            blocks.append({
                "text": text,
                "confidence": round(float(conf) * 100, 1),
                "rect": {"left": left, "top": top, "width": width, "height": height},
            })
        if blocks:
            return blocks, "easyocr", None
    except Exception:
        pass

    # Layer 3: 子进程调用 caps/screen_ocr/run.py
    try:
        # 先保存图片到临时文件, 因为screen_ocr自己会截图
        # 这里我们直接用子进程的全屏OCR能力
        params_json = json.dumps({"lang": "chi_sim+eng", "psm": 3}, ensure_ascii=False)
        r = subprocess.run(
            [sys.executable, str(CAPS_DIR / "screen_ocr" / "run.py"), "read_all", params_json],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace"
        )
        if r.returncode == 0 and r.stdout.strip():
            data = json.loads(r.stdout)
            if data.get("ok") and data.get("blocks"):
                return data["blocks"], "screen_ocr_cap", None
    except Exception:
        pass

    return [], "unavailable", "OCR不可用: 所有OCR方式均失败 (pytesseract/easyocr/子进程)"


def _img_array(img):
    """PIL Image → numpy array (for easyocr)"""
    try:
        import numpy as np
        return np.array(img)
    except ImportError:
        return img


def img_array(img):
    """module-level alias for easyocr"""
    return _img_array(img)
HANDLERS = {}


def _reg(name):
    def dec(fn):
        HANDLERS[name] = fn
        return fn
    return dec


@_reg("see")
def do_see(params):
    """看屏幕 — 返回base64图片"""
    region = None
    if params and any(k in params for k in ("x", "y", "w", "h")):
        region = {"x": params.get("x", 0), "y": params.get("y", 0),
                  "w": params.get("w", 1920), "h": params.get("h", 1080)}
    return eyes.see(region)


@_reg("read")
def do_read(params):
    """OCR读屏幕文字"""
    x = params.get("x", 0) if params else 0
    y = params.get("y", 0) if params else 0
    w = params.get("w", 1920) if params else 1920
    h = params.get("h", 1080) if params else 1080
    return eyes.read(x, y, w, h)


@_reg("read_all")
def do_read_all(params):
    """OCR读全屏"""
    return eyes.read_all()


@_reg("find")
def do_find(params):
    """在屏幕上找文字, 返回坐标"""
    text = params.get("text", "") if params else ""
    pos = eyes.find(text)
    if pos:
        return {"ok": True, "text": text, "position": list(pos)}
    return {"ok": False, "error": f"未找到: {text}"}


@_reg("find_all")
def do_find_all(params):
    """找所有匹配位置"""
    text = params.get("text", "") if params else ""
    positions = eyes.find_all(text)
    return {"ok": True, "text": text, "positions": [list(p) for p in positions],
            "count": len(positions)}


@_reg("analyze")
def do_analyze(params):
    """AI视觉分析 — 截图+理解"""
    question = params.get("question", "屏幕上有什么?") if params else "屏幕上有什么?"
    return eyes.analyze(question)


@_reg("wait_for")
def do_wait_for(params):
    """等待屏幕上出现指定文字"""
    text = params.get("text", "") if params else ""
    timeout = params.get("timeout", 30.0) if params else 30.0
    pos = eyes.wait_for(text, timeout)
    if pos:
        return {"ok": True, "text": text, "position": list(pos)}
    return {"ok": False, "error": f"超时未找到: {text}"}


@_reg("wait_until_gone")
def do_wait_until_gone(params):
    """等待文字消失"""
    text = params.get("text", "") if params else ""
    timeout = params.get("timeout", 30.0) if params else 30.0
    gone = eyes.wait_until_gone(text, timeout)
    return {"ok": True, "text": text, "gone": gone}


@_reg("colors_at")
def do_colors_at(params):
    """获取屏幕某点颜色"""
    x = params.get("x", 0) if params else 0
    y = params.get("y", 0) if params else 0
    return eyes.colors_at(x, y)


@_reg("compare")
def do_compare(params):
    """比较两个区域差异 (像素级hash)"""
    r1 = params.get("region1", {}) if params else {}
    r2 = params.get("region2", {}) if params else {}
    return eyes.compare(r1, r2)


@_reg("to_image")
def do_to_image(params):
    """保存截图为PNG"""
    filepath = params.get("filepath", None) if params else None
    return eyes.to_image(filepath)


@_reg("to_annotated")
def do_to_annotated(params):
    """截图+标注所有文字"""
    filepath = params.get("filepath", None) if params else None
    return eyes.to_annotated(filepath)


# ── 手部操作 ────────────────────────────

@_reg("move")
def do_move(params):
    """移动鼠标"""
    x = params.get("x", 0)
    y = params.get("y", 0)
    return hands.move(x, y)


@_reg("click")
def do_click(params):
    """左键点击"""
    x = params.get("x", 0)
    y = params.get("y", 0)
    return hands.click(x, y)


@_reg("double_click")
def do_double_click(params):
    """双击"""
    x = params.get("x", 0)
    y = params.get("y", 0)
    return hands.double_click(x, y)


@_reg("right_click")
def do_right_click(params):
    """右键点击"""
    x = params.get("x", 0)
    y = params.get("y", 0)
    return hands.right_click(x, y)


@_reg("type")
def do_type(params):
    """键盘输入"""
    text = params.get("text", "")
    return hands.type(text)


@_reg("press")
def do_press(params):
    """按键"""
    key = params.get("key", "")
    return hands.press(key)


@_reg("hotkey")
def do_hotkey(params):
    """组合键"""
    keys = params.get("keys", [])
    return hands.hotkey(*keys)


@_reg("drag")
def do_drag(params):
    """拖拽"""
    x1 = params.get("x1", 0)
    y1 = params.get("y1", 0)
    x2 = params.get("x2", 0)
    y2 = params.get("y2", 0)
    return hands.drag(x1, y1, x2, y2)


@_reg("scroll")
def do_scroll(params):
    """滚轮"""
    amount = params.get("amount", 1)
    return hands.scroll(amount)


@_reg("move_to_text")
def do_move_to_text(params):
    """找到文字→移动→点击"""
    text = params.get("text", "")
    timeout = params.get("timeout", 10.0)
    return hands.move_to_text(text, timeout)


@_reg("type_and_enter")
def do_type_and_enter(params):
    """输入+回车"""
    text = params.get("text", "")
    return hands.type_and_enter(text)


@_reg("select_all_copy")
def do_select_all_copy(params):
    """全选复制"""
    return hands.select_all_copy()


@_reg("paste")
def do_paste(params):
    """粘贴"""
    return hands.paste()


@_reg("screenshot_region")
def do_screenshot_region(params):
    """截取屏幕区域"""
    x = params.get("x", 0)
    y = params.get("y", 0)
    w = params.get("w", 1920)
    h = params.get("h", 1080)
    return hands.screenshot_region(x, y, w, h)


# ── 后台视觉 · 人类级并行 ────────────────

@_reg("start_watching")
def do_start_watching(params):
    """开启后台持续视觉 — 此后latest/wait_for_async即时可用"""
    fps = params.get("fps", 30) if params else 30
    return eyes.start_watching(fps)


@_reg("stop_watching")
def do_stop_watching(params):
    """停止后台视觉"""
    return eyes.stop_watching()



@_reg("look_deep")
def do_look_deep(params):
    """深度视觉 — 多通道增强: OCR+4x超分+AI兜底, 专治远程桌面模糊"""
    x = params.get("x", 0) if params else 0
    y = params.get("y", 0) if params else 0
    w = params.get("w", 1920) if params else 1920
    h = params.get("h", 1080) if params else 1080
    return eyes.look_deep(x, y, w, h)

@_reg("latest")
def do_latest(params):
    """取最新帧 — 零阻塞"""
    return eyes.latest


@_reg("buffer_stats")
def do_buffer_stats(params):
    """帧缓冲状态"""
    return eyes.buffer_stats


@_reg("wait_for_async")
def do_wait_for_async(params):
    """等待文字出现 — 非阻塞, 手可同时操作"""
    text = params.get("text", "") if params else ""
    timeout = params.get("timeout", 30.0) if params else 30.0
    pos = eyes.wait_for_async(text, timeout)
    if pos:
        return {"ok": True, "text": text, "position": list(pos)}
    return {"ok": False, "error": f"\u8d85\u65f6\u672a\u627e\u5230: {text}"}


# ── 复合操作 ────────────────────────────

@_reg("look_and_click")
def do_look_and_click(params):
    """看→找→点: 一站式, 手眼并行
    {"text":"登录按钮"} → 自动找文字, 移动过去, 点击
    """
    text = params.get("text", "")
    timeout = params.get("timeout", 10.0)
    return hands.look_and_click(text, timeout)


@_reg("look_and_type")
def do_look_and_type(params):
    """找输入框→点击→输入: 一站式"""
    text = params.get("text", "")
    input_text = params.get("input_text", "")
    timeout = params.get("timeout", 10.0)
    return hands.look_and_type(text, input_text, timeout)



# ── 浏览原语 · 刷抖音/朋友圈 ──────────────

@_reg("wait_for_stable")
def do_wait_for_stable(params):
    """等待屏幕稳定 — 滚动后等新内容加载完"""
    timeout = params.get("timeout", 5.0) if params else 5.0
    return eyes.wait_for_stable(timeout)


@_reg("browse_screen")
def do_browse_screen(params):
    """看当前屏+AI分析"""
    question = params.get("question", "这是什么内容?") if params else "这是什么内容?"
    return eyes.browse_screen(question)


@_reg("browse_scroll")
def do_browse_scroll(params):
    """浏览: 滚→等稳定→看→AI理解"""
    direction = params.get("direction", "down")
    amount = params.get("amount", 3)
    question = params.get("question", "这是什么内容?")
    return hands.browse_scroll(direction, amount, question)


@_reg("browse_feed")
def do_browse_feed(params):
    """连续刷feed — 抖音/朋友圈/微博"""
    count = params.get("count", 10)
    direction = params.get("direction", "down")
    question = params.get("question", "这是什么内容? 简要描述")
    pause_on = params.get("pause_on", None)
    return hands.browse_feed(count, direction, question, pause_on)


@_reg("browse_and_interact")
def do_browse_and_interact(params):
    """浏览并互动 — 刷到内容→找互动入口→操作"""
    scroll_count = params.get("scroll_count", 5)
    interact_text = params.get("interact_text", "评论")
    action = params.get("action", "click")
    return hands.browse_and_interact(scroll_count, interact_text, action)


# ── 电影模式 ────────────────────────────

@_reg("movie")
def do_movie(params):
    """电影模式 — 高速连续采集+场景检测
    {"duration":10,"fps":30,"detect_scenes":true}
    """
    duration = params.get("duration", 10.0)
    fps = params.get("fps", 30)
    detect = params.get("detect_scenes", True)
    return eyes.movie(duration, int(fps), detect)


@_reg("movie_record")
def do_movie_record(params):
    """录制屏幕视频
    {"duration":10,"fps":30,"output":"path/to/file.mp4"}
    """
    duration = params.get("duration", 10.0)
    fps = params.get("fps", 30)
    output = params.get("output", None)
    return eyes.movie_record(duration, int(fps), output)


@_reg("movie_analyze")
def do_movie_analyze(params):
    """看电影+AI理解 — 采集→场景检测→关键帧AI分析
    {"duration":5,"fps":5,"question":"屏幕上在发生什么?"}
    """
    duration = params.get("duration", 5.0)
    fps = params.get("fps", 5)
    question = params.get("question", "屏幕上在发生什么?")
    return eyes.movie_analyze(duration, int(fps), question)

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "see"
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except:
            pass
    handler = HANDLERS.get(action)
    if handler:
        result = handler(params)
    else:
        result = {"ok": False, "error": f"未知action: {action}",
                  "available": list(HANDLERS.keys())}
    print(json.dumps(result, ensure_ascii=False, default=str))
