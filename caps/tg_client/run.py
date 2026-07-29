# 开发者：自由的风
"""tg_client/run.py — Telethon真人TG账号(无Bot限制)
==================================================
信息域 core — 使用Telethon客户端，真人账号无Bot API限制。
可自由加群/DM/搜索/下载媒体。
"""
import sys, json, os
from pathlib import Path

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_DIR = Path.home() / ".gbt" / "telegram"
SESSION_DIR.mkdir(parents=True, exist_ok=True)

API_ID = int(os.environ.get("TELEGRAM_API_ID", "0"))
API_HASH = os.environ.get("TELEGRAM_API_HASH", "")
PHONE = os.environ.get("TELEGRAM_PHONE", "")

def _get_client():
    try:
        from telethon import TelegramClient
        from telethon.sessions import StringSession
    except ImportError:
        return None, "telethon未安装(pip install telethon)"
    if not API_ID or not API_HASH:
        return None, "TELEGRAM_API_ID/API_HASH未设置"
    session_file = SESSION_DIR / "gbt_session.session"
    return TelegramClient(str(session_file), API_ID, API_HASH), None

def do_login(params):
    client, err = _get_client()
    if err:
        return {"ok": False, "error": err}
    import asyncio
    async def _login():
        await client.start(phone=PHONE or params.get("phone", ""))
        me = await client.get_me()
        return {"ok": True, "cap": "tg_client", "action": "login",
                "domain": "信息域", "user": me.username or me.first_name,
                "user_id": me.id, "phone": me.phone}
    try:
        return asyncio.run(_login())
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def do_send(params):
    client, err = _get_client()
    if err:
        return {"ok": False, "error": err}
    target = params.get("to", params.get("target", ""))
    text = params.get("text", params.get("message", ""))
    if not target or not text:
        return {"ok": False, "error": "缺少to和text"}
    import asyncio
    async def _send():
        await client.start()
        await client.send_message(target, text)
        return {"ok": True, "cap": "tg_client", "action": "send", "to": target}
    try:
        return asyncio.run(_send())
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def do_search(params):
    client, err = _get_client()
    if err:
        return {"ok": False, "error": err}
    query = params.get("query", params.get("q", ""))
    if not query:
        return {"ok": False, "error": "缺少query"}
    import asyncio
    async def _search():
        await client.start()
        results = []
        async for dialog in client.iter_dialogs(limit=20):
            if query.lower() in (dialog.name or "").lower():
                results.append({"name": dialog.name, "id": dialog.id,
                               "type": str(dialog.entity.__class__.__name__)})
        return {"ok": True, "cap": "tg_client", "action": "search",
                "query": query, "results": results, "found": len(results)}
    try:
        return asyncio.run(_search())
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def do_join(params):
    client, err = _get_client()
    if err:
        return {"ok": False, "error": err}
    group = params.get("group", params.get("channel", ""))
    if not group:
        return {"ok": False, "error": "缺少group/channel"}
    import asyncio
    async def _join():
        await client.start()
        await client(ImportChatInviteRequest(group)) if group.startswith("+") else None
        entity = await client.get_entity(group)
        return {"ok": True, "cap": "tg_client", "action": "join", "group": group,
                "name": getattr(entity, 'title', str(entity.id))}
    try:
        return asyncio.run(_join())
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

HANDLERS = {"login": do_login, "send": do_send, "search": do_search, "join": do_join}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "search"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
