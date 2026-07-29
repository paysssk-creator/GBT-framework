# GBT cap: reverse_scrape — 反向抓取
import sys, json, os, urllib.request, urllib.error, re, time
from pathlib import Path

SANDBOX = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SANDBOX))

def do_reverse_trace(params):
    """从数据片段反向定位原始来源"""
    url = params.get("url", "")
    snippet = params.get("data_snippet", "")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GBT-ReverseScrape/1.0"})
        content = urllib.request.urlopen(req, timeout=15).read().decode(errors="replace")
        sources = []
        if snippet and snippet in content:
            sources.append({"source": url, "match": "exact", "position": content.index(snippet)})
        # 提取页面中所有外链作为潜在来源
        links = re.findall(r'https?://[^\s"\'<>]+', content)
        sources.append({"external_links": len(links), "sample": links[:5]})
        return {"ok": True, "sources": sources, "matched": len(sources) > 0}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def do_api_reverse(params):
    """从未公开接口反推API端点"""
    domain = params.get("domain", "")
    pattern = params.get("pattern", "api")
    common_paths = ["/api", "/v1", "/v2", "/graphql", "/rest", "/wp-json", "/_api", "/api/v1"]
    found = []
    for path in common_paths:
        try:
            url = f"https://{domain}{path}"
            req = urllib.request.Request(url, headers={"User-Agent": "GBT-ReverseScrape/1.0"})
            resp = urllib.request.urlopen(req, timeout=8)
            found.append({"path": path, "status": resp.status, "type": resp.headers.get("Content-Type", "")})
        except:
            pass
    return {"ok": True, "domain": domain, "endpoints_found": len(found), "endpoints": found}

def do_proxy_scrape(params):
    """通过反向代理采集"""
    url = params.get("url", "")
    depth = params.get("depth", 1)
    results = []
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        })
        content = urllib.request.urlopen(req, timeout=15).read().decode(errors="replace")
        results.append({"url": url, "size": len(content), "depth": 0})
        if depth > 1:
            links = re.findall(r'href="(https?://[^"]+)"', content)[:10]
            for link in links[:3]:
                try:
                    r2 = urllib.request.urlopen(urllib.request.Request(link, headers={"User-Agent": "GBT/1.0"}), timeout=10)
                    results.append({"url": link, "size": len(r2.read()), "depth": 1})
                except:
                    pass
        return {"ok": True, "pages": len(results), "results": results}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def do_fingerprint_reverse(params):
    """分析目标站反爬策略"""
    url = params.get("url", "")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GBT-ReverseScrape/1.0"})
        content = urllib.request.urlopen(req, timeout=10).read().decode(errors="replace")
        checks = {
            "cloudflare": "cloudflare" in content.lower() or "cf-" in content.lower(),
            "captcha": "captcha" in content.lower() or "recaptcha" in content.lower(),
            "js_challenge": "challenge" in content.lower() and "javascript" in content.lower(),
            "waf": "blocked" in content.lower() or "access denied" in content.lower(),
            "rate_limit": "429" in content or "too many requests" in content.lower(),
        }
        profile = {"url": url, "detections": checks, "recommend": []}
        if checks["cloudflare"]: profile["recommend"].append("use anti-cf fingerprint")
        if checks["captcha"]: profile["recommend"].append("use 2captcha solver")
        if checks["js_challenge"]: profile["recommend"].append("use headless browser")
        if checks["waf"]: profile["recommend"].append("use proxy rotation")
        return {"ok": True, "profile": profile}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def do_chain_trace(params):
    """追踪数据链路"""
    url = params.get("start_url", "")
    max_hops = params.get("max_hops", 5)
    chain = []
    current = url
    for hop in range(max_hops):
        try:
            req = urllib.request.Request(current, headers={"User-Agent": "GBT-ReverseScrape/1.0"})
            resp = urllib.request.urlopen(req, timeout=10)
            chain.append({"hop": hop, "url": current, "status": resp.status})
            redirect = resp.geturl()
            if redirect != current:
                current = redirect
            else:
                break
        except Exception as e:
            chain.append({"hop": hop, "url": current, "error": str(e)[:100]})
            break
    return {"ok": True, "hops": len(chain), "chain": chain}

HANDLERS = {
    "reverse_trace": do_reverse_trace,
    "api_reverse": do_api_reverse,
    "proxy_scrape": do_proxy_scrape,
    "fingerprint_reverse": do_fingerprint_reverse,
    "chain_trace": do_chain_trace,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "fingerprint_reverse"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    fn = HANDLERS.get(action, do_fingerprint_reverse)
    print(json.dumps(fn(params), ensure_ascii=False, default=str))
