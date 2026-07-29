# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除

# ── shared_browser 穿透接入（GBT全域浏览器共享）──────────────────────────
import sys as _sys
_sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent.parent))
try:
    import shared_browser as _SB
    _SB_OK = True
except Exception:
    _SB_OK = False

def _fetch_html(url, wait_ms=1000, selector=""):
    """优先用真实浏览器（继承Cookie），降级到 urllib"""
    if _SB_OK:
        r = _SB.get_html(url, wait_ms=wait_ms, selector=selector)
        if r.get("ok"):
            return r.get("html",""), r.get("mode","browser")
    # urllib 兜底
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"
        })
        with urllib.request.urlopen(req, timeout=12) as resp:
            return resp.read().decode("utf-8","replace"), "urllib"
    except Exception as e:
        return "", f"error:{e}"

# ── 2Captcha 验证码自动求解 (deep_scrape 增强) ──────────────────────────
try:
    from caps._2captcha.client import CaptchaSolver
    _SOLVER = CaptchaSolver()
    _SOLVER_OK = True
except Exception:
    _SOLVER_OK = False

def _detect_captcha(html, url):
    """检测页面是否包含验证码，返回 (captcha_type, details)"""
    if not html:
        return None, {}
    hl = html.lower()
    # reCAPTCHA
    if "g-recaptcha" in hl or "recaptcha/api2" in hl or "google.com/recaptcha" in hl:
        import re as _re
        m = _re.search(r'data-sitekey=["\x27]([^"\x27]+)', html)
        if m:
            return "recaptcha_v2", {"website_key": m.group(1), "website_url": url}
        m = _re.search(r'[?&]k=([^&\x27"\s]+)', html)
        if m:
            return "recaptcha_v2", {"website_key": m.group(1), "website_url": url}
    # Cloudflare Turnstile
    if "turnstile" in hl or "challenges.cloudflare.com" in hl:
        import re as _re
        m = _re.search(r'data-sitekey=["\x27]([^"\x27]+)', html)
        if m:
            return "turnstile", {"website_key": m.group(1), "website_url": url}
    # hCaptcha
    if "h-captcha" in hl or "hcaptcha.com" in hl:
        import re as _re
        m = _re.search(r'data-sitekey=["\x27]([^"\x27]+)', html)
        if m:
            return "hcaptcha", {"website_key": m.group(1), "website_url": url}
    return None, {}

def _solve_captcha_if_needed(html, url):
    """如果检测到验证码，尝试自动求解"""
    if not _SOLVER_OK:
        return html, None
    ctype, details = _detect_captcha(html, url)
    if not ctype:
        return html, None
    solve_map = {
        "recaptcha_v2": _SOLVER.solve_recaptcha_v2,
        "turnstile": _SOLVER.solve_turnstile,
        "hcaptcha": _SOLVER.solve_hcaptcha,
    }
    solver_fn = solve_map.get(ctype)
    if not solver_fn:
        return html, None
    result = solver_fn(**details)
    if result.get("ok"):
        return html, {"type": ctype, "solved": True, "solution": result.get("solution", {})}
    return html, {"type": ctype, "solved": False, "error": result.get("error", "")}
# ─────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────

"""deep_scrape/run.py — 深度自适应爬虫"""
import sys, json, os, re, urllib.request, urllib.parse, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def _fetch(url, timeout=30):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ct = r.headers.get("Content-Type", "")
            raw = r.read()
            if "json" in ct:
                return {"ok": True, "type": "json", "data": json.loads(raw)}
            html = raw.decode("utf-8", errors="replace")
            return {"ok": True, "type": "html", "html": html, "size": len(html)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _extract_links(html, base_url):
    links = set()
    for m in re.finditer(r'href=["\']([^"\']+)["\']', html, re.I):
        href = m.group(1)
        if href.startswith("http"): links.add(href)
        elif href.startswith("/"): links.add(urllib.parse.urljoin(base_url, href))
    return list(links)[:50]

def _extract_text(html):
    # 去掉script/style
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.I|re.S)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.I|re.S)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()[:5000]

