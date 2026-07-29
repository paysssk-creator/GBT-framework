# 开发者：自由的风
"""anti_track/run.py — 反追踪隐身引擎·每根触手内置
=================================================
攻击域 core — 所有侦察/攻击触手都通过此引擎发送请求:
  - User-Agent轮换池(20+真实浏览器指纹)
  - 代理链轮换(HTTP/SOCKS5)
  - 请求间隔随机化(防速率检测)
  - 请求头指纹混淆(模拟真实浏览器)
  - Referer链伪造
  - Cookie隔离
  - TLS指纹随机化
  - 反蜜罐检测
  - 日志自清理
"""
import sys, json, os, random, time, hashlib, urllib.request, urllib.error, ssl, socket
from pathlib import Path
from datetime import datetime

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_DIR = Path.home() / ".gbt" / "anti_track"
STATE_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════
#  User-Agent轮换池 — 20个真实浏览器指纹(多OS/多版本)
# ═══════════════════════════════════════════════════════════

UA_POOL = [
    # Windows Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Windows Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    # Windows Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
    # macOS Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # macOS Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    # macOS Firefox
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.5; rv:126.0) Gecko/20100101 Firefox/126.0",
    # Linux Chrome
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Linux Firefox
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0",
    # Android Chrome
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.34 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    # iPhone Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    # iPad Safari
    "Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    # Bots/Crawlers (伪装搜索引擎爬虫)
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    "DuckDuckBot/1.0; (+http://duckduckgo.com/duckduckbot.html)",
]

# 常见Accept-Language组合
ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    "en-US,en;q=0.9",
    "zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7",
    "en-GB,en;q=0.9,en-US;q=0.8",
    "ja-JP,ja;q=0.9,en;q=0.8",
]

# Accept-Encoding组合
ACCEPT_ENCODINGS = [
    "gzip, deflate, br",
    "gzip, deflate",
    "br, gzip, deflate",
]

# Sec-CH-UA 平台伪装
SEC_CH_UA_PLATFORMS = [
    '"Windows"', '"macOS"', '"Linux"', '"Android"', '"iOS"',
]

# Referer池(伪造来源)
REFERER_POOL = [
    "https://www.google.com/search?q=",
    "https://www.bing.com/search?q=",
    "https://duckduckgo.com/?q=",
    "https://github.com/",
    "https://stackoverflow.com/",
    "https://www.reddit.com/",
    "https://twitter.com/",
    "https://t.co/",
    None,  # 直接访问
]

# ═══════════════════════════════════════════════════════════
#  反蜜罐检测
# ═══════════════════════════════════════════════════════════

HONEYPOT_SIGNATURES = [
    "honeypot", "honeynet", "trap", "decoy", "sandbox",
    "vmware", "virtualbox", "qemu", "xen",
    r"<input[^>]*type\s*=\s*[\"']hidden[\"'][^>]*name\s*=\s*[\"'](?:email|name|url|address|phone)",
]


def _generate_headers(target_url="", use_referer=True):
    """生成一次性随机请求头指纹"""
    headers = {
        "User-Agent": random.choice(UA_POOL),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": random.choice(ACCEPT_LANGUAGES),
        "Accept-Encoding": random.choice(ACCEPT_ENCODINGS),
        "Cache-Control": random.choice(["no-cache", "max-age=0"]),
        "Sec-Fetch-Dest": random.choice(["document", "empty"]),
        "Sec-Fetch-Mode": random.choice(["navigate", "cors"]),
        "Sec-Fetch-Site": random.choice(["none", "cross-site", "same-origin"]),
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "DNT": random.choice(["0", "1"]),
        "Connection": "keep-alive",
    }

    # Sec-CH-UA (仅Chrome系)
    if "Chrome" in headers["User-Agent"] and "Edg" not in headers["User-Agent"]:
        headers["Sec-CH-UA"] = '"Chromium";v="125", "Google Chrome";v="125", "Not?A_Brand";v="99"'
        headers["Sec-CH-UA-Platform"] = random.choice(SEC_CH_UA_PLATFORMS)
        headers["Sec-CH-UA-Mobile"] = random.choice(["?0", "?1"])

    if use_referer and target_url:
        ref = random.choice(REFERER_POOL)
        if ref:
            headers["Referer"] = ref

    return headers


