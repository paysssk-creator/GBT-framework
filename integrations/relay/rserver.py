# GBT Remote Command Server - 微型 (认证版)
# 部署到远程机器后: python rserver.py [TOKEN]
# 本机连接: curl -H "X-GBT-Token: TOKEN" http://REMOTE_IP:9998/exec -d '{"cmd":"..."}'
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess, json, sys, os, secrets

AUTH_TOKEN = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GBT_REMOTE_TOKEN", secrets.token_hex(16))
os.chdir(os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else '.')

class H(BaseHTTPRequestHandler):
    def _check_auth(self):
        return secrets.compare_digest(
            self.headers.get("X-GBT-Token", ""), AUTH_TOKEN)

    def do_POST(self):
        if not self._check_auth():
            self.send_response(403); self.end_headers(); return
        try:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length)) if length > 0 else {}
            cmd = data.get('cmd', 'echo NO_CMD')
            timeout = data.get('timeout', 30)
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
            result = {'ok': True, 'out': r.stdout[-5000:], 'err': r.stderr[-1000:], 'code': r.returncode}
        except Exception as e:
            result = {'ok': False, 'error': str(e)}
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
    
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'GBT Remote Server OK')

    def log_message(self, *args):
        pass

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9998
    print(f'GBT Remote Server on :{port}')
    HTTPServer(('0.0.0.0', port), H).serve_forever()
