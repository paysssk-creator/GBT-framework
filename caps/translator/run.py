# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""translator/run.py — DeepL + LibreTranslate 双引擎翻译
========================================================
DeepL API (DEEPL_API_KEY) → LibreTranslate (LIBRETRANSLATE_URL) 自动回退
动作: translate · detect_language · list_languages
"""
import sys, json, os, urllib.request

DEEPL_KEY = os.environ.get("DEEPL_API_KEY", "")
LT_URL   = os.environ.get("LIBRETRANSLATE_URL", "").rstrip("/")

def _req(method, url, payload=None, headers=None):
    """HTTP JSON request helper."""
    hdrs = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers: hdrs.update(headers)
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        return e.code, {"error": body[:300]}
    except Exception as e:
        return 0, {"error": str(e)[:200]}

# ── DeepL ──────────────────────────────────────────────────────────

def _dl_base():
    return "https://api-free.deepl.com/v2" if DEEPL_KEY.endswith(":fx") else "https://api.deepl.com/v2"

def _dl_headers():
    return {"Authorization": f"DeepL-Auth-Key {DEEPL_KEY}"}

def _dl_translate(params):
    text = params.get("text") or params.get("q", "")
    target = params.get("target_lang") or params.get("target", "EN")
    payload = {"text": [text], "target_lang": target.upper()}
    src = params.get("source_lang") or params.get("source")
    if src: payload["source_lang"] = src.upper()
    st, body = _req("POST", f"{_dl_base()}/translate", payload, _dl_headers())
    if st == 200 and "translations" in body:
        t = body["translations"][0]
        return {"ok": True, "engine": "deepl", "text": t["text"],
                "source_lang": t.get("detected_source_language", src or ""), "target_lang": target.upper()}
    return {"ok": False, "engine": "deepl", "error": body.get("error", body.get("message", str(body)))[:200]}

def _dl_detect(params):
    text = params.get("text") or params.get("q", "")
    st, body = _req("POST", f"{_dl_base()}/translate",
                     {"text": [text], "target_lang": "EN"}, _dl_headers())
    if st == 200 and "translations" in body:
        lang = body["translations"][0].get("detected_source_language", "")
        return {"ok": True, "engine": "deepl", "language": lang, "confidence": 1.0}
    return {"ok": False, "engine": "deepl", "error": body.get("error", body.get("message", str(body)))[:200]}

def _dl_languages(params):
    st, body = _req("GET", f"{_dl_base()}/languages?type={params.get('type', 'target')}")
    if st == 200 and isinstance(body, list):
        langs = [{"code": l["language"], "name": l["name"]} for l in body]
        return {"ok": True, "engine": "deepl", "languages": langs, "count": len(langs)}
    return {"ok": False, "engine": "deepl", "error": body.get("error", str(body))[:200]}

# ── LibreTranslate ─────────────────────────────────────────────────

def _lt_translate(params):
    payload = {"q": params.get("text") or params.get("q", ""),
               "source": params.get("source_lang") or params.get("source", "auto"),
               "target": params.get("target_lang") or params.get("target", "en"),
               "format": "text"}
    st, body = _req("POST", f"{LT_URL}/translate", payload)
    if st == 200 and "translatedText" in body:
        return {"ok": True, "engine": "libretranslate", "text": body["translatedText"],
                "source_lang": body.get("detectedLanguage", {}).get("language", payload["source"]),
                "target_lang": payload["target"]}
    return {"ok": False, "engine": "libretranslate", "error": body.get("error", str(body))[:200]}

def _lt_detect(params):
    st, body = _req("POST", f"{LT_URL}/detect",
                    {"q": params.get("text") or params.get("q", "")})
    if st == 200 and isinstance(body, list) and body:
        r = body[0]
        return {"ok": True, "engine": "libretranslate",
                "language": r.get("language", ""), "confidence": r.get("confidence", 0)}
    return {"ok": False, "engine": "libretranslate", "error": body.get("error", str(body))[:200]}

def _lt_languages(params):
    st, body = _req("GET", f"{LT_URL}/languages")
    if st == 200 and isinstance(body, list):
        langs = [{"code": l["code"], "name": l["name"]} for l in body]
        return {"ok": True, "engine": "libretranslate", "languages": langs, "count": len(langs)}
    return {"ok": False, "engine": "libretranslate", "error": body.get("error", str(body))[:200]}

# ── Dispatchers ────────────────────────────────────────────────────

def _need_text(params):
    if not params.get("text") and not params.get("q"):
        return {"ok": False, "error": "缺少 text/q 参数"}
    return None

def do_translate(params):
    if err := _need_text(params): return err
    if DEEPL_KEY: return _dl_translate(params)
    if LT_URL: return _lt_translate(params)
    return {"ok": False, "error": "未配置 DEEPL_API_KEY 或 LIBRETRANSLATE_URL"}

def do_detect_language(params):
    if err := _need_text(params): return err
    if DEEPL_KEY: return _dl_detect(params)
    if LT_URL: return _lt_detect(params)
    return {"ok": False, "error": "未配置 DEEPL_API_KEY 或 LIBRETRANSLATE_URL"}

def do_list_languages(params):
    if DEEPL_KEY:
        r = _dl_languages(params)
        if r.get("ok"): return r
    if LT_URL: return _lt_languages(params)
    # 内置回退: 常用语言列表 (不需要API)
    return {"ok": True, "mode": "builtin", "languages": {
        "zh": "中文", "en": "English", "ja": "日本語", "ko": "한국어",
        "fr": "Français", "de": "Deutsch", "es": "Español", "pt": "Português",
        "ru": "Русский", "ar": "العربية", "hi": "हिन्दी", "th": "ไทย",
        "vi": "Tiếng Việt", "id": "Bahasa Indonesia", "it": "Italiano",
    }, "count": 15, "note": "内置语言列表(无需API key)。配置DEEPL_API_KEY获取完整列表"}

HANDLERS = {"translate": do_translate, "detect_language": do_detect_language,
            "list_languages": do_list_languages}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "translate"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    if not params:
        try:
            raw = sys.stdin.read().strip()
            if raw: params = json.loads(raw)
        except: pass
    if not params and action != "list_languages":
        params = {"text": " ".join(sys.argv[2:])} if len(sys.argv) > 2 else params
    h = HANDLERS.get(action)
    result = h(params) if h else {"ok": False, "error": f"未知动作: {action}",
                                   "available": list(HANDLERS.keys())}
    print(json.dumps(result, ensure_ascii=False, default=str))
