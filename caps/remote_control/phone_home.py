# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
# phone_home.py — GBT 侧收件箱
# agent 自动回连 → 这里收到 session → 自动接入
# ============================================================
"""GBT Phone Home Server — 接收远程 agent 自动回连

用法:
  python phone_home.py                    # 启动监听 (自动创建隧道)
  python phone_home.py --port 9999        # 指定端口
"""

import http.server, json, threading, time, sys, os, subprocess
from pathlib import Path
from datetime import datetime

SESSIONS_DIR = Path.home() / ".gbt_sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

class PhoneHomeHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        """接收 session JSON"""
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            session = json.loads(body)
            
            # 保存
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            host = session.get("hostname", "unknown")
            fname = f"session_{host}_{ts}.json"
            path = SESSIONS_DIR / fname
            path.write_text(json.dumps(session, indent=2, ensure_ascii=False))
            
            # 保存为 latest
            latest = SESSIONS_DIR / "latest.json"
            latest.write_text(json.dumps(session, indent=2, ensure_ascii=False))
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "host": host}).encode())
            
            print(f"\n📥 Session received: {host}")
            print(f"   Services: {len(session.get('services', []))}")
            print(f"   Token: {session.get('token', 'N/A')[:16]}...")
            print(f"   Saved: {fname}")
            
            # 回调钩子
            if PhoneHomeHandler._on_session:
                PhoneHomeHandler._on_session(session)
                
        except Exception as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
            print(f"Error: {e}")

    def do_GET(self):
        """健康检查 / 列出最新 session"""
        if self.path == "/latest":
            latest = SESSIONS_DIR / "latest.json"
            if latest.exists():
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(latest.read_bytes())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'{"error":"no sessions"}')
        else:
            self.send_response(200)
            self.end_headers()
            files = sorted(SESSIONS_DIR.glob("session_*.json"), reverse=True)
            body = {"status": "listening", "sessions": len(files), "latest": files[0].name if files else None}
            self.wfile.write(json.dumps(body).encode())

    def log_message(self, *args):
        pass  # 静默

PhoneHomeHandler._on_session = None

def start_tunnel(port):
    """启动 cloudflared 隧道"""
    cf_paths = [
        r"C:\Program Files (x86)\cloudflared\cloudflared.exe",
    ]
    cf = None
    for p in cf_paths:
        if Path(p).exists():
            cf = p
            break
    if not cf:
        print("cloudflared not found - run without tunnel on port", port)
        return None

    proc = subprocess.Popen(
        [cf, "tunnel", "--url", f"http://localhost:{port}"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True
    )
    import re
    for _ in range(30):
        line = proc.stdout.readline()
        if not line: break
        m = re.search(r'https://[^\s]+\.trycloudflare\.com', line)
        if m:
            return m.group(0)
    return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9877)
    parser.add_argument("--no-tunnel", action="store_true")
    args = parser.parse_args()

    port = args.port
    tunnel_url = None
    
    if not args.no_tunnel:
        print("Starting cloudflared tunnel...")
        tunnel_url = start_tunnel(port)
    
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), PhoneHomeHandler)
    
    print("=" * 50)
    print("  GBT Phone Home Server")
    print(f"  Listening on port {port}")
    if tunnel_url:
        print(f"  Public: {tunnel_url}")
        print(f"  Agent POST URL: {tunnel_url}")
    print(f"  Sessions: {SESSIONS_DIR}")
    print("=" * 50)
    
    if tunnel_url:
        # 保存收件箱 URL 供 agent.py 使用
        inbox_path = Path.home() / ".gbt_inbox_url"
        inbox_path.write_text(tunnel_url)
        print(f"\nInbox URL saved: {inbox_path}")
    
    print("\nWaiting for agents... Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped")
