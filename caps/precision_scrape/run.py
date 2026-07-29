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
# ─────────────────────────────────────────────────────────────────────────

"""精准抓取 — 网页数据提取"""
import sys, json
try:
    import requests
except ImportError:
    import subprocess; subprocess.run([sys.executable,'-m','pip','install','requests','-q'],capture_output=True)
    import requests

def do_scrape(params):
    url = params.get('url', '')
    if not url: return {"ok": False, "error": "缺少url参数"}
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent':'GBT/1.0'})
        return {"ok": True, "url": url, "status": r.status_code, "size": len(r.text), "content": r.text[:5000]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

handlers = {'scrape': do_scrape}
if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv)>1 else 'scrape'
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = handlers.get(action, lambda p: {"ok":False,"error":f"未知:{action}"})
    print(json.dumps(h(params), ensure_ascii=False))