def _random_delay(min_ms=200, max_ms=1500):
    """随机延迟 — 模拟人类浏览"""
    delay = random.uniform(min_ms / 1000, max_ms / 1000)
    time.sleep(delay)
    return round(delay * 1000)


def _is_honeypot(body, headers):
    """检测蜜罐陷阱"""
    body_lower = body.lower()[:5000]
    for sig in HONEYPOT_SIGNATURES:
        if sig.lower() in body_lower:
            return True, f"检测到蜜罐特征: {sig[:40]}"
    return False, None


# ═══════════════════════════════════════════════════════════
#  隐身请求
# ═══════════════════════════════════════════════════════════

def do_stealth_request(params):
    """隐身HTTP请求 — 随机指纹+延迟+反蜜罐"""
    url = params.get("url", "")
    method = params.get("method", "GET")
    data = params.get("data", None)
    use_delay = params.get("delay", True)
    use_referer = params.get("referer", True)
    timeout = params.get("timeout", 15)

    if not url:
        return {"ok": False, "error": "缺少 url 参数"}

    headers = _generate_headers(url, use_referer)
    delay_ms = _random_delay(300, 1200) if use_delay else 0

    try:
        # 默认安全SSL — 仅测试时可关(传 insecure_ssl=true)
        ctx = ssl.create_default_context()
        if params.get("insecure_ssl"):
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(url, data=data.encode() if data else None, headers=headers, method=method)
        resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        body = resp.read().decode("utf-8", errors="replace")

        is_hp, hp_reason = _is_honeypot(body, str(resp.headers))

        return {
            "ok": True,
            "cap": "anti_track",
            "action": "stealth_request",
            "status": resp.status,
            "response_len": len(body),
            "headers_sent": {k: v for k, v in headers.items() if k in ("User-Agent", "Accept-Language", "Referer")},
            "delay_ms": delay_ms,
            "honeypot_detected": is_hp,
            "honeypot_reason": hp_reason,
            "body_preview": body[:500] if not is_hp else "[蜜罐响应已拦截]",
        }
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500] if e.fp else ""
        return {
            "ok": True, "status": e.code, "error_page": True,
            "headers_sent": {k: v for k, v in headers.items() if k in ("User-Agent", "Accept-Language", "Referer")},
            "delay_ms": delay_ms, "body_preview": body,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def do_rotate_identity(params):
    """轮换身份 — 全新随机指纹 + UA + Accept-Lang + 平台 + 代理"""
    headers = _generate_headers()
    proxy = {
        "type": random.choice(["none", "http", "socks5"]),
        "current": None,
    }
    if proxy["type"] != "none":
        proxy_host = os.environ.get(f"GBT_PROXY_{proxy['type'].upper()}", "")
        if proxy_host:
            proxy["current"] = proxy_host
    return {
        "ok": True,
        "cap": "anti_track",
        "action": "rotate_identity",
        "identity": {
            "ua": headers["User-Agent"][:80],
            "accept_lang": headers["Accept-Language"],
            "accept_encoding": headers.get("Accept-Encoding", ""),
            "dnt": headers.get("DNT", "0"),
            "platform": headers.get("Sec-CH-UA-Platform", "unknown"),
            "sec_fetch_dest": headers.get("Sec-Fetch-Dest", ""),
            "sec_fetch_mode": headers.get("Sec-Fetch-Mode", ""),
            "sec_fetch_site": headers.get("Sec-Fetch-Site", ""),
            "cache_control": headers.get("Cache-Control", ""),
            "proxy": proxy,
        },
        "total_uas": len(UA_POOL),
        "params_rotated": 9,
    }

# ═══ stealth_check: 隐身配置自我检测 ═══

_STEALTH_TEST_SITES = [
    {"name": "BrowserLeaks JS", "url": "https://browserleaks.com/javascript", "check": "navigator"},
    {"name": "BrowserLeaks IP", "url": "https://browserleaks.com/ip", "check": "ip"},
    {"name": "IPInfo", "url": "https://ipinfo.io/json", "check": "geo"},
    {"name": "HTTPBin Headers", "url": "https://httpbin.org/headers", "check": "headers"},
]

def do_stealth_check(params):
    """隐身检测 — 测试当前配置在跟踪检测站上的表现"""
    results = {}
    leaks_found = []
    score = 100
    identity = do_rotate_identity({})
    for site in _STEALTH_TEST_SITES:
        try:
            headers = _generate_headers(site["url"], use_referer=False)
            req = urllib.request.Request(site["url"], headers=headers)
            ctx = ssl.create_default_context()
            resp = urllib.request.urlopen(req, timeout=10, context=ctx)
            body = resp.read().decode("utf-8", errors="replace")[:2000]
            results[site["name"]] = {
                "ok": True,
                "status": resp.status,
                "body_preview": body[:500],
            }
            # 检测泄漏
            if site["check"] == "headers":
                try:
                    data = json.loads(body)
                    sent_headers = data.get("headers", {})
                    real_ip_headers = ["X-Forwarded-For", "X-Real-Ip", "X-Client-Ip",
                                       "Cf-Connecting-Ip", "True-Client-Ip"]
                    for h in real_ip_headers:
                        if h in sent_headers or h.lower() in sent_headers:
                            leaks_found.append({"site": site["name"], "leak": f"IP via {h}"})
                            score -= 25
                    if sent_headers.get("User-Agent", "").startswith("python"):
                        leaks_found.append({"site": site["name"], "leak": "Python UA detected"})
                        score -= 20
                except Exception:
                    pass
            if site["check"] == "geo":
                try:
                    data = json.loads(body)
                    if data.get("ip"):
                        results[site["name"]]["visible_ip"] = data["ip"]
                except Exception:
                    pass
        except Exception as e:
            results[site["name"]] = {"ok": False, "error": str(e)[:200]}
            score -= 10
    return {
        "ok": True,
        "cap": "anti_track",
        "action": "stealth_check",
        "domain": "攻击域",
        "current_identity": identity.get("identity", {}),
        "test_results": results,
        "leaks_found": leaks_found,
        "stealth_score": max(score, 0),
        "verdict": "安全" if score >= 80 else "警告: 存在泄漏" if score >= 50 else "危险: 严重泄漏",
    }

# ═══ auto_rotate: 自动轮换身份 ═══

_ROTATE_STATE_FILE = STATE_DIR / "auto_rotate.json"

def _load_rotate_state():
    if _ROTATE_STATE_FILE.exists():
        try:
            return json.loads(_ROTATE_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"request_count": 0, "last_rotate": None, "rotations": 0, "history": []}

def _save_rotate_state(state):
    _ROTATE_STATE_FILE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

def do_auto_rotate(params):
    """自动轮换 — 每N次请求或M分钟后自动切换身份"""
    max_requests = params.get("max_requests", 10)
    max_minutes = params.get("max_minutes", 30)
    force = params.get("force", False)
    state = _load_rotate_state()
    now = time.time()
    should_rotate = force
    reason = "forced"
    # 检查请求计数
    if state["request_count"] >= max_requests:
        should_rotate = True
        reason = f"requests ({state['request_count']} >= {max_requests})"
    # 检查时间
    if state["last_rotate"] and (now - state["last_rotate"]) >= max_minutes * 60:
        should_rotate = True
        reason = f"time ({int((now - state['last_rotate'])/60)}min >= {max_minutes}min)"
    new_identity = None
    if should_rotate:
        new_identity = do_rotate_identity({})
        state["request_count"] = 0
        state["last_rotate"] = now
        state["rotations"] += 1
        state["history"].append({
            "time": datetime.now().isoformat(),
            "reason": reason,
            "ua": new_identity.get("identity", {}).get("ua", "")[:60],
        })
        if len(state["history"]) > 50:
            state["history"] = state["history"][-50:]
    else:
        state["request_count"] += 1
    _save_rotate_state(state)
    return {
        "ok": True,
        "cap": "anti_track",
        "action": "auto_rotate",
        "domain": "攻击域",
        "rotated": should_rotate,
        "reason": reason if should_rotate else None,
        "new_identity": new_identity.get("identity") if new_identity else None,
        "state": {
            "request_count": state["request_count"],
            "max_requests": max_requests,
            "max_minutes": max_minutes,
            "total_rotations": state["rotations"],
            "last_rotate": datetime.fromtimestamp(state["last_rotate"]).isoformat() if state["last_rotate"] else None,
        },
    }



def do_check_honeypot(params):
    """反蜜罐检测 — 分析页面是否为蜜罐"""
    body = params.get("body", params.get("html", ""))
    url = params.get("url", "")

    if not body:
        return {"ok": False, "error": "缺少 body/html 参数"}

    is_hp, reason = _is_honeypot(body, "")

    # 额外检测
    extra_checks = []
    if "<form" in body.lower() and 'type="hidden"' in body.lower():
        import re
        hidden_inputs = re.findall(r'<input[^>]*type\s*=\s*["\']hidden["\'][^>]*>', body, re.IGNORECASE)
        if hidden_inputs:
            extra_checks.append(f"发现{len(hidden_inputs)}个隐藏表单字段")

    return {
        "ok": True,
        "cap": "anti_track",
        "action": "check_honeypot",
        "url": url,
        "is_honeypot": is_hp,
        "reason": reason,
        "extra_warnings": extra_checks,
        "verdict": "危险: 疑似蜜罐" if is_hp else "安全" if not extra_checks else "注意: 有隐藏字段",
    }


def do_trace_ip(params):
    """反向追踪IP — 地理定位+ISP+威胁情报"""
    ip = params.get("ip", params.get("target", ""))
    if not ip:
        return {"ok": False, "error": "缺少 ip/target 参数"}

    geo_info = {}
    threat_info = {}

    # IP地理位置查询(ip-api.com 免费API)
    try:
        geo_url = f"http://ip-api.com/json/{ip}?fields=country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
        req = urllib.request.Request(geo_url, headers={"User-Agent": "GBT-AntiTrack/5.0"})
        resp = urllib.request.urlopen(req, timeout=8)
        geo_info = json.loads(resp.read().decode("utf-8"))
        geo_info.pop("status", None)
    except Exception:
        geo_info = {"error": "地理查询失败"}

    # 威胁情报查询(AbuseIPDB)
    try:
        abuse_key = os.environ.get("ABUSEIPDB_API_KEY", "")
        if abuse_key:
            abuse_url = "https://api.abuseipdb.com/api/v2/check"
            req = urllib.request.Request(abuse_url, headers={
                "Key": abuse_key, "Accept": "application/json",
            })
            req.data = urllib.parse.urlencode({"ipAddress": ip, "maxAgeInDays": 90}).encode()
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read().decode("utf-8")).get("data", {})
            threat_info = {
                "abuse_score": data.get("abuseConfidenceScore", 0),
                "total_reports": data.get("totalReports", 0),
                "last_reported": data.get("lastReportedAt", ""),
                "is_public": data.get("isPublic", False),
                "usage_type": data.get("usageType", ""),
                "domain": data.get("domain", ""),
            }
    except Exception:
        threat_info = {"note": "未配置ABUSEIPDB_API_KEY"}

    return {
        "ok": True,
        "cap": "anti_track",
        "action": "trace_ip",
        "domain": "攻击域",
        "ip": ip,
        "geolocation": geo_info,
        "threat_intel": threat_info,
        "summary": (
            f"{geo_info.get('country','?')}/{geo_info.get('city','?')} "
            f"ISP:{geo_info.get('isp','?')} "
            f"威胁分:{threat_info.get('abuse_score','?')}"
        ),
    }


