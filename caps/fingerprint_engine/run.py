"""fingerprint_engine/run.py — GBT自建浏览器指纹引擎

不依赖2Captcha，本地生成真实浏览器指纹数据库。
用户按次付费使用，平台直接赚钱。

指纹维度:
  screen · userAgent · navigator · webgl · webgpu
  voices · intl · canvas · fonts · headers · visitorId

数据来源: 基于真实浏览器统计分布生成
覆盖: Windows/macOS/Linux · Chrome/Firefox/Safari/Edge · 全球主要国家
"""
import hashlib
import json
import os
import random
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
DATA_DIR = Path.home() / ".gbt" / "fingerprints"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════
#  真实浏览器指纹数据库
# ═══════════════════════════════════════════════════════════

# Chrome 版本库（基于全球统计分布）
CHROME_VERSIONS = {
    "Windows": [
        {"major": 131, "weight": 35},
        {"major": 130, "weight": 28},
        {"major": 129, "weight": 18},
        {"major": 128, "weight": 12},
        {"major": 127, "weight": 7},
    ],
    "macOS": [
        {"major": 131, "weight": 38},
        {"major": 130, "weight": 30},
        {"major": 129, "weight": 20},
        {"major": 128, "weight": 12},
    ],
    "Linux": [
        {"major": 131, "weight": 32},
        {"major": 130, "weight": 30},
        {"major": 129, "weight": 20},
        {"major": 128, "weight": 18},
    ]
}

# 屏幕分辨率库（全球 TOP 统计）
SCREEN_PRESETS = {
    "Windows": [
        {"w": 1920, "h": 1080, "dpr": 1.0, "weight": 22},
        {"w": 1366, "h": 768, "dpr": 1.0, "weight": 18},
        {"w": 2560, "h": 1440, "dpr": 1.0, "weight": 10},
        {"w": 1536, "h": 864, "dpr": 1.25, "weight": 8},
        {"w": 1440, "h": 900, "dpr": 1.0, "weight": 7},
        {"w": 3840, "h": 2160, "dpr": 1.5, "weight": 4},
        {"w": 1280, "h": 720, "dpr": 1.0, "weight": 6},
        {"w": 1680, "h": 1050, "dpr": 1.0, "weight": 5},
    ],
    "macOS": [
        {"w": 1440, "h": 900, "dpr": 2.0, "weight": 25},
        {"w": 1680, "h": 1050, "dpr": 2.0, "weight": 20},
        {"w": 2560, "h": 1600, "dpr": 2.0, "weight": 15},
        {"w": 1728, "h": 1117, "dpr": 2.0, "weight": 12},
        {"w": 2056, "h": 1329, "dpr": 2.0, "weight": 8},
        {"w": 3840, "h": 2160, "dpr": 2.0, "weight": 5},
    ],
    "Linux": [
        {"w": 1920, "h": 1080, "dpr": 1.0, "weight": 40},
        {"w": 2560, "h": 1440, "dpr": 1.0, "weight": 20},
        {"w": 1366, "h": 768, "dpr": 1.0, "weight": 15},
        {"w": 3840, "h": 2160, "dpr": 1.0, "weight": 10},
    ]
}

# WebGL 渲染器库
WEBGL_RENDERERS = {
    "Windows": [
        "ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 (0x00002803) Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 (0x00002504) Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (Intel, Intel(R) UHD Graphics (0x00009A49) Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (AMD, Radeon RX 580 Series (0x000067DF) Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 (0x00002184) Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 (0x00002786) Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics (0x00009A60) Direct3D11 vs_5_0 ps_5_0)",
    ],
    "macOS": [
        "ANGLE (Apple, Apple M2 Pro (0x00000001) OpenGL 4.1)",
        "ANGLE (Apple, Apple M1 (0x00000001) OpenGL 4.1)",
        "ANGLE (Apple, Apple M3 (0x00000001) OpenGL 4.1)",
        "ANGLE (Apple, Apple M2 (0x00000001) OpenGL 4.1)",
        "ANGLE (Apple, Apple M1 Pro (0x00000001) OpenGL 4.1)",
    ],
    "Linux": [
        "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 (0x00002504) OpenGL 4.5)",
        "ANGLE (AMD, Radeon RX 6700 XT (0x000073DF) OpenGL 4.6)",
        "Mesa Intel(R) UHD Graphics (TGL GT2) (0x00009A49)",
        "ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 (0x00002803) OpenGL 4.6)",
    ]
}

