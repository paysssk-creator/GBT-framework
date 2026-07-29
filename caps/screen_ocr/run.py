# 开发者：自由的风
"""screen_ocr/run.py — 屏幕文字直接识别，不经过视觉模型
====================================================
感知域 core — 截图+Tesseract OCR，直接读屏幕上的文字。
不依赖Kimi Vision/Florence-2/GLM-4V等外部视觉模型。
"""
import sys, json, os

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False


def _capture_region(region=None):
    """截取屏幕区域 → PIL Image"""
    if not HAS_MSS:
        return None, "mss 未安装 (pip install mss)"
    if not HAS_PIL:
        return None, "Pillow 未安装 (pip install Pillow)"

    with mss.mss() as sct:
        if region:
            img = sct.grab(region)
        else:
            img = sct.grab(sct.monitors[0])
        return Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX"), None


def do_read(params):
    """读取屏幕指定区域文字"""
    if not HAS_TESSERACT:
        return {"ok": False, "error": "pytesseract 未安装 (pip install pytesseract; 需安装Tesseract-OCR)",
                "available_actions": ["read", "read_all"]}

    region = None
    if "left" in params:
        region = {
            "left": params.get("left", 0),
            "top": params.get("top", 0),
            "width": params.get("width", 800),
            "height": params.get("height", 600),
        }

    lang = params.get("lang", "chi_sim+eng")
    psm = params.get("psm", 3)  # 3 = fully automatic page segmentation

    img, err = _capture_region(region)
    if err:
        return {"ok": False, "error": err}

    try:
        text = pytesseract.image_to_string(img, lang=lang, config=f"--psm {psm}")
        # 也获取带位置信息的结果
        data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)
    except Exception as e:
        return {"ok": False, "error": f"OCR失败: {e}"}

    # 提取有效的文字块
    text_blocks = []
    for i in range(len(data["text"])):
        txt = data["text"][i].strip()
        if txt and data["conf"][i] > 0:
            text_blocks.append({
                "text": txt,
                "confidence": data["conf"][i],
                "rect": {
                    "left": data["left"][i],
                    "top": data["top"][i],
                    "width": data["width"][i],
                    "height": data["height"][i],
                }
            })

    return {
        "ok": True,
        "cap": "screen_ocr",
        "action": "read",
        "domain": "感知域",
        "text": text.strip(),
        "line_count": len(text.strip().split("\n")) if text else 0,
        "blocks": text_blocks[:100],
        "block_count": len(text_blocks),
        "region": region,
        "lang": lang,
    }


def do_read_all(params):
    """读取全屏文字"""
    lang = params.get("lang", "chi_sim+eng")
    return do_read({"lang": lang, "psm": params.get("psm", 3)})


HANDLERS = {"read": do_read, "read_all": do_read_all}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "read_all"
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
