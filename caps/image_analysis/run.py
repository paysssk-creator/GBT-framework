# 开发者：自由的风
"""
image_analysis/run.py — 图片分析域
===================================
整合现有的图片分析能力(ai_vision/local_eye/screen_ocr)
+ 新增分类/综合分析功能。

底层引擎: Florence-2 (ai_vision) + EasyOCR (local_eye) + LLM推理
"""

import sys, json, os, base64, logging, urllib.request, urllib.error
from pathlib import Path
from typing import Optional

L = logging.getLogger("ImageAnalysis")
SANDBOX_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SANDBOX_DIR))

def _call_llm(messages, max_tokens=2000, temperature=0.7, timeout=60):
    """Local LLM call via DEEPSEEK_API_KEY or KIMI_API_KEY. Returns text or None."""
    api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("KIMI_API_KEY") or ""
    if not api_key:
        return None
    base_url = os.environ.get("GBT_LLM_BASE_URL", "https://api.deepseek.com")
    model = os.environ.get("GBT_LLM_MODEL", "deepseek-chat")
    url = f"{base_url.rstrip('/')}/chat/completions"
    body = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception:
        return None


def _read_image(params: dict) -> Optional[bytes]:
    """从参数中读取图片数据"""
    # 方式1: base64
    b64 = params.get("image_b64", params.get("base64", ""))
    if b64:
        try:
            return base64.b64decode(b64)
        except Exception:
            pass

    # 方式2: 文件路径
    path = params.get("path", params.get("image_path", params.get("file", "")))
    if path:
        p = Path(path)
        if p.exists():
            return p.read_bytes()

    # 方式3: URL
    url = params.get("url", "")
    if url:
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": "GBT/3.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read()
        except Exception as e:
            L.warning(f"URL加载失败: {e}")

    return None


def do_describe(params: dict = None) -> dict:
    """深度描述图片内容"""
    if params is None:
        params = {}
    img_data = _read_image(params)
    if not img_data:
        return {"ok": False, "error": "未提供图片数据。需要 image_b64/path/url 之一"}

    # 优先使用 ai_vision (Florence-2)
    try:
        from capability_protocol import get_engine
        engine = get_engine()
        result = engine.call("ai_vision", "describe", {"image_b64": base64.b64encode(img_data).decode()})
        if result.get("ok"):
            return {"ok": True, "engine": "florence-2", **result}
    except Exception as e:
        L.debug(f"ai_vision不可用: {e}")

    # 降级: local_eye
    try:
        from capability_protocol import get_engine
        engine = get_engine()
        # 保存临时文件
        tmp = SANDBOX_DIR / "_tmp_image.png"
        tmp.write_bytes(img_data)
        result = engine.call("local_eye", "describe", {"path": str(tmp)})
        tmp.unlink(missing_ok=True)
        if result.get("ok"):
            return {"ok": True, "engine": "local_eye", **result}
    except Exception as e:
        L.debug(f"local_eye不可用: {e}")

    # 最终降级: LLM视觉
    try:
        b64 = base64.b64encode(img_data).decode()
        prompt = f"请用中文详细描述这张图片的内容。图片数据(base64): {b64[:100]}...[截断]"
        desc = _call_llm([{"role": "user", "content": prompt}], max_tokens=300)
        if desc:
            return {"ok": True, "engine": "llm", "description": desc}
    except Exception:
        pass

    return {"ok": False, "error": "所有图片分析引擎不可用"}


def do_ocr(params: dict = None) -> dict:
    """图片文字识别"""
    if params is None:
        params = {}
    img_data = _read_image(params)
    if not img_data:
        return {"ok": False, "error": "未提供图片数据"}

    # 优先 screen_ocr + local_eye
    for cap_name in ["screen_ocr", "local_eye"]:
        try:
            from capability_protocol import get_engine
            engine = get_engine()
            tmp = SANDBOX_DIR / "_tmp_ocr.png"
            tmp.write_bytes(img_data)
            result = engine.call(cap_name, "read" if cap_name == "screen_ocr" else "ocr",
                                {"path": str(tmp)})
            tmp.unlink(missing_ok=True)
            if result.get("ok"):
                return {"ok": True, "engine": cap_name, **result}
        except Exception:
            pass

    # 降级: ai_vision OCR
    try:
        from capability_protocol import get_engine
        engine = get_engine()
        result = engine.call("ai_vision", "ocr", {"image_b64": base64.b64encode(img_data).decode()})
        if result.get("ok"):
            return {"ok": True, "engine": "florence-ocr", **result}
    except Exception:
        pass

    return {"ok": False, "error": "OCR引擎不可用"}


