# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""proxy_network/run.py — 2Captcha住宅代理网络能力模块"""
import sys
import json

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent.parent))
from caps._2captcha.client import ProxyNetwork

proxy = ProxyNetwork()

HANDLERS = {
    "account_info": lambda p: proxy.account_info(),
    "balance": lambda p: proxy.balance(),
    "list_countries": lambda p: proxy.list_countries(p.get("page", 0)),
    "list_regions": lambda p: proxy.list_regions(p.get("page", 0)),
    "list_cities": lambda p: proxy.list_cities(p.get("page", 0)),
    "list_asns": lambda p: proxy.list_asns(p.get("page", 0)),
    "generate_whitelist": lambda p: proxy.generate_whitelist(),
}


def do_action(params):
    action = params.get("action", params.get("_action", "account_info"))
    handler = HANDLERS.get(action)
    if handler is None:
        return {"ok": False, "error": f"unknown action: {action}"}
    return handler(params)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    elif not sys.stdin.isatty():
        try:
            raw = sys.stdin.read()
            params = json.loads(raw) if raw.strip() else {}
        except (json.JSONDecodeError, EOFError):
            params = {}
    result = do_action(params)
    print(json.dumps(result, ensure_ascii=False, default=str))
