# 开发者：自由的风
"""darknet_scanner/run.py — 暗网监控扫描"""
import sys, json, os, urllib.request, urllib.error, re, hashlib

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ONION_SCAN_SITES = [
    "https://onion.live/?q={query}",
    "https://dark.fail",
]

def do_scan(params):
    query = params.get("query", params.get("keyword",""))
    category = params.get("category", "all")
    results = []
    for site in ONION_SCAN_SITES:
        try:
            url = site.format(query=urllib.parse.quote(query)) if "{query}" in site else site
            req = urllib.request.Request(url, headers={"User-Agent": "GBT-DarkScan/5.0"})
            resp = urllib.request.urlopen(req, timeout=15)
            body = resp.read().decode("utf-8", errors="replace")
            onions = re.findall(r'[a-z2-7]{16,56}\.onion', body)
            for o in onions[:20]:
                results.append({"onion": o, "source": site, "hash": hashlib.sha256(o.encode()).hexdigest()[:12]})
        except: pass
    return {"ok": True, "cap": "darknet_scanner", "domain": "信息域",
            "query": query, "onions_found": len(results), "results": results,
            "note": "仅索引公开的.onion地址,不访问暗网内容"}

HANDLERS = {"scan": do_scan}
if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv)>1 else "scan"
    p = json.loads(sys.argv[2]) if len(sys.argv)>2 else {}
    r = HANDLERS.get(a, lambda p:{"ok":False})(p)
    print(json.dumps(r, ensure_ascii=False, default=str))
