# gbt_http_relay.py - HTTP命令中继 v2.0 (服务端)
# 支持两种协议: 
#   Agent协议: /agent/register /agent/poll /agent/result (remote_client.py)
#   Relay协议: GET/POST / (relay_agent.py)
from http.server import HTTPServer, BaseHTTPRequestHandler
import json, time, threading, os, secrets
from datetime import datetime
PENDING_BROADCAST = []  # commands auto-pushed to new agents on register
AGENTS = {}       # {sid: {name, last_seen, connected_at, commands: [{cmd_id, action, params}]}}
CMD_RESULTS = {}  # {cmd_id: result}
RELAY_CMDS = {}   # {cmd_id: {command, timeout}}  (legacy relay protocol)
RELAY_RESULTS = {}# {cmd_id: result}
AUTH_TOKEN = os.environ.get("GBT_RELAY_TOKEN", "")

def _check_auth(headers):
    if not AUTH_TOKEN:
        return True  # 未配置Token时不强制认证(向后兼容)
    return secrets.compare_digest(headers.get("X-GBT-Token", ""), AUTH_TOKEN)

_lock = threading.Lock()

class H(BaseHTTPRequestHandler):
    # ── Agent Protocol ──
    def _handle_agent_register(self, data):
        sid = data.get("sid", str(int(time.time())))
        with _lock:
            if sid not in AGENTS:
                cmds = list(PENDING_BROADCAST)  # auto-push pending broadcast
                AGENTS[sid] = {
                    "name": data.get("name", "unknown"),
                    "last_seen": time.time(),
                    "connected_at": datetime.now().isoformat(),
                    "commands": cmds
                }
            else:
                AGENTS[sid]["last_seen"] = time.time()
                AGENTS[sid]["name"] = data.get("name", AGENTS[sid]["name"])
        return {"ok": True, "sid": sid, "pending_cmds": len(AGENTS[sid]["commands"])}

    def _handle_agent_poll(self, data):
        sid = data.get("sid", "")
        with _lock:
            if sid not in AGENTS:
                return {"ok": False, "error": f"会话 {sid} 不存在，请重新注册"}
            agent = AGENTS[sid]
            agent["last_seen"] = time.time()
            if agent["commands"]:
                cmd = agent["commands"].pop(0)
                return {"ok": True, "has_cmd": True, "cmd": cmd}
        return {"ok": True, "has_cmd": False}

    def _handle_agent_result(self, data):
        sid = data.get("sid", "")
        cmd_id = data.get("cmd_id", "")
        result = data.get("result", {})
        with _lock:
            CMD_RESULTS[cmd_id] = {"sid": sid, "result": result, "time": datetime.now().isoformat()}
            if sid in AGENTS:
                AGENTS[sid]["last_seen"] = time.time()
        return {"ok": True}

    def _handle_agent_list(self, data):
        with _lock:
            agents = []
            for sid, a in AGENTS.items():
                agents.append({
                    "sid": sid, "name": a["name"],
                    "last_seen": datetime.fromtimestamp(a["last_seen"]).isoformat(),
                    "connected_at": a["connected_at"],
                    "pending_cmds": len(a["commands"])
                })
        return {"ok": True, "agents": agents, "count": len(agents)}

    # ── Relay Protocol (legacy) ──
    def _handle_relay_get(self):
        with _lock:
            pending = {k: v for k, v in RELAY_CMDS.items() if k not in RELAY_RESULTS}
        if pending:
            cmd_id, cmd = next(iter(pending.items()))
            return {"ok": True, "type": "command", "id": cmd_id, "command": cmd["command"], "timeout": cmd.get("timeout", 60)}
        return {"ok": True, "type": "wait", "msg": "no pending commands"}

    def _handle_relay_post(self, data):
        if "command" in data:
            cmd_id = str(int(time.time() * 1000))
            with _lock:
                RELAY_CMDS[cmd_id] = {"command": data["command"], "timeout": data.get("timeout", 60)}
            return {"ok": True, "id": cmd_id}
        else:
            cmd_id = data.get("id", "")
            with _lock:
                RELAY_RESULTS[cmd_id] = data
            return {"ok": True}

    def _handle_agent_send(self, data):
        sid = data.get("sid", "")
        action = data.get("action", "exec")
        params = data.get("params", {})
        cmd_id = data.get("cmd_id", str(int(time.time() * 1000)))
        with _lock:
            if sid not in AGENTS:
                return {"ok": False, "error": f"Agent {sid} not found"}
            AGENTS[sid]["commands"].append({"cmd_id": cmd_id, "action": action, "params": params})
        return {"ok": True, "cmd_id": cmd_id, "sid": sid}

    def _handle_agent_broadcast(self, data):
        action = data.get("action", "exec")
        params = data.get("params", {})
        persist = data.get("persist", True)  # persist for future agents too
        with _lock:
            sent = []
            cmd_base = {"action": action, "params": params}
            if persist:
                cid = str(int(time.time() * 1000))
                cmd_base["cmd_id"] = cid
                PENDING_BROADCAST.append(cmd_base.copy())
            for sid in AGENTS:
                cid = str(int(time.time() * 1000)) + "_" + sid[:4]
                AGENTS[sid]["commands"].append({"cmd_id": cid, "action": action, "params": params})
                sent.append({"sid": sid, "cmd_id": cid})
        return {"ok": True, "sent": sent, "count": len(sent), "pending_queue": len(PENDING_BROADCAST)}

    # ── HTTP Routing ──
    def do_GET(self):
        if not _check_auth(self.headers):
            self.send_response(403); self.end_headers(); return
        path = self.path.split("?")[0]
        if path == "/agents":
            self._json(self._handle_agent_list({}))
        elif path == "/agent/list":
            self._json(self._handle_agent_list({}))
        else:
            self._json(self._handle_relay_get())

    def do_POST(self):
        if not _check_auth(self.headers):
            self.send_response(403); self.end_headers(); return

        try:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length)) if length > 0 else {}
        except:
            data = {}

        path = self.path.split("?")[0]

        if path == "/agent/register":
            self._json(self._handle_agent_register(data))
        elif path == "/agent/poll":
            self._json(self._handle_agent_poll(data))
        elif path == "/agent/result":
            self._json(self._handle_agent_result(data))
        elif path == "/agent/list":
            self._json(self._handle_agent_list(data))
        elif path == "/agent/send":
            self._json(self._handle_agent_send(data))
        elif path == "/agent/broadcast":
            self._json(self._handle_agent_broadcast(data))
        else:
            self._json(self._handle_relay_post(data))

    def _json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def log_message(self, *a): pass