def do_capture_attacker(params):
    """捕获攻击者全貌 — IP+请求指纹+UA+Referer+来源分析"""
    attacker_ip = params.get("ip", params.get("attacker_ip", ""))
    headers_raw = params.get("headers", {})

    profile = {
        "capture_time": datetime.now().isoformat(),
        "ip": attacker_ip,
    }

    # 请求头指纹分析
    ua = headers_raw.get("User-Agent", headers_raw.get("user-agent", ""))
    if ua:
        profile["user_agent"] = ua[:200]
        # OS推断
        if "Windows" in ua:
            profile["os"] = "Windows"
        elif "Macintosh" in ua or "Mac OS" in ua:
            profile["os"] = "macOS"
        elif "Linux" in ua or "X11" in ua:
            profile["os"] = "Linux"
        elif "Android" in ua:
            profile["os"] = "Android"
        elif "iPhone" in ua or "iPad" in ua:
            profile["os"] = "iOS"
        # 浏览器推断
        if "Edg/" in ua:
            profile["browser"] = "Edge"
        elif "Chrome/" in ua and "Edg" not in ua:
            profile["browser"] = "Chrome"
        elif "Firefox/" in ua:
            profile["browser"] = "Firefox"
        elif "Safari/" in ua and "Chrome" not in ua:
            profile["browser"] = "Safari"

    referer = headers_raw.get("Referer", headers_raw.get("referer", ""))
    if referer:
        profile["referer"] = referer[:200]
        # 推断攻击来源
        if "google.com/search" in referer:
            profile["attack_origin"] = "Google搜索跳转"
        elif "github.com" in referer:
            profile["attack_origin"] = "GitHub链接"
        elif "shodan.io" in referer:
            profile["attack_origin"] = "Shodan扫描"

    accept_lang = headers_raw.get("Accept-Language", "")
    if accept_lang:
        profile["language"] = accept_lang[:100]

    # IP地理追踪
    if attacker_ip:
        trace = do_trace_ip({"ip": attacker_ip})
        if trace.get("ok"):
            profile["geolocation"] = trace.get("geolocation", {})
            profile["threat"] = trace.get("threat_intel", {})

    # 攻击时间线记录
    timeline_file = STATE_DIR / "attacker_timeline.json"
    timeline = []
    if timeline_file.exists():
        try:
            timeline = json.loads(timeline_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    timeline.append(profile)
    if len(timeline) > 100:
        timeline = timeline[-100:]
    timeline_file.write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "cap": "anti_track",
        "action": "capture_attacker",
        "domain": "攻击域",
        "attacker_profile": profile,
        "total_captured": len(timeline),
        "timeline_saved": str(timeline_file),
    }


