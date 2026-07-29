# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
# remote_control/quick_test.py — 一键端到端测试
# ============================================================
"""快速验证远程操控通道是否打通"""
import http.server, socketserver, threading, json, time, subprocess, os, sys

PORT = 8765

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/test":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status":"ok", "message":"GBT Remote Control works!", "time": time.strftime("%H:%M:%S")}).encode())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>GBT Remote Agent Test</h1><p>Channel active!</p>")

# 启动 HTTP 服务
def serve():
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"✅ HTTP server on 127.0.0.1:{PORT}")
        httpd.serve_forever()

threading.Thread(target=serve, daemon=True).start()
time.sleep(1)

# 验证本地
import urllib.request
try:
    resp = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/test", timeout=3)
    data = json.loads(resp.read())
    print(f"✅ Local API: {data}")
except Exception as e:
    print(f"❌ Local FAIL: {e}")
    sys.exit(1)

# 启动 cloudflared 隧道
CF = r"C:\Program Files (x86)\cloudflared\cloudflared.exe"
if not os.path.exists(CF):
    print("❌ cloudflared not found")
    sys.exit(1)

proc = subprocess.Popen(
    [CF, "tunnel", "--url", f"http://localhost:{PORT}"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
)

import re
tunnel_url = None
for _ in range(45):
    line = proc.stdout.readline()
    if not line: break
    print(f"   [cloudflared] {line.rstrip()}")
    m = re.search(r'https://[^\s]+\.trycloudflare\.com', line)
    if m:
        tunnel_url = m.group(0)
        break

if tunnel_url:
    print(f"\n🔗 Tunnel URL: {tunnel_url}")
    # 测试隧道
    try:
        resp = urllib.request.urlopen(f"{tunnel_url}/api/test", timeout=15)
        data = json.loads(resp.read())
        print(f"✅ Tunnel API: {data}")
        print("\n🟢 远程操控通道验证成功！")
    except Exception as e:
        print(f"❌ Tunnel FAIL: {e}")
else:
    print("❌ Tunnel not established")

proc.terminate()