def do_classify(params: dict = None) -> dict:
    """图片分类"""
    if params is None:
        params = {}
    img_data = _read_image(params)
    if not img_data:
        return {"ok": False, "error": "未提供图片数据"}

    # 用LLM做分类
    try:
        b64 = base64.b64encode(img_data).decode()
        prompt = f"""分析这张图片并分类。返回JSON格式:
{{"category": "场景/物体/人物/文档/截屏/代码/其他",
  "subcategory": "具体子类",
  "style": "写实/插画/图表/照片/合成",
  "dominant_colors": ["颜色1","颜色2"],
  "confidence": 0.0-1.0}}
只输出JSON。图片(base64): {b64[:200]}...[截断]"""
        reply = _call_llm([{"role": "user", "content": prompt}], max_tokens=300)
        if reply:
            try:
                result = json.loads(reply)
                return {"ok": True, "engine": "llm", **result}
            except json.JSONDecodeError:
                return {"ok": True, "engine": "llm", "classification": reply[:300]}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

    return {"ok": False, "error": "分类引擎不可用"}


def do_analyze(params: dict = None) -> dict:
    """综合分析: 描述+OCR+分类+颜色+构图"""
    if params is None:
        params = {}

    result = {"ok": True, "engine": "composite"}

    # 并行获取各项分析
    desc_result = do_describe(params)
    result["description"] = desc_result.get("description", desc_result.get("error", ""))

    ocr_result = do_ocr(params)
    result["text"] = ocr_result.get("text", ocr_result.get("data", ""))

    classify_result = do_classify(params)
    if classify_result.get("ok"):
        result["category"] = classify_result.get("category", "")
        result["subcategory"] = classify_result.get("subcategory", "")
        result["style"] = classify_result.get("style", "")
        result["dominant_colors"] = classify_result.get("dominant_colors", [])
        result["confidence"] = classify_result.get("confidence", 0)

    return result

def do_to_code(params: dict = None) -> dict:
    """
    图片→代码 — 一步到位。不截图、不OCR、不分步。
    任意图片(设计稿/手绘/截屏/mockup) → 可运行代码。
    """
    if params is None:
        params = {}
    img_data = _read_image(params)
    if not img_data:
        return {"ok": False, "error": "未提供图片数据"}

    target_lang = params.get("lang", params.get("language", "html"))
    framework = params.get("framework", "")
    b64 = base64.b64encode(img_data).decode()
    mime = params.get("mime", "image/png")
    size_kb = round(len(img_data) / 1024, 1)

    # 用视觉LLM直接理解图片内容
    framework_hint = f"使用{framework}框架。" if framework else ""
    prompt = (
        f"将这张图片精确转换为{target_lang}代码。{framework_hint}"
        f"像素级还原布局、颜色、字体、间距。所有交互元素可操作。响应式设计。只输出代码。"
    )

    try:
        # 构造视觉消息 — 图片+文本一起发送
        messages = [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                {"type": "text", "text": prompt},
            ]
        }]
        code = _call_llm(messages, max_tokens=4096, temperature=0.2)
        if code:
            return {
                "ok": True,
                "engine": "vision-llm",
                "language": target_lang,
                "framework": framework,
                "image_size_kb": size_kb,
                "code": code,
                "code_length": len(code),
            }
    except Exception as e:
        # 降级: 文本LLM + 图片描述
        try:
            desc = do_describe(params)
            if desc.get("ok"):
                text_prompt = (
                    f"基于以下图片描述生成{target_lang}代码。{framework_hint}"
                    f"图片描述: {desc.get('description', '')}"
                    f"\n像素级还原。只输出代码。"
                )
                code = _call_llm([{"role": "user", "content": text_prompt}], max_tokens=4096, temperature=0.2)
                if code:
                    return {"ok": True, "engine": "text-llm(fallback)", "language": target_lang,
                            "code": code, "code_length": len(code), "fallback": True}
        except Exception:
            pass
        return {"ok": False, "error": str(e)[:200] if isinstance(e, Exception) else "代码生成失败"}

    return {"ok": False, "error": "代码生成引擎不可用"}


HANDLERS = {
    "describe": do_describe,
    "ocr": do_ocr,
    "classify": do_classify,
    "analyze": do_analyze,
    "to_code": do_to_code,
}


if __name__ == "__main__":
    action = sys.argv[1].lstrip("-") if len(sys.argv) > 1 and sys.argv[1] != "run.py" else "describe"

    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except json.JSONDecodeError:
            pass

    try:
        stdin_data = sys.stdin.read().strip()
        if stdin_data:
            params = {**json.loads(stdin_data), **params}
    except (json.JSONDecodeError, Exception):
        pass

    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知: {action}", "available": list(HANDLERS.keys())})
    result = h(params)
    print(json.dumps(result, ensure_ascii=False, default=str))