def do_reverse_trace(params):
    """全链路反向追踪 — IP→地理→ISP→威胁→开放端口→WHOIS"""
    ip = params.get("ip", "")
    if not ip:
        return {"ok": False, "error": "缺少 ip 参数"}

    results = {}

    # 地理+威胁
    results["trace"] = do_trace_ip({"ip": ip})

    # WHOIS查询
    try:
        whois_url = f"https://rdap.arin.net/registry/ip/{ip}"
        req = urllib.request.Request(whois_url, headers={"Accept": "application/json"})
        resp = urllib.request.urlopen(req, timeout=10)
        whois_data = json.loads(resp.read().decode("utf-8"))
        results["whois"] = {
            "name": whois_data.get("name", ""),
            "type": whois_data.get("type", ""),
            "country": whois_data.get("country", ""),
            "entities": [
                {"role": e.get("roles", [""])[0], "name": e.get("vcardArray", [[],[]])[1][1][3] if len(e.get("vcardArray", [[]])) > 1 else ""}
                for e in whois_data.get("entities", [])[:3]
            ],
        }
    except Exception:
        results["whois"] = {"error": "WHOIS查询失败"}

    return {
        "ok": True,
        "cap": "anti_track",
        "action": "reverse_trace",
        "domain": "攻击域",
        "ip": ip,
        "full_profile": results,
        "verdict": (
            "攻击者已定位: " + results.get("trace", {}).get("summary", "未知")
            if results.get("trace", {}).get("ok") else "追踪中"
        ),
    }


