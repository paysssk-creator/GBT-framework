# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""caps/_2captcha/client.py — 2Captcha 统一客户端

四条产品线:
  1. CaptchaSolver   — API v2 JSON端点 (createTask/getTaskResult/report)
  2. ProxyNetwork    — 住宅代理 (账户/位置/白名单)
  3. FingerprintAPI  — 浏览器指纹 (random/generate)
  4. CloudBrowser    — 云端CDP浏览器 (accounts/profiles/connection)

所有客户端共享同一个 API Key (环境变量 CAPTCHA_API_KEY)。
"""
import os
import json
import time
import base64
import urllib.request
import urllib.error
from pathlib import Path

# ═══════════════════════════════════════════════════════════
#  配置
# ═══════════════════════════════════════════════════════════

API_KEY = os.environ.get("CAPTCHA_API_KEY", "")
BASE_URL = "https://api.2captcha.com"
LEGACY_IN = "https://2captcha.com/in.php"
LEGACY_RES = "https://2captcha.com/res.php"

def _get_key():
    k = API_KEY
    if not k:
        # fallback: try .env in project root
        env_file = Path(__file__).parent.parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("CAPTCHA_API_KEY="):
                    k = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not k:
        raise RuntimeError("CAPTCHA_API_KEY not set. Export it or add to .env")
    return k


def _req(method, url, data=None, headers=None, timeout=60):
    """HTTP请求封装，返回 (body_bytes, error_str)"""
    hdrs = {"Content-Type": "application/json", "User-Agent": "GBT-xiaotudou/5.0"}
    if headers:
        hdrs.update(headers)
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read(), None
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return None, f"HTTP {e.code}: {err_body[:500]}"
    except Exception as e:
        return None, str(e)[:500]


def _parse(resp_bytes):
    if resp_bytes is None:
        return None
    try:
        return json.loads(resp_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return {"error": f"JSON parse failed: {e}"}


# ═══════════════════════════════════════════════════════════
#  1. CaptchaSolver — 验证码识别 (API v2)
# ═══════════════════════════════════════════════════════════

class CaptchaSolver:
    """2Captcha 验证码识别服务 (API v2)

    支持所有40+种验证码类型。核心流程:
      create_task → poll_result → report_correct/report_incorrect
    """

    def __init__(self, api_key=None):
        self.key = api_key or _get_key()

    # ── 核心方法 ──────────────────────────────────────────

    def create_task(self, task_type, **params):
        """提交验证码任务。

        task_type: 任务类型字符串，如:
          - "RecaptchaV2Task" / "RecaptchaV2TaskProxyless"
          - "RecaptchaV3TaskProxyless"
          - "RecaptchaEnterpriseTask"
          - "FunCaptchaTask" / "FunCaptchaTaskProxyless"
          - "GeeTestTask" / "GeeTestTaskProxyless"
          - "TurnstileTask" / "TurnstileTaskProxyless"
          - "HCaptchaTask" / "HCaptchaTaskProxyless"
          - "ImageToTextTask" (普通图片验证码)
          - "TextCaptchaTask"
          - "AudioCaptchaTask"
          - "CoordinatesTask" (点击验证码)
          - "RotateTask"
          - "AmazonWafTaskProxyless"
          - "DataDomeSliderTask"
          - "FriendlyCaptchaTaskProxyless"
          - "CutCaptchaTaskProxyless"
          - "MTCaptchaTaskProxyless"
          - "LeminTaskProxyless"
          - "CapyTaskProxyless"
          - "TencentTaskProxyless"
          - "BinanceTaskProxyless"
          - "ImpervaTaskProxyless"
          - "YandexTaskProxyless"
          以及更多...
        params: 任务特定参数 (websiteURL, websiteKey, proxy等)
        """
        task = {"type": task_type}
        task.update(params)
        body, err = _req("POST", f"{BASE_URL}/createTask",
                         {"clientKey": self.key, "task": task})
        if err:
            return {"ok": False, "error": err}
        data = _parse(body)
        if data.get("errorId") == 0:
            return {"ok": True, "taskId": data["taskId"]}
        return {"ok": False, "error": data.get("errorDescription", str(data))}

    def get_result(self, task_id):
        """获取任务结果。如果未完成返回 ok=False, error='not_ready'"""
        body, err = _req("POST", f"{BASE_URL}/getTaskResult",
                         {"clientKey": self.key, "taskId": task_id})
        if err:
            return {"ok": False, "error": err}
        data = _parse(body)
        if data.get("errorId") != 0:
            return {"ok": False, "error": data.get("errorDescription", str(data))}
        if data.get("status") == "ready":
            return {"ok": True, "solution": data.get("solution", {})}
        return {"ok": False, "error": "not_ready"}

    def solve_and_wait(self, task_type, poll_interval=3, max_wait=120, **params):
        """提交任务并等待结果。一体式便捷方法。"""
        task = self.create_task(task_type, **params)
        if not task["ok"]:
            return task
        tid = task["taskId"]
        waited = 0
        while waited < max_wait:
            time.sleep(poll_interval)
            waited += poll_interval
            result = self.get_result(tid)
            if result["ok"]:
                return {"ok": True, "taskId": tid, "solution": result["solution"]}
            if result.get("error") != "not_ready":
                return result
        return {"ok": False, "error": "timeout", "taskId": tid}

    def report_correct(self, task_id):
        """报告答案正确（改善AI训练）"""
        body, err = _req("POST", f"{BASE_URL}/reportCorrect",
                         {"clientKey": self.key, "taskId": task_id})
        if err:
            return {"ok": False, "error": err}
        return {"ok": True}

    def report_incorrect(self, task_id):
        """报告答案错误（退款+训练信号）"""
        body, err = _req("POST", f"{BASE_URL}/reportIncorrect",
                         {"clientKey": self.key, "taskId": task_id})
        if err:
            return {"ok": False, "error": err}
        return {"ok": True}

    def get_balance(self):
        """查询账户余额"""
        body, err = _req("POST", f"{BASE_URL}/getBalance",
                         {"clientKey": self.key})
        if err:
            return {"ok": False, "error": err}
        data = _parse(body)
        if data.get("errorId") == 0:
            return {"ok": True, "balance": data.get("balance", 0)}
        return {"ok": False, "error": data.get("errorDescription", "")}

    # ── 便捷方法 (常用验证码类型) ──────────────────────────

    def solve_recaptcha_v2(self, website_url, website_key, proxy=None, is_invisible=False):
        """求解 reCAPTCHA v2 (含 Invisible)"""
        params = {"websiteURL": website_url, "websiteKey": website_key}
        if is_invisible:
            params["isInvisible"] = True
        if proxy:
            params.update(self._format_proxy(proxy))
            return self.solve_and_wait("RecaptchaV2Task", **params)
        return self.solve_and_wait("RecaptchaV2TaskProxyless", **params)

    def solve_recaptcha_v3(self, website_url, website_key, min_score=0.3, action="verify"):
        """求解 reCAPTCHA v3"""
        return self.solve_and_wait("RecaptchaV3TaskProxyless",
                                   websiteURL=website_url,
                                   websiteKey=website_key,
                                   minScore=min_score,
                                   pageAction=action)

    def solve_turnstile(self, website_url, website_key, proxy=None):
        """求解 Cloudflare Turnstile"""
        params = {"websiteURL": website_url, "websiteKey": website_key}
        if proxy:
            params.update(self._format_proxy(proxy))
            return self.solve_and_wait("TurnstileTask", **params)
        return self.solve_and_wait("TurnstileTaskProxyless", **params)

    def solve_funcaptcha(self, website_url, website_public_key, proxy=None, **extra):
        """求解 Arkose Labs FunCaptcha"""
        params = {"websiteURL": website_url, "websitePublicKey": website_public_key}
        params.update(extra)
        if proxy:
            params.update(self._format_proxy(proxy))
            return self.solve_and_wait("FunCaptchaTask", **params)
        return self.solve_and_wait("FunCaptchaTaskProxyless", **params)

    def solve_image(self, image_path=None, image_base64=None, case_sensitive=False,
                    numeric=False, min_len=0, max_len=0, phrase=False, calc=False,
                    lang=None, hint=None):
        """求解普通图片验证码。传入文件路径或base64字符串。"""
        body_b64 = None
        if image_path:
            with open(image_path, "rb") as f:
                body_b64 = base64.b64encode(f.read()).decode("utf-8")
        elif image_base64:
            body_b64 = image_base64
        else:
            return {"ok": False, "error": "image_path or image_base64 required"}

        params = {"body": body_b64}
        if case_sensitive:
            params["regsense"] = 1
        if numeric:
            params["numeric"] = numeric
        if min_len:
            params["min_len"] = min_len
        if max_len:
            params["max_len"] = max_len
        if phrase:
            params["phrase"] = 1
        if calc:
            params["calc"] = 1
        if hint:
            params["textinstructions"] = hint
        if lang:
            params["lang"] = lang

        return self.solve_and_wait("ImageToTextTask", **params)

    def solve_geetest(self, website_url, gt, challenge, api_server=None, proxy=None):
        """求解 GeeTest v3"""
        params = {"websiteURL": website_url, "gt": gt, "challenge": challenge}
        if api_server:
            params["geetestApiServerSubdomain"] = api_server
        if proxy:
            params.update(self._format_proxy(proxy))
            return self.solve_and_wait("GeeTestTask", **params)
        return self.solve_and_wait("GeeTestTaskProxyless", **params)

    def solve_geetest_v4(self, website_url, captcha_id, proxy=None):
        """求解 GeeTest v4"""
        params = {"websiteURL": website_url, "captchaId": captcha_id}
        if proxy:
            params.update(self._format_proxy(proxy))
            return self.solve_and_wait("GeeTestV4Task", **params)
        return self.solve_and_wait("GeeTestV4TaskProxyless", **params)

    def solve_hcaptcha(self, website_url, website_key, proxy=None):
        """求解 hCaptcha"""
        params = {"websiteURL": website_url, "websiteKey": website_key}
        if proxy:
            params.update(self._format_proxy(proxy))
            return self.solve_and_wait("HCaptchaTask", **params)
        return self.solve_and_wait("HCaptchaTaskProxyless", **params)

    def solve_amazon_waf(self, website_url, website_key, proxy=None, **extra):
        """求解 Amazon WAF"""
        params = {"websiteURL": website_url, "websiteKey": website_key}
        params.update(extra)
        if proxy:
            params.update(self._format_proxy(proxy))
            return self.solve_and_wait("AmazonWafTask", **params)
        return self.solve_and_wait("AmazonWafTaskProxyless", **params)

    def solve_datadome(self, website_url, captcha_url, proxy, user_agent):
        """求解 DataDome slider"""
        return self.solve_and_wait("DataDomeSliderTask",
                                   websiteURL=website_url,
                                   captchaUrl=captcha_url,
                                   proxyType=proxy.get("type", "http"),
                                   proxyAddress=proxy.get("host"),
                                   proxyPort=proxy.get("port"),
                                   proxyLogin=proxy.get("login", ""),
                                   proxyPassword=proxy.get("password", ""),
                                   userAgent=user_agent)

    def solve_tencent(self, website_url, app_id, proxy=None):
        """求解 Tencent (TenDI)"""
        params = {"websiteURL": website_url, "appId": app_id}
        if proxy:
            params.update(self._format_proxy(proxy))
            return self.solve_and_wait("TencentTask", **params)
        return self.solve_and_wait("TencentTaskProxyless", **params)

    def solve_binance(self, website_url, website_key, proxy=None):
        """求解 Binance Captcha"""
        params = {"websiteURL": website_url, "websiteKey": website_key}
        if proxy:
            params.update(self._format_proxy(proxy))
            return self.solve_and_wait("BinanceTask", **params)
        return self.solve_and_wait("BinanceTaskProxyless", **params)

    def solve_imperva(self, website_url, website_key, proxy=None, user_agent=None):
        """求解 Imperva (Incapsula)"""
        params = {"websiteURL": website_url, "websiteKey": website_key}
        if user_agent:
            params["userAgent"] = user_agent
        if proxy:
            params.update(self._format_proxy(proxy))
        return self.solve_and_wait("ImpervaTaskProxyless", **params)

    def solve_yandex(self, website_url, website_key, proxy=None):
        """求解 Yandex SmartCaptcha"""
        params = {"websiteURL": website_url, "websiteKey": website_key}
        if proxy:
            params.update(self._format_proxy(proxy))
            return self.solve_and_wait("YandexTask", **params)
        return self.solve_and_wait("YandexTaskProxyless", **params)

    def solve_audio(self, audio_path=None, audio_base64=None, lang="en"):
        """求解音频验证码"""
        body_b64 = None
        if audio_path:
            with open(audio_path, "rb") as f:
                body_b64 = base64.b64encode(f.read()).decode("utf-8")
        elif audio_base64:
            body_b64 = audio_base64
        else:
            return {"ok": False, "error": "audio_path or audio_base64 required"}
        return self.solve_and_wait("AudioCaptchaTask", body=body_b64, lang=lang)

    def solve_coordinates(self, image_path=None, image_base64=None, comment=None):
        """求解点击验证码 (返回点击坐标)"""
        body_b64 = None
        if image_path:
            with open(image_path, "rb") as f:
                body_b64 = base64.b64encode(f.read()).decode("utf-8")
        elif image_base64:
            body_b64 = image_base64
        else:
            return {"ok": False, "error": "image_path or image_base64 required"}
        params = {"body": body_b64}
        if comment:
            params["comment"] = comment
        return self.solve_and_wait("CoordinatesTask", **params)

    # ── 辅助 ──────────────────────────────────────────────

    def _format_proxy(self, proxy):
        """将 proxy dict 转为 2Captcha API 格式"""
        # proxy: {"type": "http", "host": "1.2.3.4", "port": 8080, "login": "...", "password": "..."}
        return {
            "proxyType": proxy.get("type", "http"),
            "proxyAddress": proxy.get("host"),
            "proxyPort": int(proxy.get("port", 8080)),
            "proxyLogin": proxy.get("login", ""),
            "proxyPassword": proxy.get("password", ""),
        }


# ═══════════════════════════════════════════════════════════
#  2. ProxyNetwork — 住宅代理网络
# ═══════════════════════════════════════════════════════════

class ProxyNetwork:
    """2Captcha 住宅代理网络 — 220+国家真实住宅IP"""

    def __init__(self, api_key=None):
        self.key = api_key or _get_key()

    def account_info(self):
        """获取代理账户信息（流量使用、白名单IP）"""
        body, err = _req("GET", f"{BASE_URL}/proxy?key={self.key}")
        if err:
            return {"ok": False, "error": err}
        data = _parse(body)
        if data.get("status") == "OK":
            return {"ok": True, "data": data.get("data", {})}
        return {"ok": False, "error": str(data)}

    def balance(self):
        """查询代理余额"""
        body, err = _req("GET", f"{BASE_URL}/proxy/balance?key={self.key}")
        if err:
            return {"ok": False, "error": err}
        data = _parse(body)
        if data.get("status") == "OK":
            return {"ok": True, "balance": data.get("balance", 0)}
        return {"ok": False, "error": str(data)}

    def list_countries(self, page=0):
        """列出可用国家 (208个)"""
        body, err = _req("GET",
                         f"{BASE_URL}/proxy/locations/countries?key={self.key}&page={page}")
        if err:
            return {"ok": False, "error": err}
        data = _parse(body)
        if data.get("status") == "OK":
            return {"ok": True, "countries": data.get("data", []), "total": data.get("total", 0)}
        return {"ok": False, "error": str(data)}

    def list_regions(self, page=0):
        """列出可用地区 (967个)"""
        body, err = _req("GET",
                         f"{BASE_URL}/proxy/locations/regions?key={self.key}&page={page}")
        if err:
            return {"ok": False, "error": err}
        data = _parse(body)
        if data.get("status") == "OK":
            return {"ok": True, "regions": data.get("data", []), "total": data.get("total", 0)}
        return {"ok": False, "error": str(data)}

    def list_cities(self, page=0):
        """列出可用城市 (3145个)"""
        body, err = _req("GET",
                         f"{BASE_URL}/proxy/locations/cities?key={self.key}&page={page}")
        if err:
            return {"ok": False, "error": err}
        data = _parse(body)
        if data.get("status") == "OK":
            return {"ok": True, "cities": data.get("data", []), "total": data.get("total", 0)}
        return {"ok": False, "error": str(data)}

    def list_asns(self, page=0):
        """列出可用ASN（运营商级）"""
        body, err = _req("GET",
                         f"{BASE_URL}/proxy/locations/asns?key={self.key}&page={page}")
        if err:
            return {"ok": False, "error": err}
        data = _parse(body)
        if data.get("status") == "OK":
            return {"ok": True, "asns": data.get("data", []), "total": data.get("total", 0)}
        return {"ok": False, "error": str(data)}

    def generate_whitelist(self):
        """生成白名单连接IP"""
        body, err = _req("POST",
                         f"{BASE_URL}/proxy/whitelist?key={self.key}",
                         {"key": self.key})
        if err:
            return {"ok": False, "error": err}
        data = _parse(body)
        return {"ok": True, "data": data}


# ═══════════════════════════════════════════════════════════
#  3. FingerprintAPI — 浏览器指纹
# ═══════════════════════════════════════════════════════════

class FingerprintAPI:
    """2Captcha 浏览器指纹API — 真实浏览器指纹生成

    订阅制: Start $29/mo → Unlimited $199/mo
    """

    def __init__(self, api_key=None):
        self.key = api_key or _get_key()

    def random(self, tags=None, country=None, browser_version=None,
               min_browser_version=None, fmt="chromium", force_version=False):
        """获取随机真实浏览器指纹。

        tags: 平台/OS过滤 ["Windows", "Android", "iOS", "macOS", "Linux"]
        country: ISO 3166-1 alpha-2 (如 "us", "de", "jp")
        browser_version: 特定浏览器主版本号
        min_browser_version: 最低浏览器主版本
        fmt: "chromium" (默认，Playwright/Puppeteer兼容) 或 "raw"
        """
        params = f"key={self.key}&format={fmt}"
        if tags:
            if isinstance(tags, list):
                params += "&" + "&".join(f"tags={t}" for t in tags)
            else:
                params += f"&tags={tags}"
        if country:
            params += f"&country={country}"
        if browser_version:
            params += f"&browser_version={browser_version}"
        if min_browser_version:
            params += f"&min_browser_version={min_browser_version}"
        if force_version:
            params += f"&force_browser_version={browser_version or min_browser_version}"

        body, err = _req("GET",
                         f"{BASE_URL}/fingerprint/random?{params}")
        if err:
            return {"ok": False, "error": err}
        data = _parse(body)
        if "errorCode" in data:
            return {"ok": False, "error": data.get("error", data["errorCode"])}
        return {"ok": True, "fingerprint": data}

    def generate(self, tags=None, country=None, browser_version=None,
                 build_version=None, min_browser_version=None, fmt="chromium"):
        """按参数生成定制浏览器指纹。"""
        params = f"key={self.key}&format={fmt}"
        if tags:
            if isinstance(tags, list):
                params += "&" + "&".join(f"tags={t}" for t in tags)
            else:
                params += f"&tags={tags}"
        if country:
            params += f"&country={country}"
        if browser_version:
            params += f"&browser_version={browser_version}"
        if build_version:
            params += f"&build_version={build_version}"
        if min_browser_version:
            params += f"&min_browser_version={min_browser_version}"

        body, err = _req("GET",
                         f"{BASE_URL}/fingerprint/generate?{params}")
        if err:
            return {"ok": False, "error": err}
        data = _parse(body)
        if "errorCode" in data:
            return {"ok": False, "error": data.get("error", data["errorCode"])}
        return {"ok": True, "fingerprint": data}


    # ── 指纹字段提取器 ───────────────────────────────────

    def extract_ua(self, fp_data):
        """从指纹数据中提取 User-Agent 字符串"""
        ua = fp_data.get("userAgent", {})
        return ua.get("value", ua.get("userAgent", ""))

    def extract_platform(self, fp_data):
        """提取操作系统平台"""
        ua = fp_data.get("userAgent", {})
        nav = fp_data.get("navigator", {})
        return ua.get("platform", nav.get("platform", ""))

    def extract_screen(self, fp_data):
        """提取屏幕信息 {width, height, deviceScaleFactor}"""
        s = fp_data.get("screen", {})
        return {
            "width": s.get("width", 1920),
            "height": s.get("height", 1080),
            "deviceScaleFactor": s.get("deviceScaleFactor", 1),
        }

    def extract_navigator(self, fp_data):
        """提取 navigator 属性 (hardwareConcurrency, deviceMemory, platform)"""
        n = fp_data.get("navigator", {})
        return {
            "hardwareConcurrency": n.get("hardwareConcurrency", 4),
            "deviceMemory": n.get("deviceMemory", 4),
            "platform": n.get("platform", ""),
        }

    def extract_webgl(self, fp_data):
        """提取 WebGL 完整配置 (vendor, renderer, extensions, parameters)"""
        w = fp_data.get("webgl", {})
        return {
            "vendor": w.get("vendor", ""),
            "renderer": w.get("renderer", ""),
            "extensions": w.get("glAvailableExtensions", []),
            "parameters": w.get("glParameters", {}),
        }

    def extract_webgpu(self, fp_data):
        """提取 WebGPU 信息"""
        w = fp_data.get("webgpu", {})
        hp = w.get("highPerformance", {})
        return {
            "available": bool(hp),
            "adapter": hp.get("adapter", {}),
        }

    def extract_voices(self, fp_data):
        """提取语音合成声音列表 [{name, lang, isDefault}]"""
        ss = fp_data.get("speechSynthesis", {})
        return ss.get("voices", [])

    def extract_intl(self, fp_data):
        """提取国际化设置 (languages, timeZone)"""
        i = fp_data.get("intl", {})
        return {
            "languages": i.get("languages", ["en-US"]),
            "timeZone": i.get("timeZone", "America/New_York"),
        }

    def extract_canvas_hash(self, fp_data):
        """提取 Canvas 指纹哈希 (仅 raw 格式)"""
        d = fp_data.get("data", fp_data)
        return d.get("canvas", "")

    def extract_fonts(self, fp_data):
        """提取系统字体列表 (仅 raw 格式)"""
        d = fp_data.get("data", fp_data)
        return d.get("fonts", [])

    def extract_visitor_id(self, fp_data):
        """提取访问者ID (仅 raw 格式)"""
        d = fp_data.get("data", fp_data)
        return d.get("visitor_id", "")

    def extract_country(self, fp_data):
        """提取指纹对应的国家码"""
        return fp_data.get("country", "")

    # ── 完整配置文件生成器 ─────────────────────────────────

    def get_puppeteer_context(self, tags=None, country=None, fmt="chromium"):
        """生成 Puppeteer-ready 浏览器启动参数和上下文配置。

        返回可直接传给 puppeteer.launch() + browser.createIncognitoBrowserContext() 的参数。
        """
        fp = self.random(tags=tags, country=country, fmt=fmt)
        if not fp["ok"]:
            return fp
        f = fp["fingerprint"]
        ua = self.extract_ua(f)
        screen = self.extract_screen(f)
        intl = self.extract_intl(f)
        nav = self.extract_navigator(f)
        webgl = self.extract_webgl(f)
        return {
            "ok": True,
            "launch_args": [
                f"--window-size={screen['width']},{screen['height']}",
                f"--user-agent={ua}",
            ],
            "context": {
                "viewport": {"width": screen["width"], "height": screen["height"]},
                "userAgent": ua,
                "locale": intl["languages"][0] if intl["languages"] else "en-US",
                "timezoneId": intl["timeZone"],
                "deviceScaleFactor": screen.get("deviceScaleFactor", 1),
            },
            "fingerprint": f,
            "extracted": {
                "screen": screen, "navigator": nav, "webgl": webgl,
                "intl": intl, "ua": ua, "platform": self.extract_platform(f),
                "voices": self.extract_voices(f), "country": self.extract_country(f),
            },
        }

    def get_stealth_config(self, tags=None, country=None, fmt="chromium"):
        """生成完整隐身配置 — 可用于 Playwright / Puppeteer / Selenium / CDP。

        返回:
          - launch_args: 浏览器启动参数
          - context: browser.new_context() 参数
          - cdp_scripts: 页面注入脚本 (反检测)
          - headers: 额外HTTP请求头
          - fingerprint: 原始指纹数据
          - extracted: 所有提取字段的汇总
        """
        fp = self.random(tags=tags, country=country, fmt=fmt)
        if not fp["ok"]:
            return fp
        f = fp["fingerprint"]
        ua = self.extract_ua(f)
        screen = self.extract_screen(f)
        intl = self.extract_intl(f)
        nav = self.extract_navigator(f)
        webgl = self.extract_webgl(f)
        voices = self.extract_voices(f)
        platform = self.extract_platform(f)
        country_code = self.extract_country(f)
        # Accept-Language 头
        accept_lang = ",".join(
            f"{l};q={1.0 - i * 0.1:.1f}" if i > 0 else l
            for i, l in enumerate(intl["languages"])
        ) if intl["languages"] else "en-US,en;q=0.9"
        # Sec-CH-UA 头
        sec_ch_ua = f'"Chromium";v="{f.get("browserVersion", "126")}", "Google Chrome";v="{f.get("browserVersion", "126")}", "Not=A?Brand";v="99"'
        config = {
            "ok": True,
            "fingerprint": f,
            "launch_args": [
                f"--window-size={screen['width']},{screen['height']}",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
            "context": {
                "viewport": {"width": screen["width"], "height": screen["height"]},
                "user_agent": ua,
                "locale": intl["languages"][0] if intl["languages"] else "en-US",
                "timezone_id": intl["timeZone"],
                "device_scale_factor": screen.get("deviceScaleFactor", 1),
                "geolocation": {"latitude": 40.7128, "longitude": -74.0060},
                "permissions": ["geolocation"],
            },
            "headers": {
                "User-Agent": ua,
                "Accept-Language": accept_lang,
                "Sec-CH-UA": sec_ch_ua,
                "Sec-CH-UA-Platform": f'"{platform}"' if platform else '"Windows"',
                "Sec-CH-UA-Mobile": "?0",
            },
            "cdp_scripts": {
                "hide_webdriver": 'Object.defineProperty(navigator,"webdriver",{get:()=>undefined})',
                "fake_plugins": f'navigator.plugins.length > 0 || Object.defineProperty(navigator,"plugins",{{get:()=>[{nav["hardwareConcurrency"]}]}})',
                "fake_languages": f'Object.defineProperty(navigator,"languages",{{get:()=>{json.dumps(intl["languages"])}}})',
            },
            "extracted": {
                "ua": ua, "platform": platform, "screen": screen,
                "navigator": nav, "webgl": webgl, "intl": intl,
                "voices": voices, "country": country_code,
                "accept_language": accept_lang, "sec_ch_ua": sec_ch_ua,
            },
        }
        return config

    def get_browser_headers(self, tags=None, country=None):
        """仅生成真实浏览器HTTP请求头 (含 UA, Accept-Language, Sec-CH-UA 等)"""
        fp = self.random(tags=tags, country=country, fmt="chromium")
        if not fp["ok"]:
            return fp
        f = fp["fingerprint"]
        ua = self.extract_ua(f)
        intl = self.extract_intl(f)
        platform = self.extract_platform(f)
        accept_lang = ",".join(
            f"{l};q={1.0 - i * 0.1:.1f}" if i > 0 else l
            for i, l in enumerate(intl["languages"])
        ) if intl["languages"] else "en-US,en;q=0.9"
        return {
            "ok": True,
            "headers": {
                "User-Agent": ua,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": accept_lang,
                "Accept-Encoding": "gzip, deflate, br",
                "Sec-CH-UA": f'"Chromium";v="126", "Google Chrome";v="126", "Not=A?Brand";v="99"',
                "Sec-CH-UA-Platform": f'"{platform}"' if platform else '"Windows"',
                "Sec-CH-UA-Mobile": "?0",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
            },
            "extracted": {"ua": ua, "platform": platform, "intl": intl},
        }

    def get_playwright_context(self, tags=None, country=None, fmt="chromium"):
        """生成Playwright-ready浏览器上下文配置 (全字段版)。"""
        fp = self.random(tags=tags, country=country, fmt=fmt)
        if not fp["ok"]:
            return fp
        f = fp["fingerprint"]
        ua = self.extract_ua(f)
        screen = self.extract_screen(f)
        intl = self.extract_intl(f)
        nav = self.extract_navigator(f)
        webgl = self.extract_webgl(f)
        voices = self.extract_voices(f)
        platform = self.extract_platform(f)
        ctx = {
            "viewport": {"width": screen["width"], "height": screen["height"]},
            "user_agent": ua,
            "locale": intl["languages"][0] if intl["languages"] else "en-US",
            "timezone_id": intl["timeZone"],
            "device_scale_factor": screen.get("deviceScaleFactor", 1),
            "geolocation": {"latitude": 40.7128, "longitude": -74.0060},
            "permissions": ["geolocation"],
        }
        return {
            "ok": True,
            "context": ctx,
            "fingerprint": f,
            "extracted": {
                "ua": ua, "platform": platform, "screen": screen,
                "navigator": nav, "webgl": webgl, "intl": intl,
                "voices": voices, "country": self.extract_country(f),
            },
        }

    def get_complete_profile(self, tags=None, country=None, fmt="chromium"):
        """获取完整指纹档案 — 所有字段的汇总输出。

        包含: screen, navigator, webgl, webgpu, voices, intl, canvas, fonts, visitor_id
        """
        fp = self.random(tags=tags, country=country, fmt=fmt)
        if not fp["ok"]:
            return fp
        f = fp["fingerprint"]
        profile = {
            "ok": True,
            "fingerprint_id": f.get("id", ""),
            "country": self.extract_country(f),
            "screen": self.extract_screen(f),
            "user_agent": self.extract_ua(f),
            "platform": self.extract_platform(f),
            "navigator": self.extract_navigator(f),
            "webgl": self.extract_webgl(f),
            "webgpu": self.extract_webgpu(f),
            "speech_voices": self.extract_voices(f),
            "intl": self.extract_intl(f),
            "canvas_hash": self.extract_canvas_hash(f),
            "fonts": self.extract_fonts(f),
            "visitor_id": self.extract_visitor_id(f),
            "raw_fingerprint": f,
        }
        return profile


# ═══════════════════════════════════════════════════════════
#  4. CloudBrowser — 云端CDP浏览器
# ═══════════════════════════════════════════════════════════

class CloudBrowser:
    """2Captcha 云端CDP浏览器 — Playwright/Puppeteer远程连接

    在2Captcha云端运行真实Chrome，通过CDP WebSocket直连。
    代理、国家、验证码自动处理。
    """

    def __init__(self, api_key=None):
        self.key = api_key or _get_key()

    # ── 账户管理 ──────────────────────────────────────────

    def account_status(self):
        """获取Browser API账户状态（流量、限制）"""
        body, err = _req("GET", f"{BASE_URL}/browser?key={self.key}")
        if err:
            return {"ok": False, "error": err}
        data = _parse(body)
        if data.get("status") == "OK":
            return {"ok": True, "status": data}
        return {"ok": False, "error": str(data)}

    def list_accounts(self):
        """列出浏览器账户"""
        body, err = _req("GET", f"{BASE_URL}/browser/accounts?key={self.key}")
        if err:
            return {"ok": False, "error": err}
        data = _parse(body)
        if data.get("status") == "OK":
            return {"ok": True, "accounts": data.get("data", data.get("accounts", []))}
        return {"ok": False, "error": str(data)}

    def create_account(self, name, proxy_mode="none", country="us",
                       custom_proxy=None, proxy_account_id=None):
        """创建浏览器账户。

        proxy_mode: "none" | "our_proxy" | "custom_proxy"
        country: ISO国家码 (our_proxy模式)
        custom_proxy: {"type":"http","host":"...","port":8080,"login":"...","password":"..."}
        """
        payload = {"key": self.key, "name": name, "proxyMode": proxy_mode}
        if proxy_mode == "our_proxy" and country:
            payload["country"] = country
        if proxy_account_id:
            payload["proxyAccountId"] = proxy_account_id
        if custom_proxy:
            payload["customProxy"] = custom_proxy
        body, err = _req("POST", f"{BASE_URL}/browser/accounts", payload)
        if err:
            return {"ok": False, "error": err}
        data = _parse(body)
        if data.get("status") == "OK":
            return {"ok": True, "account": data.get("account", {})}
        return {"ok": False, "error": data.get("error", str(data))}

    def delete_account(self, account_id):
        """删除浏览器账户"""
        body, err = _req("DELETE",
                         f"{BASE_URL}/browser/accounts/{account_id}",
                         {"key": self.key})
        if err:
            return {"ok": False, "error": err}
        return {"ok": True}

    # ── Profile管理 ───────────────────────────────────────

    def list_profiles(self, account_id=None):
        """列出浏览器Profiles"""
        url = f"{BASE_URL}/browser/profiles?key={self.key}"
        if account_id:
            url += f"&accountId={account_id}"
        body, err = _req("GET", url)
        if err:
            return {"ok": False, "error": err}
        data = _parse(body)
        if data.get("status") == "OK":
            return {"ok": True, "profiles": data.get("data", data.get("profiles", []))}
        return {"ok": False, "error": str(data)}

    def create_profile(self, account_id, name="", proxy_mode="inherit",
                       country=None, custom_proxy=None):
        """创建浏览器Profile"""
        payload = {"key": self.key, "accountId": account_id, "proxyMode": proxy_mode}
        if name:
            payload["name"] = name
        if country:
            payload["country"] = country
        if custom_proxy:
            payload["customProxy"] = custom_proxy
        body, err = _req("POST", f"{BASE_URL}/browser/profiles", payload)
        if err:
            return {"ok": False, "error": err}
        data = _parse(body)
        if data.get("status") == "OK":
            return {"ok": True, "profile": data.get("profile", {})}
        return {"ok": False, "error": data.get("error", str(data))}

    def delete_profile(self, profile_id):
        """删除Profile"""
        body, err = _req("DELETE",
                         f"{BASE_URL}/browser/profiles/{profile_id}",
                         {"key": self.key})
        if err:
            return {"ok": False, "error": err}
        return {"ok": True}

    # ── 连接 ──────────────────────────────────────────────

    def get_connection(self, account_id, profile_id=None,
                       custom_proxy=None, device_type=None,
                       captcha_mode="auto"):
        """获取CDP WebSocket连接URL。

        account_id: 浏览器账户ID
        profile_id: 可选profile ID
        custom_proxy: 连接时传入的自定义代理
        device_type: "windows" | "android"
        captcha_mode: "auto" (clickcaptcha) | "none" (nocaptcha) | None (默认)

        返回可以直接传给 playwright.chromium.connectOverCDP() 的URL。
        """
        payload = {"key": self.key, "accountId": account_id}
        if profile_id:
            payload["profileId"] = profile_id
        if custom_proxy:
            payload["customProxy"] = custom_proxy
        body, err = _req("POST", f"{BASE_URL}/browser/connection", payload)
        if err:
            return {"ok": False, "error": err}
        data = _parse(body)
        if data.get("status") == "OK":
            uri = data.get("connectionUri", "")
            # append device_type / captcha flags if needed
            if device_type or captcha_mode:
                uri = self._patch_uri(uri, device_type, captcha_mode)
            return {"ok": True, "connectionUri": uri}
        return {"ok": False, "error": data.get("error", str(data))}

    def _patch_uri(self, uri, device_type=None, captcha_mode=None):
        """在WebSocket URL的用户名部分追加参数"""
        # ws://username:password@host:port
        if "://" not in uri or "@" not in uri:
            return uri
        proto, rest = uri.split("://", 1)
        creds, hostpart = rest.split("@", 1)
        username, password = creds.rsplit(":", 1)
        if device_type:
            username += f"-dt-{device_type}"
        if captcha_mode == "auto":
            username += "-clickcaptcha"
        elif captcha_mode == "none":
            username += "-nocaptcha"
        return f"{proto}://{username}:{password}@{hostpart}"

    def get_statistics(self):
        """获取流量统计"""
        body, err = _req("GET", f"{BASE_URL}/browser/statistics?key={self.key}")
        if err:
            return {"ok": False, "error": err}
        data = _parse(body)
        if data.get("status") == "OK":
            return {"ok": True, "statistics": data.get("statistics", data)}
        return {"ok": False, "error": str(data)}

    # ── 便捷：创建完整浏览器会话 ───────────────────────────

    def create_session(self, name="GBT Session", country="us",
                       proxy_mode="none", custom_proxy=None,
                       captcha_mode="auto", device_type="windows"):
        """一键创建完整浏览器会话（账户+Profile+CDP URL）。

        返回可以直接传给 Playwright/Puppeteer 的连接URL。
        """
        # 1. 创建账户
        acc = self.create_account(name, proxy_mode=proxy_mode,
                                  country=country, custom_proxy=custom_proxy)
        if not acc["ok"]:
            return acc
        account = acc["account"]
        # 2. 获取连接（使用Default profile）
        conn = self.get_connection(account["id"],
                                   custom_proxy=custom_proxy,
                                   device_type=device_type,
                                   captcha_mode=captcha_mode)
        if not conn["ok"]:
            return conn
        return {
            "ok": True,
            "accountId": account["id"],
            "login": account.get("login", ""),
            "password": account.get("password", ""),
            "connectionUri": conn["connectionUri"],
        }


# ═══════════════════════════════════════════════════════════
#  全局单例
# ═══════════════════════════════════════════════════════════

_solver = None
_proxy = None
_fingerprint = None
_browser = None


def get_solver() -> CaptchaSolver:
    global _solver
    if _solver is None:
        _solver = CaptchaSolver()
    return _solver


def get_proxy() -> ProxyNetwork:
    global _proxy
    if _proxy is None:
        _proxy = ProxyNetwork()
    return _proxy


def get_fingerprint() -> FingerprintAPI:
    global _fingerprint
    if _fingerprint is None:
        _fingerprint = FingerprintAPI()
    return _fingerprint


def get_browser() -> CloudBrowser:
    global _browser
    if _browser is None:
        _browser = CloudBrowser()
    return _browser
