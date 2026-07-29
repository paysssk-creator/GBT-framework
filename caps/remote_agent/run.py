# 开发者：自由的风
"""remote_agent/run.py — GBT远程协助 · 服务端
===============================================
HTTP 服务端，等待用户代理连接。通过 JSON API 向用户机器发送操控命令。

用法:
  gbt run remote_agent serve                    启动服务端 (默认端口 9877)
  gbt run remote_agent serve '{"port":9877}'    指定端口
  gbt run remote_agent sessions                  查看已连接用户
  gbt run remote_agent cmd '{"sid":"xxx","action":"screenshot"}'
"""
import sys, json, os, time, uuid, threading, subprocess
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone

SANDBOX_DIR = Path(__file__).parent.parent.parent
DATA_DIR = Path.home() / ".gbt" / "remote_sessions"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 会话存储 — 文件共享（serve和cmd在不同进程）
SESSION_FILE = DATA_DIR / "sessions.json"
_file_lock = threading.Lock()

def _load_sessions():
    if SESSION_FILE.exists():
        try:
            return json.loads(SESSION_FILE.read_text(encoding="utf-8"))
        except: pass
    return {}

def _save_sessions(data):
    with _file_lock:
        SESSION_FILE.write_text(json.dumps(data, ensure_ascii=False, default=str), encoding="utf-8")

def _get_sessions():
    return _load_sessions()

def _update_session(sid, updates):
    data = _load_sessions()
    if sid in data:
        data[sid].update(updates)
    else:
        data[sid] = updates
    _save_sessions(data)
    return data[sid]

class AgentHandler(BaseHTTPRequestHandler):
    """用户代理连接的 HTTP 处理器"""
    
    def log_message(self, format, *args):
        pass  # 静默日志
    
    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_GET(self):
        if self.path == "/ping":
            self._json({"status": "ok", "server": "GBT Remote Agent"})
        elif self.path.startswith("/sessions"):
            data = _get_sessions()
            self._json({"sessions": {k: {"connected": v.get("connected"), "last_seen": v.get("last_seen")} for k, v in data.items()}})
    
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length > 0 else {}
        
        if self.path == "/agent/register":
            sid = body.get("sid", str(uuid.uuid4())[:8])
            name = body.get("name", f"User-{sid[:4]}")
            _update_session(sid, {
                "connected": True,
                "name": name,
                "last_seen": datetime.now(timezone.utc).isoformat(),
                "pending_cmd": None,
                "cmd_result": None,
                "history": [],
            })
            self._json({"ok": True, "sid": sid, "message": f"已连接: {name}"})
        
        elif self.path == "/agent/poll":
            sid = body.get("sid", "")
            data = _get_sessions()
            if sid not in data:
                self._json({"ok": False, "error": "会话不存在，请重新注册"})
                return
            s = data[sid]
            s["last_seen"] = datetime.now(timezone.utc).isoformat()
            s["connected"] = True
            cmd = s.pop("pending_cmd", None)
            _save_sessions(data)
            if cmd:
                self._json({"ok": True, "has_cmd": True, "cmd": cmd})
            else:
                self._json({"ok": True, "has_cmd": False})
        
        elif self.path == "/agent/result":
            sid = body.get("sid", "")
            result = body.get("result", {})
            data = _get_sessions()
            if sid in data:
                data[sid]["cmd_result"] = result
                hist = data[sid].setdefault("history", [])
                hist.append({
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "cmd": body.get("cmd", ""),
                    "ok": result.get("ok", False),
                })
                _save_sessions(data)
            self._json({"ok": True, "received": True})
        
        else:
            self._json({"error": "not found"}, 404)

def do_serve(params=None):
    """启动协助服务端"""
    params = params or {}
    port = int(params.get("port", 9877))
    host = params.get("host", "0.0.0.0")
    
    server = HTTPServer((host, port), AgentHandler)
    print(f"🆘 GBT远程协助服务端已启动: http://{host}:{port}", file=sys.stderr)
    print(f"   用户代理连接地址: http://<本机IP>:{port}", file=sys.stderr)
    print(f"   按 Ctrl+C 停止", file=sys.stderr)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
    return {"ok": True, "stopped": True}

def do_sessions(params=None):
    data = _get_sessions()
    return {
        "ok": True,
        "sessions": {k: {"name": v.get("name"), "connected": v.get("connected"), "last_seen": v.get("last_seen")}
                    for k, v in data.items()},
        "count": len(data),
    }

def do_cmd(params):
    """向用户代理发送操控命令"""
    sid = params.get("sid", "")
    action = params.get("action", "screenshot")
    cmd_params = params.get("params", {})
    
    if not sid:
        data = _get_sessions()
        connected = [k for k, v in data.items() if v.get("connected")]
        if not connected:
            return {"ok": False, "error": "没有已连接的用户"}
        sid = connected[0]
    
    data = _get_sessions()
    if sid not in data:
        return {"ok": False, "error": f"会话不存在: {sid}"}
    s = data[sid]
    if not s.get("connected"):
        return {"ok": False, "error": f"用户 {s['name']} 已断开"}
    s["pending_cmd"] = {"action": action, "params": cmd_params, "ts": datetime.now(timezone.utc).isoformat()}
    s["cmd_result"] = None
    _save_sessions(data)
    
    # 等待结果 (最多 30 秒)
    waited = 0
    while waited < 30:
        time.sleep(0.5)
        waited += 0.5
        data = _get_sessions()
        if sid in data and data[sid].get("cmd_result") is not None:
            result = data[sid]["cmd_result"]
            data[sid]["cmd_result"] = None
            _save_sessions(data)
            return {"ok": True, "sid": sid, "action": action, "result": result}
    
    return {"ok": False, "error": "等待用户代理响应超时 (30s)", "sid": sid}

HANDLERS = {"serve": do_serve, "sessions": do_sessions, "cmd": do_cmd}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 else "serve"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知动作: {action}", "available": list(HANDLERS.keys())})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
