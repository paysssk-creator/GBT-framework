# 开发者：自由的风
"""screenshot/run.py — 屏幕截图·邻域视觉第一层
============================================
感知域 core — 直接捕捉屏幕画面，返回base64编码PNG。
不经过任何外部视觉模型——这是GBT自己的眼睛。
"""
import sys, json, os, base64, io
from datetime import datetime

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(os.path.dirname(SANDBOX), ".gbt", "screenshots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

try:
    import mss
    import mss.tools
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def _capture_raw(monitor=0, region=None):
    """底层截图 — 返回PIL Image"""
    if not HAS_MSS:
        return None, "mss 未安装 (pip install mss)"

    with mss.mss() as sct:
        if region:
            # region: {"left": x, "top": y, "width": w, "height": h}
            img = sct.grab(region)
        else:
            # monitor 0 = all monitors combined, 1 = primary
            if isinstance(monitor, int) and monitor > 0 and monitor <= len(sct.monitors):
                img = sct.grab(sct.monitors[monitor])
            else:
                img = sct.grab(sct.monitors[0])

        if HAS_PIL:
            return Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX"), None
        else:
            return img, None


def _to_base64(pil_img, format="PNG"):
    """PIL Image → base64 string"""
    buf = io.BytesIO()
    pil_img.save(buf, format=format)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def do_capture(params):
    """截取屏幕 → 返回base64画面"""
    monitor = params.get("monitor", 0)
    save = params.get("save", False)
    quality = params.get("quality", 80)

    img, err = _capture_raw(monitor=monitor)
    if err:
        return {"ok": False, "error": err}

    w, h = img.size
    b64 = _to_base64(img, format="JPEG" if quality < 100 else "PNG")

    result = {
        "ok": True,
        "cap": "screenshot",
        "action": "capture",
        "domain": "感知域",
        "width": w, "height": h,
        "size_bytes": len(b64),
        "timestamp": datetime.now().isoformat(),
        "image_base64": b64,
    }

    if save:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"screen_{ts}.png"
        fpath = os.path.join(OUTPUT_DIR, fname)
        img.save(fpath)
        result["saved"] = fpath

    return result


def do_capture_region(params):
    """截取指定区域"""
    region = {
        "left": params.get("left", 0),
        "top": params.get("top", 0),
        "width": params.get("width", 1920),
        "height": params.get("height", 1080),
    }
    save = params.get("save", False)

    img, err = _capture_raw(region=region)
    if err:
        return {"ok": False, "error": err}

    w, h = img.size
    b64 = _to_base64(img)

    result = {
        "ok": True,
        "cap": "screenshot",
        "action": "capture_region",
        "domain": "感知域",
        "region": region,
        "width": w, "height": h,
        "size_bytes": len(b64),
        "timestamp": datetime.now().isoformat(),
        "image_base64": b64,
    }

    if save:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"region_{ts}.png"
        fpath = os.path.join(OUTPUT_DIR, fname)
        img.save(fpath)
        result["saved"] = fpath

    return result


HANDLERS = {"capture": do_capture, "capture_region": do_capture_region}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "capture"
    params_str = sys.argv[2] if len(sys.argv) > 2 else "{}"
    try:
        params = json.loads(params_str)
    except Exception:
        params = {}
    handler = HANDLERS.get(action)
    if handler:
        result = handler(params)
        # 截断base64以免输出太长
        if "image_base64" in result and len(result["image_base64"]) > 200:
            result["image_base64"] = result["image_base64"][:200] + f"...[截断, 总长{len(result['image_base64'])}]"
        print(json.dumps(result, ensure_ascii=False, default=str))
    else:
        print(json.dumps({"ok": False, "error": f"未知动作: {action}", "available": list(HANDLERS.keys())}, ensure_ascii=False))
