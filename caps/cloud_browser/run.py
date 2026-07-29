# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""cloud_browser/run.py — 2Captcha云端CDP浏览器能力模块"""
import sys
import json

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent.parent))
from caps._2captcha.client import CloudBrowser

browser = CloudBrowser()
_session_pool = {}  # name -> session_info

HANDLERS = {
    "create_session": lambda p: browser.create_session(
        name=p.get("name", "GBT Session"),
        country=p.get("country", "us"),
        proxy_mode=p.get("proxy_mode", "none"),
        custom_proxy=p.get("custom_proxy"),
        captcha_mode=p.get("captcha_mode", "auto"),
        device_type=p.get("device_type", "windows"),
    ),
    "get_connection": lambda p: browser.get_connection(
        account_id=p["account_id"],
        profile_id=p.get("profile_id"),
        custom_proxy=p.get("custom_proxy"),
        device_type=p.get("device_type"),
        captcha_mode=p.get("captcha_mode"),
    ),
    "account_status": lambda p: browser.account_status(),
    "list_accounts": lambda p: browser.list_accounts(),
    "create_account": lambda p: browser.create_account(
        name=p.get("name", "GBT Account"),
        proxy_mode=p.get("proxy_mode", "none"),
        country=p.get("country", "us"),
        custom_proxy=p.get("custom_proxy"),
        proxy_account_id=p.get("proxy_account_id"),
    ),
    "delete_account": lambda p: browser.delete_account(p["account_id"]),
    "list_profiles": lambda p: browser.list_profiles(p.get("account_id")),
    "create_profile": lambda p: browser.create_profile(
        account_id=p["account_id"],
        name=p.get("name", ""),
        proxy_mode=p.get("proxy_mode", "inherit"),
        country=p.get("country"),
        custom_proxy=p.get("custom_proxy"),
    ),
    "get_statistics": lambda p: browser.get_statistics(),
}


def do_action(params):
    action = params.get("action", params.get("_action", "create_session"))
    handler = HANDLERS.get(action)
    if handler is None:
        return {"ok": False, "error": f"unknown action: {action}"}
    return handler(params)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        raw = sys.stdin.read()
        params = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, EOFError):
        params = {}
    result = do_action(params)
    print(json.dumps(result, ensure_ascii=False, default=str))
