#!/usr/bin/env python3
"""GBT小土豆 V5 · Desktop App Launcher"""
import http.server, socketserver, subprocess, threading, webbrowser, sys, os, time, socket

PORT = 9130

# PyInstaller extracts data files to sys._MEIPASS
if getattr(sys, 'frozen', False):
    APP_DIR = sys._MEIPASS
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

def find_chrome():
    paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for p in paths:
        if os.path.exists(p): return p
    return None

def main():
    os.chdir(APP_DIR)

    # Find free port
    port = PORT
    for _ in range(5):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port)); break
        except OSError:
            port += 1

    # Start server
    handler = http.server.SimpleHTTPRequestHandler
    try:
        httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    except OSError as e:
        print(f"[GBT小土豆] 启动失败: {e}")
        input("按 Enter 退出...")
        return

    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    url = f"http://127.0.0.1:{port}"
    print(f"[GBT小土豆] 服务已启动: {url}")

    chrome = find_chrome()
    if chrome:
        proc = subprocess.Popen([chrome, f"--app={url}",
            "--window-size=1280,820", "--window-position=center",
            "--disable-extensions", "--no-first-run", "--disable-sync"])
        proc.wait()
    else:
        webbrowser.open(url)
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt: pass

    print("[GBT小土豆] 正在关闭...")
    httpd.shutdown()

if __name__ == "__main__":
    main()
