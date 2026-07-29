# TG Bridge - 后台轮询+转发
import urllib.request, urllib.parse, json, time, os, sys
from pathlib import Path

TOKEN = os.environ.get("GBT_TG_TOKEN", "")
CHAT_ID = os.environ.get("GBT_TG_CHAT_ID", "")

if not TOKEN or not CHAT_ID:
    print("错误: GBT_TG_TOKEN 和 GBT_TG_CHAT_ID 环境变量必须设置", file=sys.stderr)
    sys.exit(1)
API = f'https://api.telegram.org/bot{TOKEN}'
INBOX = Path.home() / '.gbt' / 'tg_inbox.json'
OUTBOX = Path.home() / '.gbt' / 'tg_outbox.json'
LAST_ID_FILE = Path.home() / '.gbt' / 'tg_last_update_id'

def api(method, data=None):
    try:
        url = f'{API}/{method}'
        req = urllib.request.Request(url, 
            data=urllib.parse.urlencode(data).encode() if data else None,
            headers={'User-Agent': 'GBT-TG/5.0'})
        return json.loads(urllib.request.urlopen(req, timeout=15).read())
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def send(text):
    return api('sendMessage', {'chat_id': CHAT_ID, 'text': text})

def check_incoming():
    """检查新消息"""
    last_id = 0
    if LAST_ID_FILE.exists():
        last_id = int(LAST_ID_FILE.read_text().strip())
    
    result = api('getUpdates', {'offset': last_id + 1, 'limit': 5, 'timeout': 5})
    messages = []
    if result.get('ok') and result.get('result'):
        for upd in result['result']:
            msg = upd.get('message', {})
            text = msg.get('text', '')
            if text:
                messages.append({'text': text, 'date': msg.get('date'), 'update_id': upd['update_id']})
            last_id = max(last_id, upd['update_id'])
        LAST_ID_FILE.write_text(str(last_id))
        if messages:
            INBOX.write_text(json.dumps(messages, ensure_ascii=False, indent=2), encoding='utf-8')
    return messages

# 简单循环
print('🥔 TG Bridge 启动')
send('🟢 GBT 直连桥接已激活。你现在可以进入UU远程，我会通过这里跟你联系。')

while True:
    msgs = check_incoming()
    for m in msgs:
        text = m['text']
        print(f'[TG] {text}')
        # 简单回复
        if text.startswith('/'):
            cmd = text[1:].strip()
            if cmd == 'status':
                send('📡 gbt-direct: 运行中 (ws://192.168.1.136:9876)\n📁 file-serve: 运行中 (:8765)\n⏳ 等待远程客户端连接...')
            elif cmd == 'help':
                send('/status - 查看状态\n/check - 检查连接\n任意消息 - 转发')
        else:
            send(f'收到: {text[:200]}\n(我在终端里，回复会延迟)')
    time.sleep(3)
