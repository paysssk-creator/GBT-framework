# 开发者：自由的风
"""blockchain_analyzer/run.py — 区块链交易分析"""
import sys, json, os, urllib.request, urllib.error

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BLOCKCHAIN_APIS = {
    "bitcoin": "https://blockchain.info/rawaddr/{}",
    "ethereum": "https://api.etherscan.io/api?module=account&action=txlist&address={}&sort=desc",
    "balance_btc": "https://blockchain.info/q/addressbalance/{}",
    "balance_eth": "https://api.etherscan.io/api?module=account&action=balance&address={}&tag=latest",
}

def _api(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GBT-Blockchain/5.0"})
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)[:100]}

def do_trace(params):
    address = params.get("address", params.get("wallet", ""))
    chain = params.get("chain", "bitcoin")
    if not address: return {"ok": False, "error": "缺少address"}

    if chain == "bitcoin":
        data = _api(BLOCKCHAIN_APIS["bitcoin"].format(address))
        balance = _api(BLOCKCHAIN_APIS["balance_btc"].format(address))
        btc_balance = int(balance) / 1e8 if isinstance(balance, (int, str)) and str(balance).isdigit() else 0
        txs = data.get("txs", [])[:10] if isinstance(data, dict) else []
        return {
            "ok": True, "cap": "blockchain_analyzer", "domain": "信息域",
            "chain": "Bitcoin", "address": address,
            "balance_btc": btc_balance, "balance_usd": round(btc_balance * 67000, 2),
            "total_tx": data.get("n_tx", 0) if isinstance(data, dict) else 0,
            "recent_tx": [{"hash": t.get("hash","")[:16], "time": t.get("time"),
                          "value_btc": sum(o.get("value",0) for o in t.get("out",[]) if o.get("addr")==address)/1e8}
                         for t in txs[:5]],
        }

    elif chain == "ethereum":
        etherscan_key = os.environ.get("ETHERSCAN_API_KEY", "")
        url = BLOCKCHAIN_APIS["ethereum"].format(address)
        if etherscan_key: url += "&apikey=" + etherscan_key
        data = _api(url)
        bal_url = BLOCKCHAIN_APIS["balance_eth"].format(address)
        if etherscan_key: bal_url += "&apikey=" + etherscan_key
        balance_data = _api(bal_url)
        eth_balance = int(balance_data.get("result", "0")) / 1e18 if isinstance(balance_data, dict) else 0
        txs = data.get("result", [])[:10] if isinstance(data, dict) else []
        return {
            "ok": True, "chain": "Ethereum", "address": address,
            "balance_eth": round(eth_balance, 4), "balance_usd": round(eth_balance * 3500, 2),
            "total_tx": len(txs), "recent_tx": txs[:5],
        }

    return {"ok": False, "error": "不支持的链: {}".format(chain), "supported": list(BLOCKCHAIN_APIS.keys())}

HANDLERS = {"trace": do_trace}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "trace"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    r = HANDLERS.get(action, lambda p: {"ok": False})(params)
    print(json.dumps(r, ensure_ascii=False, default=str))
