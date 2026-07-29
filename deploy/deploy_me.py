# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
# deploy_me.py — GBT远程部署代理 v3.0
# 客户运行此脚本 → 自动建隧道 → 自动上报API → GBT接手远程部署
# ============================================================
"""GBT Remote Deploy Agent v3.0

客户运行: python deploy_me.py [--session SESSION_ID]
  → 自动下载cloudflared(如无)
  → 启动本地API服务
  → 建立cloudflared隧道
  → 自动上报隧道URL到GBT API
  → GBT自动连接 → 远程部署项目

全程无需复制粘贴, GBT自动接管。
"""
import subprocess, sys, json, os, time, socket, secrets, shlex
import http.server, threading, shutil, urllib.request
from pathlib import Path

# 配置
SESSION_ID = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--session" else secrets.token_hex(8)
TOKEN = secrets.token_hex(16)
LOCAL_PORT = 15888
API_REPORT_URL = os.environ.get("GBT_API", "https://gbtxiaotudou.com/api/deploy/tunnel-handshake")

def _install_cloudflared():
    """自动安装cloudflared"""
    cf = shutil.which("cloudflared")
    if cf: return cf

    print("[1/5] 安装cloudflared隧道工具...", flush=True)
    if sys.platform == "win32":
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
        target = Path.home() / ".gbt" / "cloudflared.exe"
        target.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, str(target))
        return str(target)
    else:
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        target = "/usr/local/bin/cloudflared"
        r = subprocess.run(["curl", "-sSL", "-o", target, url], capture_output=True)
        if r.returncode == 0:
            subprocess.run(["chmod", "+x", target])
            return target
        return None

# ═══════════════ HTTP API ═══════════════
class DeployAPI(http.server.BaseHTTPRequestHandler):
    def verify(self):
        return secrets.compare_digest(self.headers.get("X-GBT-Token", ""), TOKEN)

    def log_message(self, *a): pass

    def do_GET(self):
        if not self.verify():
            self.send_response(403); self.end_headers(); return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "ok": True, "hostname": socket.gethostname(),
            "platform": sys.platform, "python": sys.version.split()[0],
            "session": SESSION_ID
        }).encode())

    def do_POST(self):
        if not self.verify():
            self.send_response(403); self.end_headers(); return
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            cmd_parts = shlex.split(body.get("cmd", "echo NO_CMD"))
            timeout = body.get("timeout", 300)
            cwd = body.get("cwd", None)
            r = subprocess.run(cmd_parts, capture_output=True, text=True,
                timeout=timeout, cwd=cwd,
                encoding="gbk" if sys.platform == "win32" else "utf-8",
                errors="replace")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "ok": r.returncode == 0,
                "stdout": r.stdout[-8000:], "stderr": r.stderr[-4000:],
                "code": r.returncode
            }).encode())
        except subprocess.TimeoutExpired:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": "命令超时"}).encode())
        except Exception as e:
            self.send_response(500); self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": str(e)[:200]}).encode())

# ═══════════════ 隧道 ═══════════════
def start_tunnel(port, cloudflared_path):
    import re
    proc = subprocess.Popen(
        [cloudflared_path, "tunnel", "--url", f"http://localhost:{port}"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    deadline = time.time() + 45
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line: time.sleep(0.5); continue
        m = re.search(r'https://[-a-z0-9]+\.trycloudflare\.com', line)
        if m: return proc, m.group(0)
    proc.terminate()
    return None, None

def report_to_api(tunnel_url):
    """自动上报隧道URL到GBT API"""
    try:
        data = json.dumps({
            "session_id": SESSION_ID,
            "tunnel_url": tunnel_url,
            "token": TOKEN,
            "hostname": socket.gethostname(),
            "platform": sys.platform,
        }).encode()
        req = urllib.request.Request(API_REPORT_URL, data=data,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read()), None
    except Exception as e:
        return None, str(e)

# ═══════════════ 主入口 ═══════════════
if __name__ == "__main__":
    print(f"\n🥔 GBT 远程部署代理 v3.0  会话: {SESSION_ID[:8]}", flush=True)

    # 1. 安装cloudflared
    cf_path = _install_cloudflared()
    if not cf_path:
        print("❌ cloudflared安装失败", flush=True)
        sys.exit(1)

    # 2. 启动本地API
    print(f"[2/5] 启动本地服务 :{LOCAL_PORT}", flush=True)
    try:
        server = http.server.HTTPServer(("127.0.0.1", LOCAL_PORT), DeployAPI)
    except OSError:
        LOCAL_PORT = secrets.randbelow(5000) + 15000
        server = http.server.HTTPServer(("127.0.0.1", LOCAL_PORT), DeployAPI)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    # 3. 启动隧道
    print("[3/5] 建立安全隧道...", flush=True)
    tunnel_proc, tunnel_url = start_tunnel(LOCAL_PORT, cf_path)
    if not tunnel_url:
        print("❌ 隧道启动失败", flush=True)
        server.shutdown(); sys.exit(1)

    # 4. 自动上报
    print("[4/5] 上报隧道地址到GBT...", flush=True)
    resp, err = report_to_api(tunnel_url)
    if err:
        print(f"⚠️ 上报失败: {err}", flush=True)
        print(f"\n手动发给GBT: {tunnel_url}?token={TOKEN}", flush=True)
    else:
        print("✅ GBT已收到隧道地址，正在连接...", flush=True)

    # 5. 等待
    print(f"""
[5/5] ╔══════════════════════════════════════╗
       ║  GBT正在远程部署你的项目...            ║
       ║  请勿关闭此窗口                        ║
       ║  Ctrl+C 断开连接                       ║
       ╚══════════════════════════════════════╝
""", flush=True)

    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 断开连接。", flush=True)
        server.shutdown()
        tunnel_proc.terminate()
