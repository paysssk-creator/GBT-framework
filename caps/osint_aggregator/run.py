# 开发者：自由的风
"""osint_aggregator/run.py — OSINT开源情报聚合"""
import sys, json, urllib.request, urllib.error, ssl, socket, concurrent.futures
from datetime import datetime

def _whois(domain):
    try:
        url = "https://rdap.verisign.com/domain/v1/" + domain
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode("utf-8"))
        return {"registrar": data.get("ldhName", ""), "status": data.get("status", [])}
    except: return {"error": "WHOIS失败"}

def _dns(domain):
    records = {}
    for rtype in ["A", "AAAA", "MX", "NS", "TXT"]:
        try:
            answers = socket.getaddrinfo(domain, None)
            records[rtype] = [a[4][0] for a in answers[:5]]
        except: pass
    return records

def _ssl_cert(domain):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
        sock = socket.create_connection((domain, 443), timeout=8)
        with ctx.wrap_socket(sock, server_hostname=domain) as ss:
            cert = ss.getpeercert()
            return {"issuer": dict(x[0] for x in cert.get("issuer", [])),
                    "not_before": cert.get("notBefore"), "not_after": cert.get("notAfter"),
                    "san": [x[1] for x in cert.get("subjectAltName", []) if x[0] == "DNS"][:10]}
    except: return {"error": "SSL连接失败"}

def do_aggregate(params):
    target = params.get("target", params.get("domain", ""))
    if not target: return {"ok": False, "error": "缺少target"}
    target = target.replace("http://", "").replace("https://", "").rstrip("/")
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        f1, f2, f3 = ex.submit(_whois, target), ex.submit(_dns, target), ex.submit(_ssl_cert, target)
        results["whois"] = f1.result(); results["dns"] = f2.result(); results["ssl"] = f3.result()
    return {"ok": True, "cap": "osint_aggregator", "domain": "信息域",
            "target": target, "timestamp": datetime.now().isoformat(), "results": results}

HANDLERS = {"aggregate": do_aggregate}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "aggregate"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    r = HANDLERS.get(action, lambda p: {"ok": False})(params)
    print(json.dumps(r, ensure_ascii=False, default=str))