# ── Public API ──
def start_server(port=9877):
    print(f"GBT HTTP Relay v2.0 on :{port}")
    HTTPServer(('0.0.0.0', port), H).serve_forever()

def send_command(command, timeout=60):
    cmd_id = str(int(time.time() * 1000))
    with _lock:
        RELAY_CMDS[cmd_id] = {"command": command, "timeout": timeout}
    return cmd_id

def get_result(cmd_id, wait_sec=30):
    for _ in range(wait_sec * 2):
        with _lock:
            if cmd_id in RELAY_RESULTS:
                return RELAY_RESULTS.pop(cmd_id)
        time.sleep(0.5)
    return None

def send_agent_cmd(sid, action, params=None, cmd_id=None):
    """向指定agent发送命令"""
    if cmd_id is None:
        cmd_id = str(int(time.time() * 1000))
    cmd = {"cmd_id": cmd_id, "action": action, "params": params or {}}
    with _lock:
        if sid not in AGENTS:
            return None
        AGENTS[sid]["commands"].append(cmd)
    return cmd_id

def wait_agent_result(cmd_id, timeout_sec=30):
    """等待agent返回结果"""
    for _ in range(timeout_sec * 2):
        with _lock:
            if cmd_id in CMD_RESULTS:
                return CMD_RESULTS.pop(cmd_id)
        time.sleep(0.5)
    return None

def broadcast_cmd(action, params=None):
    """向所有在线agent广播命令"""
    cmd_ids = []
    with _lock:
        for sid in AGENTS:
            cid = str(int(time.time() * 1000))
            AGENTS[sid]["commands"].append({"cmd_id": cid, "action": action, "params": params or {}})
            cmd_ids.append((sid, cid))
    return cmd_ids

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "send":
        cmd = sys.argv[2]
        cid = send_command(cmd)
        print(f"CMD_ID={cid}")
        result = get_result(cid, 60)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print('{"ok":false,"error":"timeout"}')
    else:
        start_server()
