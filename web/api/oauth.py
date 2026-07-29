# GBT GitHub OAuth API endpoint
# Serves: /api/oauth/login (redirect to GitHub) + /api/oauth/status (check auth)
import sys, json, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from caps.github_oauth.run import do_get_login_url, do_status, do_exchange_code

def handle_request(path, method):
    # OAuth exchange (POST from callback page)
    if "/api/oauth/exchange" in path:
        import sys as _s
        body = _s.stdin.read() if not _s.stdin.isatty() else "{}"
        try:
            params = json.loads(body) if body else {}
        except:
            params = {}
        result = do_exchange_code(params)
        print("Content-Type: application/json")
        print("Access-Control-Allow-Origin: *")
        print()
        print(json.dumps(result, ensure_ascii=False, default=str))
        return
    # Login redirect
    if "/api/oauth/login" in path:
        result = do_get_login_url({})
        if result.get("ok"):
            print("Status: 302 Found")
            print(f"Location: {result['url']}")
            print()
            return
        print("Content-Type: application/json")
        print()
        print(json.dumps(result))
        return
    # Auth status
    if "/api/oauth/status" in path:
        result = do_status({})
        print("Content-Type: application/json")
        print("Access-Control-Allow-Origin: *")
        print()
        print(json.dumps(result, ensure_ascii=False, default=str))
        return
    print("Status: 404")
    print()
    print("Not found")

if __name__ == "__main__":
    import os as _os
    path = _os.environ.get("REQUEST_URI", _os.environ.get("PATH_INFO", "/api/oauth/status"))
    method = _os.environ.get("REQUEST_METHOD", "GET")
    handle_request(path, method)
