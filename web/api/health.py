# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""Platform health API — Cloudflare Workers endpoint"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def get_health() -> dict:
    result = {"status": "healthy", "timestamp": time.time(), "checks": {}}

    # Payment channels
    wallets = {
        "ETH": ("0xA6C72Dbc9ceD413c98Ab8Ed7ea533cD42A8D7C17", "eth"),
        "TRX": ("TTML7MEQZh8iwqXZcrnrcRXF4ZL62Ln2B2", "trx"),
        "BTC": ("bc1pplv78l3h5yz2grf259y0gvhh5q5475yyjdtnazlqxadlc8zdp3rqage8y7", "btc"),
    }
    payments = {}
    for chain, (addr, coin) in wallets.items():
        try:
            params = urllib.parse.urlencode({"address": addr, "pending": "1"})
            url = f"https://api.cryptapi.io/{coin}/info/?{params}"
            req = urllib.request.Request(url, headers={"User-Agent": "GBT/1.0"})
            urllib.request.urlopen(req, timeout=5)
            payments[chain] = "online"
        except Exception:
            payments[chain] = "offline"
    payments["BSC"] = "direct"
    result["checks"]["payments"] = {
        "ok": all(v in ("online", "direct") for v in payments.values()),
        "channels": payments,
    }

    # Neighborhood
    try:
        from brain.nexus import get_nexus
        n = get_nexus()
        s = n.scan(force=True)
        result["checks"]["neighborhood"] = {
            "ok": s.get("ok", False),
            "health": s.get("health_pct", 0),
            "caps": f'{s.get("found", 0)}/{s.get("total_caps", 0)}',
        }
    except Exception:
        result["checks"]["neighborhood"] = {"ok": False}

    # Tentacle
    try:
        from brain.neural_tentacle import get_tentacle
        t = get_tentacle()
        result["checks"]["tentacle"] = {
            "ok": True,
            "scans": t._scan_count,
            "healed": t._issues_fixed_total,
        }
    except Exception:
        result["checks"]["tentacle"] = {"ok": False}

    # Overall
    all_ok = all(c.get("ok", False) for c in result["checks"].values())
    result["status"] = "healthy" if all_ok else "degraded"
    return result


if __name__ == "__main__":
    # Cloudflare Workers / HTTP response
    import os
    data = json.dumps(get_health(), ensure_ascii=False, indent=2)
    if os.environ.get("CF_WORKER") or os.environ.get("HTTP_RESPONSE"):
        print("Content-Type: application/json; charset=utf-8")
        print()
    print(data)