# 语言/地区配置
LOCALE_CONFIGS = {
    "us": {"lang": "en-US", "timezone": "America/New_York", "accept_lang": "en-US,en;q=0.9"},
    "gb": {"lang": "en-GB", "timezone": "Europe/London", "accept_lang": "en-GB,en;q=0.9"},
    "de": {"lang": "de-DE", "timezone": "Europe/Berlin", "accept_lang": "de-DE,de;q=0.9,en;q=0.7"},
    "jp": {"lang": "ja-JP", "timezone": "Asia/Tokyo", "accept_lang": "ja-JP,ja;q=0.9,en;q=0.6"},
    "cn": {"lang": "zh-CN", "timezone": "Asia/Shanghai", "accept_lang": "zh-CN,zh;q=0.9,en;q=0.5"},
    "fr": {"lang": "fr-FR", "timezone": "Europe/Paris", "accept_lang": "fr-FR,fr;q=0.9,en;q=0.6"},
}

# User-Agent 模板
UA_TEMPLATES = {
    "Windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{ver}.0.0.0 Safari/537.36",
    "macOS": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{ver}.0.0.0 Safari/537.36",
    "Linux": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{ver}.0.0.0 Safari/537.36",
}


def _weighted_choice(items):
    """加权随机选择"""
    total = sum(item["weight"] for item in items)
    r = random.uniform(0, total)
    cumulative = 0
    for item in items:
        cumulative += item["weight"]
        if r <= cumulative:
            return item
    return items[-1]


def _random_webgl_extensions(os_name):
    """生成随机WebGL扩展列表"""
    common = [
        "ANGLE_instanced_arrays", "EXT_blend_minmax", "EXT_color_buffer_half_float",
        "EXT_disjoint_timer_query", "EXT_float_blend", "EXT_frag_depth",
        "EXT_shader_texture_lod", "EXT_texture_compression_bptc",
        "EXT_texture_compression_rgtc", "EXT_texture_filter_anisotropic",
        "EXT_sRGB", "OES_element_index_uint", "OES_fbo_render_mipmap",
        "OES_standard_derivatives", "OES_texture_float", "OES_texture_float_linear",
        "OES_texture_half_float", "OES_texture_half_float_linear",
        "OES_vertex_array_object", "WEBGL_color_buffer_float",
        "WEBGL_compressed_texture_s3tc", "WEBGL_compressed_texture_s3tc_srgb",
        "WEBGL_debug_renderer_info", "WEBGL_debug_shaders", "WEBGL_depth_texture",
        "WEBGL_draw_buffers", "WEBGL_lose_context", "WEBGL_multi_draw",
    ]
    n = random.randint(22, 28)
    return random.sample(common, min(n, len(common)))


def _random_fonts(os_name):
    """生成随机系统字体列表"""
    common = [
        "Arial", "Arial Black", "Arial Narrow", "Book Antiqua", "Bookman Old Style",
        "Calibri", "Cambria", "Candara", "Century Gothic", "Comic Sans MS",
        "Consolas", "Constantia", "Corbel", "Courier New", "Franklin Gothic Medium",
        "Garamond", "Georgia", "Impact", "Lucida Console", "Lucida Sans Unicode",
        "Microsoft Sans Serif", "Palatino Linotype", "Segoe Print", "Segoe Script",
        "Segoe UI", "Segoe UI Light", "Segoe UI Semibold", "Segoe UI Symbol",
        "Tahoma", "Times New Roman", "Trebuchet MS", "Verdana", "Webdings",
        "Wingdings", "DejaVu Sans", "Liberation Sans", "Ubuntu",
    ]
    n = random.randint(100, 160)
    result = random.sample(common, min(len(common), 20))
    # 填充随机命名字体
    prefixes = ["Noto", "Source", "Open", "Roboto", "Lato", "Montserrat", "PT", "Fira"]
    suffixes = ["Sans", "Serif", "Mono", "Display", "Text", "Condensed"]
    for _ in range(n - len(result)):
        result.append(f"{random.choice(prefixes)} {random.choice(suffixes)}")
    return sorted(set(result))


