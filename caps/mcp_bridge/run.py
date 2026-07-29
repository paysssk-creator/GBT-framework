"""mcp_bridge/run.py — GBT↔MCP通用桥接

连接所有Model Context Protocol服务:
  Context7 (实时文档) · GitHub (仓库管理) · Firecrawl (网页抓取)
  Stripe (支付) · Playwright (浏览器) · Sequential Thinking (推理)
  Memory (知识图谱) · Fetch (网页读取)

协议: JSON-RPC 2.0 over stdio
参考: https://modelcontextprotocol.io
"""
import json
from dotenv import load_dotenv
load_dotenv()

import os
import re
import subprocess
import threading
import time

import sys
from pathlib import Path

MCP_CONFIG = Path(__file__).parent.parent.parent / ".gbt" / "mcp.json"


def _load_config() -> dict:
    if not MCP_CONFIG.exists():
        return {}
    with open(MCP_CONFIG, encoding="utf-8") as f:
        return json.load(f).get("mcpServers", {})


def _resolve_env(value: str) -> str:
    """Resolve ${VAR} placeholders against env"""

    def replacer(m):
        return os.environ.get(m.group(1), "")
    return re.sub(r'\$\{(\w+)\}', replacer, value)

# ── 进程缓存 (H9: 避免每次调用都重新spawn) ──────────
# 缓存键: server_name → {"proc": Popen, "lock": Lock, "last_use": float}
_PROCESS_CACHE: dict = {}
_CACHE_TTL = 300  # 5分钟空闲后清理


def _get_or_spawn(server_name: str, config: dict, env: dict) -> dict:
    """获取已缓存的进程 或 新启动一个。"""
    now = time.time()

    if server_name in _PROCESS_CACHE:
        entry = _PROCESS_CACHE[server_name]
        proc = entry["proc"]
        if proc.poll() is not None:
            # 进程已死, 清除缓存
            try:
                proc.stdin.close()
                proc.stdout.close()
                proc.stderr.close()
            except Exception:
                pass
            del _PROCESS_CACHE[server_name]

    if server_name not in _PROCESS_CACHE:
        cmd = [config["command"]] + config.get("args", [])
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env,
            cwd=config.get("cwd", ".")
        )
        _PROCESS_CACHE[server_name] = {
            "proc": proc,
            "lock": threading.Lock(),
            "last_use": now
        }

    entry = _PROCESS_CACHE[server_name]
    entry["last_use"] = now
    return entry


def _send_mcp_request(entry: dict, request_json: str, timeout: float) -> dict | None:
    """向缓存的MCP进程发送JSON-RPC请求并读取响应。

    调用者必须持有 entry["lock"]。
    返回解析后的JSON消息, 或超时/死亡时返回 None。
    """
    proc = entry["proc"]
    try:
        proc.stdin.write(request_json + "\n")
        proc.stdin.flush()
    except (BrokenPipeError, OSError):
        return None

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            line = proc.stdout.readline()
        except Exception:
            return None
        if not line:
            # EOF — 进程已退出
            return None
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            # 只要包含 result 或 error 就视为响应
            if "result" in msg or "error" in msg:
                return msg
        except json.JSONDecodeError:
            continue
    return None




def do_list_servers(params: dict) -> dict:
    """列出所有已配置的MCP服务器"""
    config = _load_config()
    servers = {}
    for name, cfg in config.items():
        servers[name] = {
            "command": cfg.get("command", "?"),
            "args": cfg.get("args", []),
            "has_env": list(cfg.get("env", {}).keys()),
            "status": "configured"
        }
    return {"ok": True, "servers": servers, "total": len(servers)}


def _do_mcp_call(server_name: str, method: str, req_params: dict,
                 params: dict, timeout_key: str = "timeout",
                 default_timeout: float = 15) -> dict:
    """通用MCP调用 — 优先使用进程缓存, 失败则fallback单次spawn"""
    config = _load_config()
    if server_name not in config:
        return None, {"ok": False, "error": f"未知服务器: {server_name}",
                      "available": list(config.keys())}

    cfg = config[server_name]
    env = os.environ.copy()
    for k, v in cfg.get("env", {}).items():
        env[k] = _resolve_env(v)

    request = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": method,
        "params": req_params
    })

    timeout = params.get(timeout_key, default_timeout)

    # 尝试使用进程缓存
    try:
        entry = _get_or_spawn(server_name, cfg, env)
        with entry["lock"]:
            msg = _send_mcp_request(entry, request, timeout)
        if msg is not None:
            return msg, None
    except Exception:
        pass

    # Fallback: 单次 subprocess.run
    try:
        cmd = [cfg["command"]] + cfg.get("args", [])
        proc = subprocess.run(cmd, input=request + "\n",
            capture_output=True, text=True,
            timeout=timeout, env=env, cwd=cfg.get("cwd", "."))
        output = proc.stdout.strip() or proc.stderr.strip()
        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                return msg, output
            except json.JSONDecodeError:
                continue
        return None, output
    except subprocess.TimeoutExpired:
        return None, {"ok": False, "error": f"超时: {server_name}"}
    except FileNotFoundError:
        return None, {"ok": False,
                      "error": f"命令未找到: {cfg['command']} (需要安装Node.js/npm)"}
    except Exception as e:
        return None, {"ok": False, "error": str(e)}


def do_list_tools(params: dict) -> dict:
    """通过MCP协议列出服务器工具(使用进程缓存)"""
    server_name = params.get("server", "context7")
    msg, err = _do_mcp_call(server_name, "tools/list", {},
                            params, "timeout", 15)
    if err:
        return err

    if msg is None:
        return {"ok": True, "server": server_name, "tools": [],
                "note": "MCP服务器无响应, 可能需要Node.js>=18及npx可用"}

    if "result" in msg and "tools" in msg["result"]:
        tools = []
        for t in msg["result"]["tools"]:
            tools.append({
                "name": t.get("name"),
                "description": t.get("description", "")[:200],
                "input_schema": t.get("inputSchema", {})
            })
        return {"ok": True, "server": server_name,
                "tools": tools, "total": len(tools)}
    if "error" in msg:
        return {"ok": False, "error": msg["error"]}
    return {"ok": True, "server": server_name, "tools": [],
            "note": "非标准响应格式"}


def do_call_tool(params: dict) -> dict:
    """调用MCP工具(使用进程缓存)"""
    server_name = params.get("server", "context7")
    tool_name = params.get("tool", "")
    tool_args = params.get("args", {})

    if not tool_name:
        return {"ok": False, "error": "缺少 tool 参数"}

    msg, err = _do_mcp_call(server_name, "tools/call",
                            {"name": tool_name, "arguments": tool_args},
                            params, "timeout", 30)
    if err:
        return err

    if msg is None:
        return {"ok": False, "error": f"MCP服务器 {server_name} 无响应"}

    if "result" in msg:
        return {"ok": True, "server": server_name,
                "tool": tool_name, "result": msg["result"]}
    if "error" in msg:
        return {"ok": False, "error": msg["error"]}
    return {"ok": True, "server": server_name, "tool": tool_name,
            "result": json.dumps(msg, default=str)[:1000],
            "note": "非标准响应格式"}




HANDLERS = {
    "list_servers": do_list_servers,
    "list_tools": do_list_tools,
    "call_tool": do_call_tool,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "list_servers"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    handler = HANDLERS.get(action)
    if handler is None:
        result = {"ok": False, "error": f"未知动作: {action}"}
    else:
        result = handler(params)
    print(json.dumps(result, ensure_ascii=False, default=str))
