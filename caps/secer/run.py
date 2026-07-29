# 开发者：自由的风
'''secer/run.py — 安全工具集：密码生成/熵评估/JWT解码/文件哈希/安全随机/编码转换'''
import sys, json, os, hashlib, secrets, string, math, base64

# ═══════════════════════════════════════════════
# 1. 强密码生成
# ═══════════════════════════════════════════════
def do_password(params: dict) -> dict:
    length = max(4, min(128, params.get("length", 20)))
    use_upper  = params.get("upper", True)
    use_lower  = params.get("lower", True)
    use_digits = params.get("digits", True)
    use_symbols = params.get("symbols", True)

    pool = ""
    if use_upper:  pool += string.ascii_uppercase
    if use_lower:  pool += string.ascii_lowercase
    if use_digits: pool += string.digits
    if use_symbols: pool += "!@#$%^&*()-_=+[]{}|;:,.<>?/~`"

    if not pool:
        return {"ok": False, "error": "至少启用一种字符类型"}

    pwd = ''.join(secrets.choice(pool) for _ in range(length))

    # 确保至少包含每种启用的类型各一个字符
    required = []
    if use_upper:  required.append(secrets.choice(string.ascii_uppercase))
    if use_lower:  required.append(secrets.choice(string.ascii_lowercase))
    if use_digits: required.append(secrets.choice(string.digits))
    if use_symbols: required.append(secrets.choice("!@#$%^&*()-_=+[]{}|;:,.<>?/~`"))

    if required:
        pwd_list = list(pwd)
        for i, ch in enumerate(required):
            pwd_list[i] = ch
        secrets.SystemRandom().shuffle(pwd_list)
        pwd = ''.join(pwd_list)

    charset_size = len(pool)
    entropy = length * math.log2(charset_size)

    return {
        "ok": True,
        "password": pwd,
        "length": length,
        "entropy_bits": round(entropy, 1),
        "charset": {"upper": use_upper, "lower": use_lower, "digits": use_digits, "symbols": use_symbols},
    }


# ═══════════════════════════════════════════════
# 2. 密码强度评估
# ═══════════════════════════════════════════════
_COMMON_PATTERNS = [
    "123456", "password", "123456789", "12345678", "12345",
    "qwerty", "abc123", "111111", "123123", "admin",
    "letmein", "welcome", "monkey", "dragon", "master",
    "1234", "1234567890", "1234567", "football", "iloveyou",
    "trustno1", "sunshine", "princess", "shadow", "batman",
]

_KEYBOARD_WALKS = [
    "qwertyuiop", "asdfghjkl", "zxcvbnm",
    "qwertzuiop", "asdfghjklö", "yxcvbnm",
    "azertyuiop", "qsdfghjklm", "wxcvbn",
    "poiuytrewq", "lkjhgfdsa", "mnbvcxz",
]