def do_scrape(params):
    url = params.get("url", "")
    solve_captcha = params.get("solve_captcha", True)
    if not url: return {"ok": False, "error": "缺少 url"}
    r = _fetch(url)
    if not r["ok"]: return r
    if r["type"] == "json":
        return {"ok": True, "url": url, "type": "json", "data": r["data"]}
    html = r["html"]
    # captcha detection + auto-solve
    captcha_info = None
    if solve_captcha:
        html, captcha_info = _solve_captcha_if_needed(html, url)
    links = _extract_links(html, url)
    title = ""
    tm = re.search(r'<title[^>]*>(.*?)</title>', html, re.I)
    if tm: title = tm.group(1)
    result = {"ok": True, "url": url, "title": title, "size": r["size"],
            "links_count": len(links), "links": links[:20],
            "text_preview": _extract_text(html)[:1000]}
    if captcha_info:
        result["captcha"] = captcha_info
    return result

def do_crawl(params):
    url = params.get("url", "")
    max_pages = params.get("max_pages", 10)
    pattern = params.get("pattern", "")  # URL模式匹配
    if not url: return {"ok": False, "error": "缺少 url"}
    visited = set()
    results = []
    queue = [url]
    
    while queue and len(visited) < max_pages:
        u = queue.pop(0)
        if u in visited: continue
        visited.add(u)
        r = _fetch(u, 15)
        if not r["ok"] or r["type"] != "html": continue
        html = r["html"]
        results.append({"url": u, "size": r["size"], "title": re.search(r'<title[^>]*>(.*?)</title>', html, re.I).group(1) if re.search(r'<title[^>]*>(.*?)</title>', html, re.I) else ""})
        for link in _extract_links(html, u):
            if link not in visited and (not pattern or pattern in link):
                queue.append(link)
    return {"ok": True, "pages": len(results), "results": results}

def do_extract(params):
    url = params.get("url", "")
    html = params.get("html", "")
    selectors = params.get("selectors", {})
    if url and not html:
        r = _fetch(url)
        if r["ok"] and r["type"] == "html": html = r["html"]
    if not html: return {"ok": False, "error": "缺少 url 或 html"}
    
    extracted = {}
    for name, sel in selectors.items():
        # CSS selector 简化实现
        if sel.startswith("."):
            cls = sel[1:]
            matches = re.findall(rf'class=["\'][^"\']*\b{cls}\b[^"\']*["\'](?:\s*>)?(.*?)(?:</|$)', html, re.I|re.S)
            extracted[name] = [m.strip()[:200] for m in matches[:5]]
        elif sel.startswith("#"):
            id_val = sel[1:]
            m = re.search(rf'id=["\']{id_val}["\'](?:\s*>)?(.*?)(?:</|$)', html, re.I|re.S)
            extracted[name] = m.group(1).strip()[:500] if m else ""
        else:
            # 标签选择器
            tag = sel
            matches = re.findall(rf'<{tag}[^>]*>(.*?)</{tag}>', html, re.I|re.S)
            extracted[name] = [m.strip()[:200] for m in matches[:5]]
    # 自动检测结构化数据
    extracted["_auto_title"] = re.search(r'<title[^>]*>(.*?)</title>', html, re.I).group(1) if re.search(r'<title[^>]*>(.*?)</title>', html, re.I) else ""
    extracted["_auto_links"] = len(_extract_links(html, url or ""))
    return {"ok": True, "extracted": extracted}

def do_sitemap(params):
    url = params.get("url", "")
    if not url: return {"ok": False, "error": "缺少 url"}
    base = url.rstrip("/")
    endpoints = []
    # 尝试 robots.txt
    try:
        r = _fetch(f"{base}/robots.txt", 10)
        if r["ok"] and r["type"] == "html":
            for m in re.finditer(r'(?:Allow|Disallow):\s*(/\S*)', r["html"]):
                endpoints.append({"path": m.group(1), "source": "robots.txt"})
    except: pass
    # 尝试常见API端点
    common = ["/api", "/api/v1", "/graphql", "/health", "/status", "/metrics", "/docs", "/swagger"]
    for path in common:
        try:
            r = _fetch(f"{base}{path}", 5)
            if r["ok"]: endpoints.append({"path": path, "status": "reachable"})
        except: pass
    return {"ok": True, "base": base, "endpoints": endpoints, "count": len(endpoints)}

HANDLERS = {"scrape": do_scrape, "crawl": do_crawl, "extract": do_extract, "sitemap": do_sitemap}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 else "scrape"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知动作: {action}", "available": list(HANDLERS.keys())})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
