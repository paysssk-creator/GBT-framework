# 开发者：自由的风
"""location_tracker/run.py — 地理位置追踪"""
import sys, json, os, urllib.request, urllib.error
SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def do_locate(params):
    ip = params.get("ip", "")
    if not ip: return {"ok": False, "error": "缺少ip"}
    try:
        url = "http://ip-api.com/json/{}?fields=country,regionName,city,lat,lon,isp,org,as,timezone,query".format(ip)
        req = urllib.request.Request(url, headers={"User-Agent": "GBT-Locator/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=8).read())
        return {"ok": True, "cap": "location_tracker", "domain": "侦察域",
                "ip": ip, "location": {"country": data.get("country"), "city": data.get("city"),
                "region": data.get("regionName"), "lat": data.get("lat"), "lon": data.get("lon"),
                "isp": data.get("isp"), "org": data.get("org"), "timezone": data.get("timezone")}}
    except Exception as e: return {"ok": False, "error": str(e)[:100]}

HANDLERS = {"locate": do_locate}
if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv)>1 else "locate"
    p = json.loads(sys.argv[2]) if len(sys.argv)>2 else {}
    r = HANDLERS.get(a, lambda p:{"ok":False})(p)
    print(json.dumps(r, ensure_ascii=False, default=str))