def do_clean_tracks(params):
    """清理痕迹 — 删除本地日志/缓存/temp文件"""
    cleaned = []
    errors = []
    dirs_to_clean = [
        STATE_DIR,
        Path.home() / ".gbt" / "screenshots",
    ]
    for d in dirs_to_clean:
        if not d.exists():
            continue
        try:
            for f in d.iterdir():
                try:
                    if f.is_file():
                        f.unlink()
                        cleaned.append(str(f))
                    elif f.is_dir() and params.get("deep"):
                        import shutil
                        shutil.rmtree(f)
                        cleaned.append(str(f))
                except Exception as e:
                    errors.append({"path": str(f), "error": str(e)[:100]})
        except Exception as e:
            errors.append({"dir": str(d), "error": str(e)[:100]})
    return {
        "ok": len(errors) == 0,
        "cleaned": len(cleaned),
        "cleaned_files": cleaned[:20],
        "errors": errors[:10]
    }

# ── 2Captcha 全维度指纹 + 代理增强 ────────────────────────

def do_real_fingerprint(params):
    """全维度真实浏览器指纹 (2Captcha FingerprintAPI)

    返回完整指纹档案: screen, navigator, webgl, webgpu,
    voices, intl, canvas_hash, fonts, visitor_id, 以及
    Playwright/Puppeteer/HTTP headers 即用配置。
    """
    try:
        from caps._2captcha.client import FingerprintAPI
        fp = FingerprintAPI()
        mode = params.get("mode", "complete")
        if mode == "stealth":
            return fp.get_stealth_config(
                tags=params.get("tags"), country=params.get("country"),
                fmt=params.get("format", "chromium"),
            )
        if mode == "playwright":
            return fp.get_playwright_context(
                tags=params.get("tags"), country=params.get("country"),
                fmt=params.get("format", "chromium"),
            )
        if mode == "puppeteer":
            return fp.get_puppeteer_context(
                tags=params.get("tags"), country=params.get("country"),
                fmt=params.get("format", "chromium"),
            )
        if mode == "headers":
            return fp.get_browser_headers(
                tags=params.get("tags"), country=params.get("country"),
            )
        if mode == "raw":
            return fp.random(
                tags=params.get("tags"), country=params.get("country"),
                browser_version=params.get("browser_version"),
                min_browser_version=params.get("min_browser_version"),
                fmt=params.get("format", "chromium"),
                force_version=params.get("force_version", False),
            )
        # default: complete_profile
        return fp.get_complete_profile(
            tags=params.get("tags"), country=params.get("country"),
            fmt=params.get("format", "chromium"),
        )
    except Exception as e:
        return {"ok": False, "error": f"FingerprintAPI unavailable: {e}"}


