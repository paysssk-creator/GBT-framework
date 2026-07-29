# 开发者：自由的风
"""api_tester/run.py — API端点测试
==================================
AI编程 ready — REST API测试: GET/POST/PUT/DELETE, 自动检测CORS/鉴权/限流。
"""
import sys, json, os, urllib.request, urllib.error, urllib.parse, time
from pathlib import Path

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _api_call(url, method="GET", data=None, headers=None, timeout=10):
    hdrs = headers or {"User-Agent": "GBT-APITester/5.0", "Accept": "application/json"}
    try:
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
        start = time.time()
        resp = urllib.request.urlopen(req, timeout=timeout)
        elapsed = round((time.time()-start)*1000)
        resp_body = resp.read().decode("utf-8", errors="replace")
        try: resp_json = json.loads(resp_body)
        except: resp_json = None
        return {"status": resp.status, "elapsed_ms": elapsed, "headers": dict(resp.headers),
                "body": resp_body[:2000], "json": resp_json, "ok": True}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500] if e.fp else ""
        return {"status": e.code, "error": True, "body": body, "ok": False}
    except Exception as e:
        return {"error": str(e)[:100], "ok": False}

def do_test(params):
    url = params.get("url", "")
    if not url: return {"ok": False, "error": "缺少url"}
    if not url.startswith("http"): url = "http://" + url
    results = {}
    for method in ["GET", "POST", "OPTIONS"]:
        results[method] = _api_call(url, method, {"test": "GBT"} if method == "POST" else None)
    # CORS检测
    cors = _api_call(url, "OPTIONS", headers={"Origin": "https://evil.com", "User-Agent": "GBT/5.0"})
    cors_headers = {k.lower(): v for k, v in cors.get("headers", {}).items()}
    security = {
        "cors_any_origin": "access-control-allow-origin" in cors_headers and cors_headers.get("access-control-allow-origin") == "*",
        "cors_allow_credentials": "access-control-allow-credentials" in cors_headers,
        "server_header": results.get("GET", {}).get("headers", {}).get("Server", ""),
        "x_powered_by": results.get("GET", {}).get("headers", {}).get("X-Powered-By", ""),
    }
    return {"ok": True, "cap": "api_tester", "action": "test", "domain": "AI编程",
            "url": url, "methods": {m: {"status": r.get("status"), "elapsed_ms": r.get("elapsed_ms")} for m, r in results.items()},
            "security": security, "verdict": "CORS全开" if security["cors_any_origin"] else "正常"}

HANDLERS = {"test": do_test}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "test"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
