# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""browser_fingerprint/run.py — 浏览器指纹 · 全维度能力模块

双引擎:
  1. GBT Fingerprint Engine (自建, 零成本, 默认)
  2. 2Captcha FingerprintAPI (付费, 回退)

指纹维度 (chromium格式):
  screen · userAgent · navigator · webgl · webgpu
  speechSynthesis · intl · canvas · fonts · visitorId · headers
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

# 优先自建引擎，无需API Key
try:
    from caps.fingerprint_engine.run import (
        generate_fingerprint,
        do_random, do_generate, do_browser_context,
        do_puppeteer_context, do_stealth_config, do_stats,
    )
    _ENGINE = "gbt"
except ImportError:
    _ENGINE = None

# 回退2Captcha（需要API Key）
try:
    from caps._2captcha.client import FingerprintAPI
    _2CAPTCHA = FingerprintAPI()
except Exception:
    _2CAPTCHA = None


def _gbt_random(params: dict) -> dict:
    fp = generate_fingerprint(
        os_filter=params.get("tags"),
        country=params.get("country", "us"),
    )
    return {"ok": True, "fingerprint": fp, "engine": "gbt"}


def _gbt_generate(params: dict) -> dict:
    fp = generate_fingerprint(
        os_filter=params.get("tags"),
        country=params.get("country", "us"),
    )
    return {"ok": True, "fingerprint": fp, "engine": "gbt"}


def _gbt_playwright(params: dict) -> dict:
    return do_browser_context(params)


def _gbt_puppeteer(params: dict) -> dict:
    return do_puppeteer_context(params)


def _gbt_stealth(params: dict) -> dict:
    return do_stealth_config(params)


def _gbt_headers(params: dict) -> dict:
    fp = generate_fingerprint(
        os_filter=params.get("tags"),
        country=params.get("country", "us"),
    )
    return {"ok": True, "headers": fp["headers"], "engine": "gbt"}


def _gbt_profile(params: dict) -> dict:
    fp = generate_fingerprint(
        os_filter=params.get("tags"),
        country=params.get("country", "us"),
    )
    return {"ok": True, "profile": fp, "engine": "gbt"}


# 提取器 (兼容两种引擎)
def _extract_ua(params: dict) -> dict:
    fp = params.get("fingerprint", {})
    ua = fp.get("userAgent", {})
    return {"ok": True, "user_agent": ua.get("value", "")}


def _extract_platform(params: dict) -> dict:
    fp = params.get("fingerprint", {})
    nav = fp.get("navigator", {})
    return {"ok": True, "platform": nav.get("platform", "")}


HANDLERS = {
    "random": lambda p: _gbt_random(p) if _ENGINE else _2CAPTCHA.random(**p),
    "generate": lambda p: _gbt_generate(p) if _ENGINE else _2CAPTCHA.generate(**p),
    "playwright_context": lambda p: _gbt_playwright(p) if _ENGINE else _2CAPTCHA.get_playwright_context(**p),
    "puppeteer_context": lambda p: _gbt_puppeteer(p) if _ENGINE else _2CAPTCHA.get_puppeteer_context(**p),
    "stealth_config": lambda p: _gbt_stealth(p) if _ENGINE else _2CAPTCHA.get_stealth_config(**p),
    "browser_headers": lambda p: _gbt_headers(p) if _ENGINE else _2CAPTCHA.get_browser_headers(**p),
    "complete_profile": lambda p: _gbt_profile(p) if _ENGINE else _2CAPTCHA.get_complete_profile(**p),
    "extract_ua": _extract_ua,
    "extract_platform": _extract_platform,
    "profile": lambda p: _gbt_profile(p) if _ENGINE else _2CAPTCHA.get_complete_profile(**p),
    "headers": lambda p: _gbt_headers(p) if _ENGINE else _2CAPTCHA.get_browser_headers(**p),
    "stealth": lambda p: _gbt_stealth(p) if _ENGINE else _2CAPTCHA.get_stealth_config(**p),
}


def do_action(params):
    action = params.get("action", params.get("_action", "complete_profile"))
    handler = HANDLERS.get(action)
    if handler is None:
        return {"ok": False, "error": f"unknown action: {action}",
                "available": sorted(HANDLERS.keys())}
    return handler(params)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        raw = sys.stdin.read()
        params = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, EOFError):
        params = {}
    result = do_action(params)
    print(json.dumps(result, ensure_ascii=False, default=str))
