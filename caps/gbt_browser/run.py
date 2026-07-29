# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
gbt_browser/run.py — GBT 统一浏览器引擎 v1.0
==============================================
合并: fingerprint_engine + browser_automation + anti_track + fingerprint_browser
→ 一个模块搞定: 指纹伪装 → 隐身浏览器 → 自动操控 → 反检测

15维指纹 · SeleniumBase+Playwright双引擎 · 请求级伪装 · 持久化配置
"""
import sys, json, os, time, random, base64, hashlib, subprocess, uuid
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
DATA_DIR = Path.home() / ".gbt" / "browser"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ══════════════════════════════════════════════════════════════
#  LAYER 1 — 15维浏览器指纹引擎
# ══════════════════════════════════════════════════════════════

CHROME_VERSIONS = {
    "win": [("131.0.6778.0", 25), ("130.0.6723.0", 30), ("129.0.6668.0", 20),
            ("128.0.6613.0", 15), ("127.0.6533.0", 10)],
    "mac": [("131.0.6778.0", 30), ("130.0.6723.0", 30), ("129.0.6668.0", 25),
            ("128.0.6613.0", 15)],
    "linux": [("130.0.6723.0", 40), ("129.0.6668.0", 35), ("128.0.6613.0", 25)],
}

SCREEN_PRESETS = {
    "win": [("1920x1080", 35), ("1366x768", 25), ("2560x1440", 15),
            ("1536x864", 10), ("1440x900", 8), ("1680x1050", 7)],
    "mac": [("1680x1050", 30), ("2560x1600", 25), ("1920x1080", 20),
            ("1440x900", 15), ("1728x1117", 10)],
    "linux": [("1920x1080", 45), ("1366x768", 30), ("2560x1440", 15),
              ("1600x900", 10)],
}

WEBGL_RENDERERS = {
    "win": ["ANGLE (NVIDIA GeForce RTX 3060)", "ANGLE (Intel UHD Graphics 630)",
            "ANGLE (AMD Radeon RX 580)", "ANGLE (NVIDIA GeForce GTX 1660)",
            "ANGLE (Intel Iris Xe Graphics)", "ANGLE (NVIDIA GeForce RTX 4060)"],
    "mac": ["Apple M1", "Apple M2", "Apple M3", "AMD Radeon Pro 5500M",
            "Intel UHD Graphics 630", "Apple M1 Pro"],
    "linux": ["Mesa Intel UHD Graphics 630", "Mesa Intel HD Graphics 620",
              "Mesa AMD Radeon RX 580", "Mesa NVIDIA GeForce GTX 1660"],
}

UA_TEMPLATES = {
    "chrome": "Mozilla/5.0 ({os}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36",
    "edge": "Mozilla/5.0 ({os}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36 Edg/{version}",
    "firefox": "Mozilla/5.0 ({os}; rv:{major}.0) Gecko/20100101 Firefox/{major}.0",
}

LOCALE_CONFIGS = {
    "us": {"lang": "en-US,en;q=0.9", "tz": "America/New_York", "tz_offset": -300},
    "cn": {"lang": "zh-CN,zh;q=0.9,en;q=0.8", "tz": "Asia/Shanghai", "tz_offset": 480},
    "jp": {"lang": "ja-JP,ja;q=0.9,en;q=0.8", "tz": "Asia/Tokyo", "tz_offset": 540},
    "hk": {"lang": "zh-HK,zh;q=0.9,en;q=0.8", "tz": "Asia/Hong_Kong", "tz_offset": 480},
    "uk": {"lang": "en-GB,en;q=0.9", "tz": "Europe/London", "tz_offset": 0},
}

OS_PLATFORMS = {
    "Windows": "Win32", "macOS": "MacIntel", "Linux": "Linux x86_64"
}

FONT_POOLS = {
    "Windows": ["Arial", "Calibri", "Cambria", "Comic Sans MS", "Consolas",
                "Courier New", "Georgia", "Impact", "Segoe UI", "Tahoma",
                "Times New Roman", "Trebuchet MS", "Verdana", "Webdings"],
    "macOS": ["Helvetica", "Helvetica Neue", "Arial", "Georgia", "Menlo",
              "Monaco", "SF Pro Display", "SF Pro Text", "Times New Roman",
              "Trebuchet MS", "Verdana", "Courier New", "Apple Color Emoji"],
    "Linux": ["DejaVu Sans", "DejaVu Serif", "Liberation Sans", "Liberation Serif",
              "FreeSans", "FreeSerif", "Noto Sans", "Noto Serif", "Ubuntu",
              "Cantarell", "Monospace", "Nimbus Sans", "Nimbus Roman"],
}

CANVAS_NOISE_LEVELS = {"off": 0, "low": 0.5, "medium": 2.0, "high": 5.0}

def _weighted_choice(items):
    total = sum(w for _, w in items)
    r = random.uniform(0, total)
    for item, weight in items:
        r -= weight
        if r <= 0:
            return item
    return items[-1][0]

def generate_fingerprint(os_name="Windows", country="cn", browser="chrome",
                          canvas_noise="medium", screen_w=None, screen_h=None):
    """生成完整的15维浏览器指纹"""
    os_name = os_name or random.choice(["Windows", "macOS", "Linux"])
    ver = _weighted_choice(CHROME_VERSIONS.get(
        {"Windows": "win", "macOS": "mac", "Linux": "linux"}.get(os_name, "win"),
        CHROME_VERSIONS["win"]))
    major = ver.split(".")[0]

    if screen_w and screen_h:
        resolution = f"{screen_w}x{screen_h}"
    else:
        resolution = _weighted_choice(SCREEN_PRESETS.get(
            {"Windows": "win", "macOS": "mac", "Linux": "linux"}.get(os_name, "win"),
            SCREEN_PRESETS["win"]))
    sw, sh = resolution.split("x")
    sw, sh = int(sw), int(sh)

    renderer = random.choice(WEBGL_RENDERERS.get(
        {"Windows": "win", "macOS": "mac", "Linux": "linux"}.get(os_name, "win"),
        WEBGL_RENDERERS["win"]))

    locale = LOCALE_CONFIGS.get(country, LOCALE_CONFIGS["cn"])
    fonts = random.sample(FONT_POOLS.get(os_name, FONT_POOLS["Windows"]),
                          random.randint(8, 14))

    os_strings = {
        "Windows": f"Windows NT 10.0; Win64; x64",
        "macOS": f"Macintosh; Intel Mac OS X 10_15_7",
        "Linux": "X11; Linux x86_64",
    }

    ua = UA_TEMPLATES.get(browser, UA_TEMPLATES["chrome"]).format(
        os=os_strings.get(os_name, os_strings["Windows"]),
        version=ver, major=major)

    canvas_hash = hashlib.sha256(
        f"{os_name}{ver}{renderer}{random.random()}".encode()).hexdigest()[:32]
    webgl_hash = hashlib.md5(
        f"{renderer}{random.random()}".encode()).hexdigest()[:16]
    visitor_id = hashlib.md5(
        f"{uuid.uuid4()}{random.random()}{time.time()}".encode()).hexdigest()[:16]

    noise = CANVAS_NOISE_LEVELS.get(canvas_noise, 2.0)

    return {
        "visitor_id": visitor_id,
        "user_agent": ua,
        "platform": OS_PLATFORMS.get(os_name, "Win32"),
        "os": os_name,
        "browser": f"Chrome/{major}",
        "chrome_version": ver,
        "screen": {"width": sw, "height": sh, "availWidth": sw, "availHeight": sh - 40,
                    "colorDepth": 24, "pixelRatio": random.choice([1, 1.25, 1.5, 2])},
        "languages": [locale["lang"].split(",")[0], "en"],
        "language_raw": locale["lang"],
        "timezone": locale["tz"],
        "timezone_offset": locale["tz_offset"],
        "webgl_renderer": renderer,
        "webgl_vendor": "Google Inc. (NVIDIA)" if "NVIDIA" in renderer else "Google Inc. (Intel)",
        "webgl_hash": webgl_hash,
        "canvas_hash": canvas_hash,
        "canvas_noise": noise,
        "fonts": sorted(fonts),
        "hardware_concurrency": random.choice([4, 8, 12, 16, 24, 32]),
        "device_memory": random.choice([4, 8, 16, 32]),
        "touch_support": False if os_name != "Android" else True,
        "audio_noise": random.uniform(0.0001, 0.001) if canvas_noise != "off" else 0,
        "headers": {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": locale["lang"],
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Ch-Ua": f'"Chromium";v="{major}", "Google Chrome";v="{major}", "Not=A?Brand";v="99"',
            "Sec-Ch-Ua-Platform": f'"{os_name}"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        },
    }


# ══════════════════════════════════════════════════════════════
#  LAYER 2 — 隐身浏览器引擎 (SeleniumBase + Playwright)
# ══════════════════════════════════════════════════════════════

HAS_SELENIUM = False
HAS_PLAYWRIGHT = False

def _get_selenium_driver(headless=True, fingerprint=None, proxy=None):
    global HAS_SELENIUM
    try:
        from seleniumbase import Driver
        HAS_SELENIUM = True
        from selenium_stealth import stealth
    except ImportError:
        return None, "pip install seleniumbase selenium-stealth"

    fp = fingerprint or generate_fingerprint()
    ua = fp["user_agent"]
    lang = fp["language_raw"]

    try:
        driver = Driver(
            browser="chrome",
            headless=headless,
            agent=ua,
            proxy=proxy,
            undetectable=True,
            incognito=True,
            disable_csp=True,
        )
        stealth(driver,
            languages=[lang],
            vendor="Google Inc.",
            platform=fp["platform"],
            webgl_vendor=fp["webgl_vendor"],
            renderer=fp["webgl_renderer"],
            fix_hairline=True,
        )
        return {"driver": driver, "fingerprint": fp, "engine": "seleniumbase"}
    except Exception as e:
        return None, str(e)

def _get_playwright_browser(headless=True, fingerprint=None, proxy=None):
    global HAS_PLAYWRIGHT
    try:
        from playwright.sync_api import sync_playwright
        HAS_PLAYWRIGHT = True
    except ImportError:
        return None, "pip install playwright && playwright install chromium"

    fp = fingerprint or generate_fingerprint()
    try:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(
            headless=headless,
            args=[
                f"--user-agent={fp['user_agent']}",
                f"--window-size={fp['screen']['width']},{fp['screen']['height']}",
                f"--accept-lang={fp['language_raw']}",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--no-sandbox",
            ] + ([f"--proxy-server={proxy}"] if proxy else [])
        )
        context = browser.new_context(
            viewport={"width": fp["screen"]["width"], "height": fp["screen"]["height"]},
            user_agent=fp["user_agent"],
            locale=fp["language_raw"].split(",")[0],
            timezone_id=fp["timezone"],
            permissions=["geolocation"],
            geolocation={"latitude": random.uniform(30, 40), "longitude": random.uniform(110, 122)} if fp["os"] == "Windows" else None,
        )
        page = context.new_page()
        return {"pw": pw, "browser": browser, "context": context, "page": page,
                "fingerprint": fp, "engine": "playwright"}
    except Exception as e:
        return None, str(e)

def launch_browser(headless=True, fingerprint=None, proxy=None, prefer="seleniumbase"):
    """启动隐身浏览器 — 自动选择可用引擎"""
    engines = [prefer] + [e for e in ["seleniumbase", "playwright"] if e != prefer]

    for engine in engines:
        if engine == "seleniumbase":
            result = _get_selenium_driver(headless, fingerprint, proxy)
        else:
            result = _get_playwright_browser(headless, fingerprint, proxy)

        if isinstance(result, dict) and "driver" in result:
            return result
        if isinstance(result, dict) and "page" in result:
            return result

    return {"ok": False, "error": "No browser engine available",
            "install": "pip install seleniumbase selenium-stealth playwright && playwright install chromium"}


# ══════════════════════════════════════════════════════════════
#  LAYER 3 — 请求级反检测
# ══════════════════════════════════════════════════════════════

UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
]

ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9", "zh-CN,zh;q=0.9,en;q=0.8", "en-GB,en;q=0.9",
    "ja-JP,ja;q=0.9,en;q=0.8", "en-US,en;q=0.9,zh-CN;q=0.8",
]

def stealth_headers(target_url=""):
    """生成一次性随机请求头"""
    fp = generate_fingerprint()
    headers = dict(fp["headers"])
    headers["User-Agent"] = random.choice(UA_POOL)
    headers["Accept-Language"] = random.choice(ACCEPT_LANGUAGES)
    if target_url:
        from urllib.parse import urlparse
        parsed = urlparse(target_url)
        headers["Host"] = parsed.netloc
        headers["Origin"] = f"{parsed.scheme}://{parsed.netloc}"
        headers["Referer"] = f"{parsed.scheme}://{parsed.netloc}/"
    return headers

def human_delay(min_ms=200, max_ms=1500):
    """拟人随机延迟 (毫秒)"""
    time.sleep(random.uniform(min_ms, max_ms) / 1000.0)

def human_scroll(page_or_driver, times=3):
    """拟人滚动 — 随机速度和停顿"""
    for _ in range(times):
        scroll = random.randint(200, 600)
        try:
            page_or_driver.execute_script(f"window.scrollBy(0, {scroll})")
        except Exception:
            try:
                page_or_driver.evaluate(f"window.scrollBy(0, {scroll})")
            except Exception:
                break
        human_delay(500, 2500)


# ══════════════════════════════════════════════════════════════
#  LAYER 4 — 持久化浏览器配置文件
# ══════════════════════════════════════════════════════════════

PROFILES_DIR = DATA_DIR / "profiles"
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

def create_profile(name, fp=None, proxy=""):
    """创建持久化浏览器配置文件"""
    fp = fp or generate_fingerprint()
    profile_dir = PROFILES_DIR / name
    profile_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "name": name, "fingerprint": fp, "proxy": proxy,
        "created": datetime.now().isoformat(), "last_used": None,
    }
    (profile_dir / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2))
    return {"ok": True, "name": name, "profile_dir": str(profile_dir), "fingerprint": fp["visitor_id"]}

def list_profiles():
    profiles = []
    if PROFILES_DIR.exists():
        for d in sorted(PROFILES_DIR.iterdir()):
            if d.is_dir() and (d / "config.json").exists():
                cfg = json.loads((d / "config.json").read_text())
                profiles.append({"name": d.name, "created": cfg.get("created"),
                                 "visitor_id": cfg["fingerprint"].get("visitor_id", "?")})
    return profiles

def delete_profile(name):
    p = PROFILES_DIR / name
    if p.exists():
        import shutil
        shutil.rmtree(p)
        return {"ok": True, "deleted": name}
    return {"ok": False, "error": f"Profile {name} not found"}


# ══════════════════════════════════════════════════════════════
#  ACTION HANDLERS
# ══════════════════════════════════════════════════════════════

def do_generate_fingerprint(params):
    fp = generate_fingerprint(
        os_name=params.get("os") or random.choice(["Windows", "macOS", "Linux"]),
        country=params.get("country", "cn"),
        browser=params.get("browser", "chrome"),
        canvas_noise=params.get("canvas_noise", "medium"),
    )
    return {"ok": True, "fingerprint": fp}

def do_launch_browser(params):
    result = launch_browser(
        headless=params.get("headless", True),
        fingerprint=params.get("fingerprint"),
        proxy=params.get("proxy"),
        prefer=params.get("engine", "seleniumbase"),
    )
    if isinstance(result, dict) and ("driver" in result or "page" in result):
        return {"ok": True, "engine": result["engine"],
                "visitor_id": result["fingerprint"]["visitor_id"]}
    return result

def do_stealth_headers(params):
    headers = stealth_headers(params.get("url", ""))
    return {"ok": True, "headers": headers, "count": len(headers)}

def do_create_profile(params):
    return create_profile(
        name=params.get("name", f"profile_{int(time.time())}"),
        fp=params.get("fingerprint"),
        proxy=params.get("proxy", ""),
    )

def do_list_profiles(params=None):
    profiles = list_profiles()
    return {"ok": True, "profiles": profiles, "total": len(profiles)}

def do_delete_profile(params):
    return delete_profile(params.get("name", ""))

def do_status(params=None):
    return {
        "ok": True,
        "engine": "GBT Browser v1.0",
        "has_seleniumbase": HAS_SELENIUM,
        "has_playwright": HAS_PLAYWRIGHT,
        "profiles": len(list_profiles()),
        "fingerprint_dimensions": 15,
        "ua_pool": len(UA_POOL),
    }


HANDLERS = {
    "generate_fingerprint": do_generate_fingerprint,
    "launch_browser": do_launch_browser,
    "stealth_headers": do_stealth_headers,
    "create_profile": do_create_profile,
    "list_profiles": do_list_profiles,
    "delete_profile": do_delete_profile,
    "status": do_status,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "status"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知: {action}"})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