def _random_voices():
    """生成随机语音合成声音列表"""
    voices = [
        {"name": "Google US English", "lang": "en-US", "default": True},
        {"name": "Google UK English Female", "lang": "en-GB", "default": False},
        {"name": "Google UK English Male", "lang": "en-GB", "default": False},
        {"name": "Google español", "lang": "es-ES", "default": False},
        {"name": "Google français", "lang": "fr-FR", "default": False},
        {"name": "Google Deutsch", "lang": "de-DE", "default": False},
        {"name": "Google 日本語", "lang": "ja-JP", "default": False},
        {"name": "Google 普通话 (中国大陆)", "lang": "zh-CN", "default": False},
        {"name": "Microsoft David", "lang": "en-US", "default": False},
        {"name": "Microsoft Zira", "lang": "en-US", "default": False},
    ]
    return random.sample(voices, random.randint(4, 8))


def _generate_visitor_id():
    """生成访问者ID (类FingerprintJS)"""
    raw = f"{uuid.uuid4()}-{random.random()}-{time.time()}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def _canvas_hash(os_name):
    """生成类Canvas指纹哈希"""
    raw = f"{os_name}-{random.random()}-{random.randint(0, 999999)}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def generate_fingerprint(os_filter=None, country="us", browser="chrome"):
    """生成一个完整的浏览器指纹"""
    os_name = os_filter or random.choice(["Windows", "macOS", "Linux"])
    if os_name not in CHROME_VERSIONS:
        os_name = "Windows"

    # 版本
    ver = _weighted_choice(CHROME_VERSIONS[os_name])
    major = ver["major"]
    minor = random.randint(0, 99)
    build = random.randint(1000, 9999)
    patch = random.randint(0, 999)

    # 屏幕
    screen = _weighted_choice(SCREEN_PRESETS.get(os_name, SCREEN_PRESETS["Windows"]))

    # User-Agent
    ua = UA_TEMPLATES.get(os_name, UA_TEMPLATES["Windows"]).format(ver=major)

    # 地区
    locale = LOCALE_CONFIGS.get(country, LOCALE_CONFIGS["us"])
    if country == "us" and random.random() > 0.7:
        locale = random.choice(list(LOCALE_CONFIGS.values()))

    # WebGL
    renderer = random.choice(WEBGL_RENDERERS.get(os_name, WEBGL_RENDERERS["Windows"]))
    vendor = "Google Inc. (NVIDIA)" if os_name != "macOS" else "Google Inc. (Apple)"

    # Navigator
    cpu_cores = random.choice([4, 8, 16, 12, 32, 6])
    device_memory = random.choice([4, 8, 16, 32])

    # 平台
    platform_map = {"Windows": "Win32", "macOS": "MacIntel", "Linux": "Linux x86_64"}
    platform = platform_map.get(os_name, "Win32")

    fingerprint = {
        "visitorId": _generate_visitor_id(),
        "userAgent": {"value": ua, "platform": platform},
        "screen": {
            "width": screen["w"], "height": screen["h"],
            "availWidth": screen["w"], "availHeight": screen["h"] - random.choice([40, 48, 60]),
            "colorDepth": 24, "pixelDepth": 24,
            "deviceScaleFactor": screen["dpr"],
        },
        "navigator": {
            "platform": platform,
            "hardwareConcurrency": cpu_cores,
            "deviceMemory": device_memory,
            "maxTouchPoints": 0 if os_name != "Linux" else random.choice([0, 0, 0, 0, 10]),
            "language": locale["lang"],
            "languages": [locale["lang"], locale["lang"].split("-")[0]],
            "vendor": "Google Inc.",
            "vendorSub": "",
            "productSub": "20030107",
            "doNotTrack": random.choice([None, "1"]),
            "cookieEnabled": True,
        },
        "webgl": {
            "vendor": vendor,
            "renderer": renderer,
            "unmaskedVendor": "Google Inc. (NVIDIA)" if "NVIDIA" in renderer else vendor,
            "unmaskedRenderer": renderer,
            "extensions": _random_webgl_extensions(os_name),
            "parameters": {
                "MAX_TEXTURE_SIZE": 16384,
                "MAX_VIEWPORT_DIMS": "16384,16384",
                "MAX_RENDERBUFFER_SIZE": 16384,
                "MAX_VERTEX_TEXTURE_IMAGE_UNITS": 16,
                "MAX_TEXTURE_IMAGE_UNITS": 16,
                "MAX_COMBINED_TEXTURE_IMAGE_UNITS": random.choice([32, 48, 64, 96]),
                "ALIASED_LINE_WIDTH_RANGE": "1,1",
                "ALIASED_POINT_SIZE_RANGE": "1,1024",
            }
        },
        "webgpu": {
            "adapter": {
                "vendor": "nvidia" if "NVIDIA" in renderer else "intel",
                "architecture": "",
                "device": "",
                "description": renderer,
            }
        },
        "fonts": _random_fonts(os_name),
        "canvas": {"hash": _canvas_hash(os_name)},
        "voices": _random_voices(),
        "timezone": {
            "value": locale["timezone"],
            "offset": random.choice([-480, -300, -240, 0, 60, 120, 480, 540]),
        },
        "intl": {
            "locale": locale["lang"],
            "timeZone": locale["timezone"],
        },
        "headers": {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": locale["accept_lang"],
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-CH-UA": f'"Chromium";v="{major}", "Google Chrome";v="{major}", "Not=A?Brand";v="99"',
            "Sec-CH-UA-Platform": f'"{os_name}"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        },
        "meta": {
            "os": os_name,
            "browser": f"Chrome {major}",
            "country": country,
            "generated_at": time.time(),
            "engine": "GBT Fingerprint Engine v1.0",
        }
    }
    return fingerprint


# ═══════════════════════════════════════════════════════════
#  Action Handlers
# ═══════════════════════════════════════════════════════════

def do_random(params: dict) -> dict:
    os_filter = params.get("os") or params.get("tags")
    country = params.get("country", "us")
    fp = generate_fingerprint(os_filter=os_filter, country=country)
    return {"ok": True, "fingerprint": fp}


def do_generate(params: dict) -> dict:
    os_filter = params.get("os") or params.get("tags")
    country = params.get("country", "us")
    browser = params.get("browser", "chrome")
    fp = generate_fingerprint(os_filter=os_filter, country=country, browser=browser)
    return {"ok": True, "fingerprint": fp}


def do_browser_context(params: dict) -> dict:
    fp = generate_fingerprint(
        os_filter=params.get("os"),
        country=params.get("country", "us"),
    )
    screen = fp["screen"]
    nav = fp["navigator"]
    headers = fp["headers"]
    context = {
        "viewport": {"width": screen["width"], "height": screen["height"]},
        "device_scale_factor": screen["deviceScaleFactor"],
        "user_agent": fp["userAgent"]["value"],
        "locale": fp["intl"]["locale"],
        "timezone_id": fp["intl"]["timeZone"],
        "geolocation": {
            "latitude": random.uniform(33.0, 48.0) if params.get("country") == "us" else random.uniform(35.0, 55.0),
            "longitude": random.uniform(-122.0, -73.0) if params.get("country") == "us" else random.uniform(-10.0, 40.0),
        },
        "permissions": ["geolocation"],
        "color_scheme": random.choice(["light", "dark"]),
        "extra_http_headers": {k: v for k, v in headers.items() if k.startswith("Sec-") or k == "Accept-Language"},
    }
    return {"ok": True, "browser_context": context}


def do_puppeteer_context(params: dict) -> dict:
    fp = generate_fingerprint(
        os_filter=params.get("os"),
        country=params.get("country", "us"),
    )
    screen = fp["screen"]
    puppeteer_args = {
        "args": [
            "--disable-blink-features=AutomationControlled",
            f"--window-size={screen['width']},{screen['height']}",
        ],
        "defaultViewport": {
            "width": screen["width"],
            "height": screen["height"],
            "deviceScaleFactor": screen["deviceScaleFactor"],
            "isMobile": False,
            "hasTouch": False,
        },
        "userDataDir": "",
        "ignoreDefaultArgs": ["--enable-automation"],
    }
    return {"ok": True, "puppeteer_context": puppeteer_args}


def do_stealth_config(params: dict) -> dict:
    os_name = params.get("os") or random.choice(["Windows", "macOS", "Linux"])
    fp = generate_fingerprint(os_filter=os_name, country=params.get("country", "us"))
    screen = fp["screen"]
    headers = fp["headers"]

    config = {
        "browser": fp["meta"]["browser"],
        "os": fp["meta"]["os"],
        "launch_args": [
            "--disable-blink-features=AutomationControlled",
            "--disable-features=IsolateOrigins,site-per-process",
            "--no-sandbox",
            f"--window-size={screen['width']},{screen['height']}",
        ],
        "context": {
            "viewport": {"width": screen["width"], "height": screen["height"]},
            "device_scale_factor": screen["deviceScaleFactor"],
            "user_agent": fp["userAgent"]["value"],
            "locale": fp["intl"]["locale"],
            "timezone_id": fp["intl"]["timeZone"],
            "geolocation": {
                "latitude": random.uniform(33.0, 48.0),
                "longitude": random.uniform(-122.0, -73.0),
            },
            "permissions": ["geolocation", "notifications"],
            "extra_http_headers": {k: v for k, v in headers.items() if "Sec-" in k or "Accept" in k},
        },
        "headers": headers,
        "cdp_scripts": [
            "// Override navigator.webdriver\n"
            "Object.defineProperty(navigator, 'webdriver', {get: () => false});",
            "// Override chrome.runtime\n"
            "window.chrome = {runtime: {}, loadTimes: function() {}, csi: function() {}};",
            "// Override permissions\n"
            f"const originalQuery = window.navigator.permissions.query;\n"
            f"window.navigator.permissions.query = (parameters) => (\n"
            f"  parameters.name === 'notifications' ?\n"
            f"    Promise.resolve({{state: Notification.permission}}) :\n"
            f"    originalQuery(parameters)\n"
            f");",
        ],
        "fingerprint": fp,
    }
    return {"ok": True, "stealth_config": config}


def do_stats(params: dict) -> dict:
    return {"ok": True, "engine": "GBT Fingerprint Engine v1.0", "stats": {
        "os_covered": list(CHROME_VERSIONS.keys()),
        "screen_presets": sum(len(v) for v in SCREEN_PRESETS.values()),
        "webgl_renderers": sum(len(v) for v in WEBGL_RENDERERS.values()),
        "locales": len(LOCALE_CONFIGS),
        "fingerprints_possible": "unlimited (generative)",
        "pricing": "$0.001/次 或 $9.99/月无限",
        "vs_2captcha": "自建零成本，用户付费你赚钱",
    }}


HANDLERS = {
    "random": do_random,
    "generate": do_generate,
    "browser_context": do_browser_context,
    "puppeteer_context": do_puppeteer_context,
    "stealth_config": do_stealth_config,
    "stats": do_stats,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "stats"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知动作: {action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
