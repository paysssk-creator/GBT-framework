# 开发者：自由的风
"""ai_vision/run.py — Kimi Vision + Florence-2 双引擎
=====================================================
主引擎: Kimi Vision API (deepseek-v4-vision-preview, 已验证可用)
备用: Florence-2 (本地CPU, 离线)
能力: OCR + 图片描述 + 物体检测 + 截图理解
"""
import sys, json, os, io, base64, urllib.request
from pathlib import Path

KIMI_URL = "https://api.moonshot.cn/v1/chat/completions"
KIMI_MODEL = "moonshot-v1-8k-vision-preview"
FLORENCE_ID = "microsoft/Florence-2-base"

# ═══════════════════ Kimi Vision (主力) ═══════════════════

def _kimi_vision(image, prompt):
    api_key = os.environ.get("MOONSHOT_API_KEY") or os.environ.get("KIMI_API_KEY", "")
    if not api_key:
        raise RuntimeError("MOONSHOT_API_KEY 未设置")

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    payload = json.dumps({
        "model": KIMI_MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
            ]
        }],
        "max_tokens": 1024,
        "temperature": 0.0,
    }).encode()

    req = urllib.request.Request(KIMI_URL, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"]

# ═══════════════════ Florence-2 (备用) ═══════════════════

_model = None
_processor = None

def _load_florence():
    global _model, _processor
    if _model is not None: return
    from transformers import AutoProcessor, AutoModelForCausalLM
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    _model = AutoModelForCausalLM.from_pretrained(
        FLORENCE_ID, trust_remote_code=True, torch_dtype=torch.float32).to(device)
    _processor = AutoProcessor.from_pretrained(FLORENCE_ID, trust_remote_code=True)

def _image_from_source(source):
    from PIL import Image
    if isinstance(source, str) and os.path.isfile(source):
        return Image.open(source).convert("RGB")
    try:
        return Image.open(io.BytesIO(base64.b64decode(source))).convert("RGB")
    except Exception:
        raise ValueError("无法读取图像")

def _florence_run(image, task):
    _load_florence()
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    inputs = _processor(text=task, images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        ids = _model.generate(input_ids=inputs["input_ids"],
                              pixel_values=inputs["pixel_values"],
                              max_new_tokens=512, do_sample=False)
    text = _processor.batch_decode(ids, skip_special_tokens=False)[0]
    return _processor.post_process_generation(text, task=task,
                image_size=(image.width, image.height))

# ═══════════════════ 统一入口 ═══════════════════

def do_ocr(params):
    source = params.get('image', params.get('path', ''))
    if not source: return {"ok": False, "error": "缺少image参数"}
    image = _image_from_source(source)

    try:
        text = _kimi_vision(image, "请精确识别并输出这张图片中的所有文字内容，不要添加任何解释，只输出文字。")
        return {"ok": True, "text": text, "engine": "kimi-vision", "w": image.width, "h": image.height}
    except Exception:
        pass

    try:
        r = _florence_run(image, "<OCR>")
        return {"ok": True, "text": str(r.get("<OCR>","")), "engine": "florence-2", "w": image.width, "h": image.height}
    except Exception as e:
        return {"ok": False, "error": f"OCR失败: {e}"}

def do_describe(params):
    source = params.get('image', params.get('path', ''))
    detail = params.get('detail', 'detailed')
    if not source: return {"ok": False, "error": "缺少image参数"}
    image = _image_from_source(source)

    try:
        prompt = "请详细描述这张图片的内容，包括所有可见元素、布局、文字、颜色和上下文。" if detail == "detailed" else "请简要描述这张图片。"
        desc = _kimi_vision(image, prompt)
        return {"ok": True, "description": desc, "engine": "kimi-vision", "detail": detail}
    except Exception:
        pass

    try:
        task = "<MORE_DETAILED_CAPTION>" if detail == "detailed" else "<DETAILED_CAPTION>"
        r = _florence_run(image, task)
        return {"ok": True, "description": str(r.get(task,"")), "engine": "florence-2", "detail": detail}
    except Exception as e:
        return {"ok": False, "error": f"描述失败: {e}"}

def do_screen(params):
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
    except ImportError:
        return {"ok": False, "error": "PIL不可用"}

    detail = params.get('detail', 'detailed')

    try:
        prompt = """请完整分析这张屏幕截图:
1. 列出所有可见的文字内容（逐行）
2. 描述当前显示的应用程序/窗口
3. 指出任何异常、错误信息或警告
4. 总结屏幕上的主要内容和状态"""
        analysis = _kimi_vision(img, prompt)
        return {"ok": True, "engine": "kimi-vision",
                "screen_size": f"{img.width}x{img.height}", "analysis": analysis}
    except Exception:
        pass

    try:
        ocr = _florence_run(img, "<OCR>")
        cap = _florence_run(img, "<MORE_DETAILED_CAPTION>")
        return {"ok": True, "engine": "florence-2",
                "screen_size": f"{img.width}x{img.height}",
                "ocr_text": str(ocr.get("<OCR>",""))[:2000],
                "description": str(cap.get("<MORE_DETAILED_CAPTION>",""))}
    except Exception as e:
        return {"ok": False, "error": f"分析失败: {e}"}


handlers = {'ocr': do_ocr, 'describe': do_describe, 'screen': do_screen}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 else "ocr"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = handlers.get(action, lambda p: {"ok": False, "error": f"未知动作: {action}", "available": list(handlers.keys())})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