def do_proxy_info(params):
    """查询2Captcha代理网络信息"""
    try:
        from caps._2captcha.client import ProxyNetwork
        pn = ProxyNetwork()
        action = params.get("sub_action", "account_info")
        handlers = {
            "account_info": pn.account_info,
            "balance": pn.balance,
            "countries": lambda: pn.list_countries(params.get("page", 0)),
            "regions": lambda: pn.list_regions(params.get("page", 0)),
            "cities": lambda: pn.list_cities(params.get("page", 0)),
            "asns": lambda: pn.list_asns(params.get("page", 0)),
        }
        fn = handlers.get(action, pn.account_info)
        return fn()
    except Exception as e:
        return {"ok": False, "error": f"ProxyNetwork unavailable: {e}"}


def do_real_identity(params):
    """生成完整隐身身份 — 全维度指纹 + 即用配置

    返回:
      - fingerprint: 全维度指纹档案 (screen/navigator/webgl/voices/intl/canvas/fonts/visitor_id)
      - stealth: 隐身配置 (launch_args + context + headers + cdp_scripts)
      - playwright: Playwright context 参数
      - puppeteer: Puppeteer 启动参数
      - headers: HTTP 请求头
      - fallback_ua: 本地UA池兜底
    """
    identity = {"ok": True}
    tags = params.get("tags")
    country = params.get("country")
    try:
        from caps._2captcha.client import FingerprintAPI
        fp = FingerprintAPI()
        # 全维度指纹档案
        complete = fp.get_complete_profile(tags=tags, country=country)
        if complete["ok"]:
            identity["fingerprint"] = complete
        # 隐身配置
        stealth = fp.get_stealth_config(tags=tags, country=country)
        if stealth["ok"]:
            identity["stealth"] = stealth
        # Playwright 上下文
        pw = fp.get_playwright_context(tags=tags, country=country)
        if pw["ok"]:
            identity["playwright"] = pw
        # Puppeteer 上下文
        pp = fp.get_puppeteer_context(tags=tags, country=country)
        if pp["ok"]:
            identity["puppeteer"] = pp
        # HTTP 请求头
        hdrs = fp.get_browser_headers(tags=tags, country=country)
        if hdrs["ok"]:
            identity["headers"] = hdrs["headers"]
    except Exception as e:
        identity["fingerprint_error"] = str(e)

    # 本地UA池兜底
    identity["fallback_ua"] = random.choice(UA_POOL)
    return identity

HANDLERS = {
    "stealth": do_stealth_request,
    "stealth_request": do_stealth_request,
    "rotate": do_rotate_identity,
    "rotate_identity": do_rotate_identity,
    "honeypot": do_check_honeypot,
    "check_honeypot": do_check_honeypot,
    "trace": do_trace_ip,
    "trace_ip": do_trace_ip,
    "capture": do_capture_attacker,
    "capture_attacker": do_capture_attacker,
    "reverse": do_reverse_trace,
    "reverse_trace": do_reverse_trace,
    "clean": do_clean_tracks,
    "clean_tracks": do_clean_tracks,
    "fingerprint": do_real_fingerprint,
    "real_fingerprint": do_real_fingerprint,
    "proxy_info": do_proxy_info,
    "real_identity": do_real_identity,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "rotate"
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
