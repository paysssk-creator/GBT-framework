# 开发者：自由的风
"""telegram/run.py — Telegram Bot接口
=====================================
信息域 ready — 发送/读取/监听Telegram消息
"""
import sys, json, os, urllib.request, urllib.error, urllib.parse

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
API = f"https://api.telegram.org/bot{TOKEN}"

def _api(method, data=None, timeout=15):
    if not TOKEN:
        return {"ok": False, "error": "TELEGRAM_BOT_TOKEN未设置"}
    try:
        url = f"{API}/{method}"
        req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode() if data else None,
                                     headers={"User-Agent": "GBT-Telegram/5.0"})
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}

def do_send(params):
    chat_id = params.get("chat_id", params.get("chat", ""))
    text = params.get("text", params.get("message", ""))
    if not chat_id or not text:
        return {"ok": False, "error": "缺少chat_id或text"}
    result = _api("sendMessage", {"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
    return {"ok": result.get("ok", False), "cap": "telegram", "action": "send",
            "domain": "信息域", "message_id": result.get("result", {}).get("message_id")}

def do_read(params):
    offset = params.get("offset", -1)
    result = _api("getUpdates", {"offset": offset, "limit": 10, "timeout": 5})
    messages = []
    if result.get("ok") and result.get("result"):
        for upd in result["result"]:
            msg = upd.get("message", {})
            messages.append({
                "from": msg.get("from", {}).get("username", msg.get("from", {}).get("first_name", "")),
                "chat_id": msg.get("chat", {}).get("id"),
                "text": (msg.get("text", msg.get("caption", "")) or "")[:200],
                "date": msg.get("date"),
                "update_id": upd.get("update_id"),
            })
    return {"ok": True, "cap": "telegram", "action": "read", "messages": messages, "count": len(messages)}

def do_listen(params):
    """监听频道消息(Webhook模式检测)"""
    result = _api("getWebhookInfo")
    webhook = result.get("result", {}) if result.get("ok") else {}
    return {"ok": True, "cap": "telegram", "action": "listen",
            "webhook_url": webhook.get("url", ""),
            "pending_updates": webhook.get("pending_update_count", 0),
            "note": "使用read轮询或设置webhook接收消息推送"}

HANDLERS = {"send": do_send, "read": do_read, "listen": do_listen}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "listen"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
