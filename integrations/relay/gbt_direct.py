# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
# gbt_direct.py — GBT 直连通道
# ============================================
# 用法:
#   服务端(本机):  python gbt_direct.py serve
#   客户端(远程):  python gbt_direct.py connect wss://YOUR_IP:9876
#
# 单文件，双端通用。远程连上后，本机直接发命令执行。
# ============================================
import asyncio, json, sys, os, subprocess, time, hashlib, base64
from datetime import datetime
from pathlib import Path

WS_PORT = 9876
AUTH_SECRET = os.environ.get("GBT_DIRECT_SECRET", "gbt-v5-direct")
WORK_DIR = Path(os.getcwd())


def sign_challenge(challenge):
    """HMAC签名验证"""
    return hashlib.sha256(f"{AUTH_SECRET}:{challenge}".encode()).hexdigest()


# ═══════════════════ 客户端 (远程机器运行) ═══════════════════
class GBTClient:
    def __init__(self, server_url):
        self.server_url = server_url
        self.ws = None
    
    async def connect(self):
        """连接服务端并保持长连接"""
        import websockets
        while True:
            try:
                async with websockets.connect(self.server_url, ping_interval=30) as ws:
                    self.ws = ws
                    print(f"✅ 已连接到 {self.server_url}")
                    # 认证
                    msg = json.loads(await ws.recv())
                    if msg.get("type") == "auth_challenge":
                        sig = sign_challenge(msg["challenge"])
                        await ws.send(json.dumps({"type": "auth_response", "signature": sig, "hostname": os.environ.get("COMPUTERNAME","?"), "cwd": str(WORK_DIR)}))
                        auth_result = json.loads(await ws.recv())
                        if auth_result.get("type") != "auth_ok":
                            print(f"❌ 认证失败: {auth_result}")
                            return
                        print("🔐 认证通过")
                    
                    # 接收命令循环
                    async for raw in ws:
                        cmd = json.loads(raw)
                        if cmd.get("type") == "exec":
                            result = await self._execute(cmd)
                            await ws.send(json.dumps(result))
                        elif cmd.get("type") == "ping":
                            await ws.send(json.dumps({"type": "pong", "time": datetime.now().isoformat()}))
            except Exception as e:
                print(f"⚠️ 连接断开: {e}, 5秒后重连...")
                await asyncio.sleep(5)
    
    async def _execute(self, cmd):
        """执行命令"""
        command = cmd.get("command", "")
        timeout = cmd.get("timeout", 60)
        cmd_id = cmd.get("id", str(int(time.time())))
        if not command:
            return {"id": cmd_id, "type": "result", "ok": False, "error": "空命令"}
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(WORK_DIR)
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "id": cmd_id, "type": "result", "ok": proc.returncode == 0,
                "code": proc.returncode,
                "stdout": stdout.decode("utf-8", errors="replace")[-8000:],
                "stderr": stderr.decode("utf-8", errors="replace")[-2000:],
                "time": datetime.now().isoformat(),
            }
        except asyncio.TimeoutError:
            return {"id": cmd_id, "type": "result", "ok": False, "error": f"超时({timeout}s)"}
        except Exception as e:
            return {"id": cmd_id, "type": "result", "ok": False, "error": str(e)}


# ═══════════════════ 服务端 (本机运行) ═══════════════════
class GBTServer:
    def __init__(self, port=WS_PORT):
        self.port = port
        self.clients = {}  # websocket -> info
    
    async def start(self):
        import websockets
        print(f"🥔 GBT Direct Server on ws://0.0.0.0:{self.port}")
        print(f"   等待远程客户端连接...")
        print(f"   客户端连接后输入命令直接执行")
        print()
        async with websockets.serve(self._handle, "0.0.0.0", self.port):
            await asyncio.Future()  # 永久运行
    
    async def _handle(self, ws):
        """处理单个客户端连接"""
        # 认证
        challenge = base64.b64encode(os.urandom(32)).decode()
        await ws.send(json.dumps({"type": "auth_challenge", "challenge": challenge}))
        
        try:
            response = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
        except:
            return
        
        expected = sign_challenge(challenge)
        if response.get("signature") != expected:
            await ws.send(json.dumps({"type": "auth_error", "msg": "签名不匹配"}))
            return
        
        await ws.send(json.dumps({"type": "auth_ok", "msg": "认证通过"}))
        hostname = response.get("hostname", "?")
        self.clients[ws] = {"hostname": hostname, "connected": datetime.now().isoformat()}
        print(f"🔗 客户端已连接: {hostname} (共{len(self.clients)}个在线)")
        
        try:
            async for raw in ws:
                msg = json.loads(raw)
                if msg.get("type") == "result":
                    self._print_result(msg)
                elif msg.get("type") == "pong":
                    pass
        except Exception:
            pass
        finally:
            self.clients.pop(ws, None)
            print(f"🔌 客户端断开: {hostname}")
    
    def _print_result(self, result):
        """打印执行结果"""
        ok = result.get("ok", False)
        icon = "✅" if ok else "❌"
        print(f"\n{icon} [{result.get('id','?')}] code={result.get('code','?')}")
        stdout = result.get("stdout", "")
        if stdout:
            for line in stdout.strip().split("\n")[-20:]:
                print(f"   {line}")
        stderr = result.get("stderr", "")
        if stderr:
            print(f"   [stderr] {stderr[:200]}")
        print()


# ═══════════════════ 交互式命令发送 ═══════════════════
async def interactive_serve(port=WS_PORT):
    """启动服务端 + 交互式命令行"""
    import websockets
    server = GBTServer(port)
    
    # 在后台启动服务器
    loop = asyncio.get_event_loop()
    server_task = loop.create_task(server.start())
    await asyncio.sleep(1)
    
    print("💡 输入命令发送到远程执行 (输入 quit 退出)")
    print("   例如: python caps/stock_trader/run.py scan")
    print()
    
    while True:
        try:
            cmd = input("GBT> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        
        if not cmd:
            continue
        if cmd.lower() in ("quit", "exit", "q"):
            break
        
        # 发送到所有已连接客户端
        if not server.clients:
            print("⚠️ 没有客户端连接")
            continue
        
        cmd_id = str(int(time.time()))
        msg = json.dumps({"type": "exec", "id": cmd_id, "command": cmd, "timeout": 120})
        
        clients = list(server.clients.keys())
        for ws in clients:
            try:
                await ws.send(msg)
            except:
                pass
    
    server_task.cancel()
    try:
        await server_task
    except:
        pass


# ═══════════════════ 入口 ═══════════════════
def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  服务端: python gbt_direct.py serve [端口]")
        print("  客户端: python gbt_direct.py connect <服务端URL>")
        print("  交互:   python gbt_direct.py interactive [端口]")
        return
    
    action = sys.argv[1]
    
    if action == "serve":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else WS_PORT
        asyncio.run(GBTServer(port).start())
    
    elif action == "connect":
        url = sys.argv[2] if len(sys.argv) > 2 else f"ws://localhost:{WS_PORT}"
        asyncio.run(GBTClient(url).connect())
    
    elif action == "interactive":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else WS_PORT
        asyncio.run(interactive_serve(port))
    
    else:
        print(f"未知动作: {action}")


if __name__ == "__main__":
    main()