def do_entropy(params: dict) -> dict:
    pwd = params.get("password", "")
    if not pwd:
        return {"ok": False, "error": "缺少 password 参数"}

    pwd_len = len(pwd)

    # 字符集分析
    has_upper = any(c in string.ascii_uppercase for c in pwd)
    has_lower = any(c in string.ascii_lowercase for c in pwd)
    has_digit = any(c in string.digits for c in pwd)
    has_symbol = any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?/~`\"'\\" for c in pwd)
    has_unicode = any(ord(c) > 127 for c in pwd)

    charset_size = 0
    if has_lower: charset_size += 26
    if has_upper: charset_size += 26
    if has_digit: charset_size += 10
    if has_symbol: charset_size += 32
    if has_unicode: charset_size += 100

    # 基础熵
    if charset_size == 0:
        raw_entropy = 0
    else:
        raw_entropy = pwd_len * math.log2(charset_size)

    # 扣分：常见密码
    is_common = pwd.lower() in _COMMON_PATTERNS
    if is_common:
        raw_entropy = min(raw_entropy, 10)

    # 扣分：键盘行走
    pwd_lower = pwd.lower()
    is_keyboard_walk = any(walk in pwd_lower or walk in pwd_lower[::-1]
                           for walk in _KEYBOARD_WALKS if len(walk) >= 4)
    if is_keyboard_walk:
        raw_entropy = max(raw_entropy * 0.3, 15)

    # 扣分：重复字符过多
    unique_ratio = len(set(pwd)) / pwd_len if pwd_len > 0 else 0
    if unique_ratio < 0.4 and pwd_len >= 8:
        raw_entropy *= 0.5

    # 扣分：全是同类型
    types_count = sum([has_upper, has_lower, has_digit, has_symbol])
    if types_count == 1 and pwd_len >= 6:
        raw_entropy *= 0.6

    final_entropy = round(raw_entropy, 1)

    if final_entropy < 28:
        strength = "very_weak"
        label = "极弱"
        color = "#FF0000"
    elif final_entropy < 36:
        strength = "weak"
        label = "弱"
        color = "#FF6600"
    elif final_entropy < 60:
        strength = "moderate"
        label = "中等"
        color = "#FFCC00"
    elif final_entropy < 80:
        strength = "strong"
        label = "强"
        color = "#66CC00"
    else:
        strength = "very_strong"
        label = "非常强"
        color = "#00CC00"

    issues = []
    if is_common:       issues.append("常见密码")
    if is_keyboard_walk: issues.append("键盘行走模式")
    if pwd_len < 8:     issues.append("长度不足 (建议≥8)")
    if types_count < 3:  issues.append("字符类型偏少 (建议≥3种)")
    if unique_ratio < 0.4 and pwd_len >= 8: issues.append("重复字符过多")

    return {
        "ok": True,
        "entropy_bits": final_entropy,
        "strength": strength,
        "label": label,
        "color": color,
        "length": pwd_len,
        "charset": {
            "upper": has_upper, "lower": has_lower,
            "digits": has_digit, "symbols": has_symbol, "unicode": has_unicode,
        },
        "unique_ratio": round(unique_ratio, 2),
        "issues": issues,
    }


# ═══════════════════════════════════════════════
# 3. JWT 解码（不验证签名，仅解析 payload）
# ═══════════════════════════════════════════════
def _b64url_decode(data: str) -> bytes:
    """将 base64url 补齐为标准 base64 后解码"""
    data = data.replace('-', '+').replace('_', '/')
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return base64.b64decode(data)

def do_jwt_decode(params: dict) -> dict:
    token = params.get("token", "")
    if not token:
        return {"ok": False, "error": "缺少 token 参数"}

    parts = token.split(".")
    if len(parts) < 2:
        return {"ok": False, "error": "无效的 JWT 格式，期望 header.payload[.signature]"}

    result = {}
    # 解码 header
    try:
        header_json = _b64url_decode(parts[0]).decode("utf-8")
        result["header"] = json.loads(header_json)
    except Exception as e:
        result["header"] = None
        result["header_error"] = str(e)

    # 解码 payload
    try:
        payload_json = _b64url_decode(parts[1]).decode("utf-8")
        result["payload"] = json.loads(payload_json)
    except Exception as e:
        result["payload"] = None
        result["payload_error"] = str(e)

    result["ok"] = result["payload"] is not None
    result["has_signature"] = len(parts) >= 3
    result["parts_count"] = len(parts)

    # 解析时间戳为可读格式
    if result.get("payload"):
        from datetime import datetime, timezone
        for field in ("iat", "exp", "nbf"):
            if field in result["payload"] and isinstance(result["payload"][field], (int, float)):
                try:
                    dt = datetime.fromtimestamp(result["payload"][field], tz=timezone.utc)
                    result["payload"][f"{field}_readable"] = dt.isoformat()
                except Exception:
                    pass

    return result


# ═══════════════════════════════════════════════
# 4. 文件哈希 (MD5 / SHA256)
# ═══════════════════════════════════════════════
_HASH_ALGOS = {
    "md5":    hashlib.md5,
    "sha1":   hashlib.sha1,
    "sha256": hashlib.sha256,
    "sha512": hashlib.sha512,
}

def do_hash_file(params: dict) -> dict:
    algo = params.get("algo", "sha256").lower()
    path = params.get("file", params.get("path", ""))

    if algo not in _HASH_ALGOS:
        return {"ok": False, "error": f"不支持的算法: {algo}，可用: {list(_HASH_ALGOS.keys())}"}
    if not path:
        return {"ok": False, "error": "缺少 file 或 path 参数"}

    try:
        h = _HASH_ALGOS[algo]()
        file_size = 0
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
                file_size += len(chunk)
        return {
            "ok": True,
            "hash": h.hexdigest(),
            "algo": algo,
            "file": path,
            "size_bytes": file_size,
            "size_kb": round(file_size / 1024, 1),
        }
    except FileNotFoundError:
        return {"ok": False, "error": f"文件不存在: {path}"}
    except PermissionError:
        return {"ok": False, "error": f"无权限读取: {path}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════
# 5. 安全随机数/字符串生成
# ═══════════════════════════════════════════════
def do_random(params: dict) -> dict:
    action = params.get("action", "string").lower()

    if action == "number" or action == "int":
        lo = params.get("min", 0)
        hi = params.get("max", 2**31 - 1)
        if lo > hi:
            lo, hi = hi, lo
        val = secrets.randbelow(hi - lo + 1) + lo
        return {"ok": True, "value": val, "min": lo, "max": hi}

    elif action == "float":
        lo = params.get("min", 0.0)
        hi = params.get("max", 1.0)
        val = lo + secrets.SystemRandom().random() * (hi - lo)
        return {"ok": True, "value": round(val, 6), "min": lo, "max": hi}

    elif action == "bytes":
        count = max(1, min(1024, params.get("length", 32)))
        raw = secrets.token_bytes(count)
        representation = params.get("format", "hex")
        if representation == "base64":
            val = base64.b64encode(raw).decode("ascii")
        else:
            val = raw.hex()
        return {"ok": True, "value": val, "length": count, "format": representation}

    elif action == "choice":
        items = params.get("items", [])
        if not items:
            return {"ok": False, "error": "缺少 items 列表"}
        return {"ok": True, "value": secrets.choice(items), "from_count": len(items)}

    elif action == "sample":
        items = params.get("items", [])
        k = params.get("count", 1)
        if not items:
            return {"ok": False, "error": "缺少 items 列表"}
        if k > len(items):
            k = len(items)
        result = secrets.SystemRandom().sample(items, k)
        return {"ok": True, "value": result, "count": k, "from_count": len(items)}

    elif action == "uuid":
        import uuid
        return {"ok": True, "value": str(uuid.uuid4())}

    elif action == "token_hex":
        nbytes = max(4, min(128, params.get("length", 32)))
        return {"ok": True, "value": secrets.token_hex(nbytes), "bytes": nbytes}

    elif action == "token_urlsafe":
        nbytes = max(4, min(128, params.get("length", 32)))
        return {"ok": True, "value": secrets.token_urlsafe(nbytes), "bytes": nbytes}

    else:
        # 默认: 生成安全随机字符串
        length = max(4, min(256, params.get("length", 32)))
        pool = string.ascii_letters + string.digits
        val = ''.join(secrets.choice(pool) for _ in range(length))
        return {"ok": True, "value": val, "length": length, "charset": "alphanumeric"}


# ═══════════════════════════════════════════════
# 6. 多编码转换 (hex / rot13 / morse)
# ═══════════════════════════════════════════════
_MORSE_TABLE = {
    'A': '.-',    'B': '-...',  'C': '-.-.',  'D': '-..',
    'E': '.',     'F': '..-.',  'G': '--.',   'H': '....',
    'I': '..',    'J': '.---',  'K': '-.-',   'L': '.-..',
    'M': '--',    'N': '-.',    'O': '---',   'P': '.--.',
    'Q': '--.-',  'R': '.-.',   'S': '...',   'T': '-',
    'U': '..-',   'V': '...-',  'W': '.--',   'X': '-..-',
    'Y': '-.--',  'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--',
    '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.',
    '.': '.-.-.-', ',': '--..--', '?': '..--..', "'": '.----.',
    '!': '-.-.--', '/': '-..-.',  '(': '-.--.',  ')': '-.--.-',
    '&': '.-...',  ':': '---...', ';': '-.-.-.',  '=': '-...-',
    '+': '.-.-.',  '-': '-....-', '_': '..--.-',  '"': '.-..-.',
    '$': '...-..-','@': '.--.-.',
    ' ': '/',
}
_MORSE_REVERSE = {v: k for k, v in _MORSE_TABLE.items()}

def do_encode(params: dict) -> dict:
    action = params.get("action", "hex_encode").lower()
    text = params.get("text", "")

    if not text and action not in ("hex_decode",):
        return {"ok": False, "error": "缺少 text 参数"}

    if action == "hex_encode":
        result = text.encode("utf-8").hex()
        return {"ok": True, "result": result, "action": action}

    elif action == "hex_decode":
        try:
            result = bytes.fromhex(text).decode("utf-8")
        except Exception as e:
            return {"ok": False, "error": f"hex 解码失败: {e}"}
        return {"ok": True, "result": result, "action": action}

    elif action == "rot13":
        def _rot13_char(c):
            if 'a' <= c <= 'z':
                return chr((ord(c) - ord('a') + 13) % 26 + ord('a'))
            if 'A' <= c <= 'Z':
                return chr((ord(c) - ord('A') + 13) % 26 + ord('A'))
            return c
        result = ''.join(_rot13_char(c) for c in text)
        return {"ok": True, "result": result, "action": action}

    elif action == "morse_encode":
        upper = text.upper()
        result = ' '.join(
            _MORSE_TABLE.get(c, '?') for c in upper
        )
        return {"ok": True, "result": result, "action": action}

    elif action == "morse_decode":
        tokens = text.strip().split()
        decoded = []
        for token in tokens:
            if token == '/':
                decoded.append(' ')
            else:
                decoded.append(_MORSE_REVERSE.get(token, '?'))
        result = ''.join(decoded)
        return {"ok": True, "result": result, "action": action}

    elif action == "base64_encode":
        result = base64.b64encode(text.encode("utf-8")).decode("ascii")
        return {"ok": True, "result": result, "action": action}

    elif action == "base64_decode":
        try:
            result = base64.b64decode(text).decode("utf-8")
        except Exception as e:
            return {"ok": False, "error": f"base64 解码失败: {e}"}
        return {"ok": True, "result": result, "action": action}

    elif action == "url_encode":
        import urllib.parse
        result = urllib.parse.quote(text, safe="")
        return {"ok": True, "result": result, "action": action}

    elif action == "url_decode":
        import urllib.parse
        result = urllib.parse.unquote(text)
        return {"ok": True, "result": result, "action": action}

    else:
        return {"ok": False, "error": f"未知编码操作: {action}",
                "available": ["hex_encode", "hex_decode", "rot13",
                              "morse_encode", "morse_decode",
                              "base64_encode", "base64_decode",
                              "url_encode", "url_decode"]}


# ═══════════════════════════════════════════════
# Handler 注册
# ═══════════════════════════════════════════════
handlers = {
    "password":   do_password,
    "entropy":    do_entropy,
    "jwt_decode": do_jwt_decode,
    "hash_file":  do_hash_file,
    "random":     do_random,
    "encode":     do_encode,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else ""
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except Exception:
            pass
    handler = handlers.get(action)
    if handler:
        result = handler(params)
    else:
        result = {
            "ok": False,
            "error": f"未知工具: {action}",
            "available": list(handlers.keys()),
        }
    print(json.dumps(result, ensure_ascii=False, default=str))
