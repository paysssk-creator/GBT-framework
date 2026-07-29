"""_2captcha — 2Captcha共享库能力模块"""
from caps._2captcha import CaptchaSolver, ProxyNetwork, FingerprintAPI, CloudBrowser
import sys, json

def do_info(params=None):
    return {"ok": True, "module": "_2captcha", "exports": ["CaptchaSolver", "ProxyNetwork", "FingerprintAPI", "CloudBrowser"], "note": "共享库模块，通过 import caps._2captcha 使用"}

def do_solve_captcha(params=None):
    try:
        solver = CaptchaSolver()
        return {"ok": True, "action": "solve_captcha", "note": "通过 CaptchaSolver 实例方法调用"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def do_get_proxy(params=None):
    try:
        proxy = ProxyNetwork()
        return {"ok": True, "action": "get_proxy", "note": "通过 ProxyNetwork 实例方法调用"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def do_get_fingerprint(params=None):
    try:
        fp = FingerprintAPI()
        return {"ok": True, "action": "get_fingerprint", "note": "通过 FingerprintAPI 实例方法调用"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def do_get_browser(params=None):
    try:
        browser = CloudBrowser()
        return {"ok": True, "action": "get_browser", "note": "通过 CloudBrowser 实例方法调用"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

HANDLERS = {"info": do_info, "solve_captcha": do_solve_captcha, "get_proxy": do_get_proxy, "get_fingerprint": do_get_fingerprint, "get_browser": do_get_browser}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "run.py" else "info"
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知: {action}"})
    print(json.dumps(h({}), ensure_ascii=False, default=str))