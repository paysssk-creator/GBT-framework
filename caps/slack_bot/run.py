# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""slack_bot/run.py — Slack+Discord集成机器人
===============================================
Slack Web API · Discord Webhook · 消息收发 · 频道管理
"""
import sys, json, os, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime

SANDBOX = Path(__file__).parent.parent

def _slack_api(method, data=None, token=None):
    """调用Slack Web API"""
    token = token or os.environ.get("SLACK_BOT_TOKEN", "")
    if not token:
        return None, "SLACK_BOT_TOKEN未设置"
    url = f"https://slack.com/api/{method}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}
    body = json.dumps(data).encode() if data else None
    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST" if data else "GET")
        resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
        return resp, None
    except Exception as e:
        return None, str(e)[:200]

def _discord_webhook(webhook_url, content, username="GBT小土豆"):
    """发送Discord Webhook消息"""
    try:
        data = json.dumps({"content": content, "username": username}).encode()
        req = urllib.request.Request(webhook_url, data=data,
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        return True, None
    except Exception as e:
        return False, str(e)[:200]

def do_send_slack(params):
    """发送Slack消息"""
    channel = params.get("channel", "")
    text = params.get("text", params.get("message", ""))
    if not channel or not text:
        return {"ok": False, "error": "缺少channel/text参数"}
    
    resp, err = _slack_api("chat.postMessage", {"channel": channel, "text": text})
    if err:
        return {"ok": False, "error": err}
    return {"ok": resp.get("ok", False), "cap": "slack_bot", "action": "send_slack",
            "channel": channel, "ts": resp.get("ts", ""), "platform": "slack"}

def do_send_discord(params):
    """发送Discord消息 (Webhook)"""
    webhook = params.get("webhook", os.environ.get("DISCORD_WEBHOOK", ""))
    text = params.get("text", params.get("message", ""))
    username = params.get("username", "GBT小土豆")
    
    if not webhook or not text:
        return {"ok": False, "error": "缺少webhook/text参数"}
    
    ok, err = _discord_webhook(webhook, text, username)
    return {"ok": ok, "cap": "slack_bot", "action": "send_discord", "platform": "discord"}

def do_list_channels(params):
    """列出Slack频道"""
    resp, err = _slack_api("conversations.list", {"types": "public_channel,private_channel"})
    if err:
        return {"ok": False, "error": err}
    
    channels = []
    for ch in resp.get("channels", []):
        channels.append({"id": ch["id"], "name": ch["name"], "is_private": ch.get("is_private", False),
                         "members": ch.get("num_members", 0)})
    return {"ok": True, "cap": "slack_bot", "action": "list_channels",
            "platform": "slack", "count": len(channels), "channels": channels}

def do_list_users(params):
    """列出Slack用户"""
    resp, err = _slack_api("users.list")
    if err:
        return {"ok": False, "error": err}
    
    users = []
    for u in resp.get("members", []):
        if not u.get("deleted") and not u.get("is_bot"):
            users.append({"id": u["id"], "name": u.get("real_name", u.get("name", "")),
                         "email": u.get("profile", {}).get("email", "")})
    return {"ok": True, "cap": "slack_bot", "action": "list_users",
            "platform": "slack", "count": len(users), "users": users[:50]}

def do_read_slack(params):
    """读取Slack频道最近消息"""
    channel = params.get("channel", "")
    limit = params.get("limit", 10)
    if not channel:
        return {"ok": False, "error": "缺少channel参数"}
    
    resp, err = _slack_api("conversations.history", {"channel": channel, "limit": limit})
    if err:
        return {"ok": False, "error": err}
    
    messages = []
    for msg in resp.get("messages", []):
        messages.append({
            "user": msg.get("user", ""),
            "text": msg.get("text", "")[:500],
            "ts": msg.get("ts", ""),
            "has_files": bool(msg.get("files")),
        })
    return {"ok": True, "cap": "slack_bot", "action": "read_slack",
            "platform": "slack", "channel": channel, "count": len(messages), "messages": messages}

def do_broadcast(params):
    """向所有平台广播消息"""
    text = params.get("text", "")
    if not text:
        return {"ok": False, "error": "缺少text参数"}
    
    results = {}
    if params.get("slack_channel"):
        results["slack"] = do_send_slack({"channel": params["slack_channel"], "text": text})
    if params.get("discord_webhook") or os.environ.get("DISCORD_WEBHOOK"):
        results["discord"] = do_send_discord({"webhook": params.get("discord_webhook", ""), "text": text})
    
    return {"ok": True, "cap": "slack_bot", "action": "broadcast",
            "platforms": list(results.keys()), "results": results}

HANDLERS = {
    "send_slack": do_send_slack, "send_discord": do_send_discord,
    "list_channels": do_list_channels, "list_users": do_list_users,
    "read_slack": do_read_slack, "broadcast": do_broadcast, "run": do_send_slack,
}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "list_channels"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知:{action}"})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
