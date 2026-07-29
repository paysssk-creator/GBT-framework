# cmd_server.py - 文件中继服务端
from http.server import HTTPServer, BaseHTTPRequestHandler
import json, os, time
from pathlib import Path

CMD_FILE = Path(__file__).parent / ".gbt" / "cmd_queue.json"
RESULT_DIR = Path(__file__).parent / ".gbt" / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
CMD_FILE.parent.mkdir(parents=True, exist_ok=True)

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/cmd.json", "/cmd.json/"):
            if CMD_FILE.exists():
                data = json.loads(CMD_FILE.read_text())
                self._json(data)
                CMD_FILE.unlink()  # 消费后删除
            else:
                self._json({"id": None, "msg": "no command"})
        else:
            self._json({"ok": True})
    
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length))
        cid = data.get("id", str(int(time.time())))
        out_file = RESULT_DIR / f"{cid}.json"
        out_file.write_text(json.dumps(data, ensure_ascii=False))
        self._json({"ok": True})
    
    def _json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
    
    def log_message(self, *a): pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "9879"))
    print(f"CMD Server on :{port}")
    HTTPServer(("0.0.0.0", port), H).serve_forever()
