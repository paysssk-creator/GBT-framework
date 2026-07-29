# gbt_server_light.py - 认证WebSocket命令服务器
import asyncio, json, os, secrets, time
from datetime import datetime

PORT = 9876
WORK_DIR = os.getcwd()

AUTH_TOKEN = os.environ.get("GBT_LIGHT_TOKEN", secrets.token_hex(16))
ALLOWED_COMMANDS = {"python", "pip", "git", "docker", "dir", "ls", "echo", "type", "where", "which"}

async def handle(ws):
    """处理一个客户端连接"""
    print(f"🔗 客户端已连接")
    authenticated = False
    try:
        async for raw in ws:
            try:
                cmd = json.loads(raw)
            except Exception:
                continue

            # --- 认证检查 ---
            if not authenticated:
                if cmd.get("type") == "auth" and cmd.get("token") == AUTH_TOKEN:
                    authenticated = True
                    await ws.send(json.dumps({"type": "auth_ok"}))
                    continue
                else:
                    await ws.send(json.dumps({"type": "error", "error": "需要认证: {\"type\":\"auth\",\"token\":\"...\"}"}))
                    break

            if cmd.get("type") == "exec":
                command = cmd.get("command", "")
                timeout = cmd.get("timeout", 60)
                cmd_id = cmd.get("id", str(int(time.time())))

                if not command:
                    await ws.send(json.dumps({"id": cmd_id, "type": "result", "ok": False, "error": "空命令"}))
                    continue

                # --- 命令白名单检查 ---
                first_word = command.strip().split()[0].lower() if command.strip() else ""
                if first_word not in ALLOWED_COMMANDS:
                    result = {"id": cmd_id, "type": "result", "ok": False, "error": f"禁止命令: {first_word}"}
                    await ws.send(json.dumps(result, ensure_ascii=False))
                    continue
                
                print(f"  ⚡ {command[:80]}")
                try:
                    proc = await asyncio.create_subprocess_shell(
                        command,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=WORK_DIR
                    )
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                    result = {
                        "id": cmd_id, "type": "result",
                        "ok": proc.returncode == 0,
                        "code": proc.returncode,
                        "stdout": stdout.decode("utf-8", errors="replace")[-8000:],
                        "stderr": stderr.decode("utf-8", errors="replace")[-2000:],
                        "time": datetime.now().isoformat(),
                    }
                except asyncio.TimeoutError:
                    result = {"id": cmd_id, "type": "result", "ok": False, "error": f"超时({timeout}s)"}
                except Exception as e:
                    result = {"id": cmd_id, "type": "result", "ok": False, "error": str(e)}
                
                await ws.send(json.dumps(result, ensure_ascii=False))
            
            elif cmd.get("type") == "ping":
                await ws.send('{"type":"pong"}')
    except Exception as e:
        print(f"  🔌 断开: {e}")

async def main():
    import websockets
    print(f"🥔 GBT Light Server on ws://0.0.0.0:{PORT}")
    async with websockets.serve(handle, "0.0.0.0", PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
