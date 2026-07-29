# 开发者：自由的风
'''toolbox/run.py — 多宝盒工具集：JSON/Base64/URL/哈希/时间戳/UUID/二维码/差异对比/正则测试'''
import sys, json, os, base64, hashlib, uuid, datetime, urllib.parse, difflib, re

# ─── 1. JSON 格式化 / 压缩 / 验证 ───
def do_json_fmt(params: dict) -> dict:
    action = params.get("action", "format")
    text = params.get("text", "")
    indent = params.get("indent", 2)
    result = {"ok": True, "action": action}
    try:
        parsed = json.loads(text)
        if action == "format":
            result["result"] = json.dumps(parsed, ensure_ascii=False, indent=indent)
        elif action == "compact":
            result["result"] = json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
        elif action == "validate":
            result["result"] = "有效 JSON"
            result["parsed_type"] = type(parsed).__name__
            if isinstance(parsed, dict):
                result["keys"] = list(parsed.keys())
            elif isinstance(parsed, list):
                result["length"] = len(parsed)
        else:
            result["ok"] = False
            result["error"] = f"未知 action: {action} (可选: format/compact/validate)"
    except json.JSONDecodeError as e:
        result["ok"] = False
        result["error"] = f"JSON 解析失败: {str(e)}"
    return result


# ─── 2. Base64 编解码 ───
def do_base64(params: dict) -> dict:
    action = params.get("action", "encode")
    text = params.get("text", "")
    result = {"ok": True, "action": action}
    try:
        if action == "encode":
            result["result"] = base64.b64encode(text.encode("utf-8")).decode("utf-8")
        elif action == "decode":
            result["result"] = base64.b64decode(text.encode("utf-8")).decode("utf-8", errors="replace")
        else:
            result["ok"] = False
            result["error"] = f"未知 action: {action} (可选: encode/decode)"
    except Exception as e:
        result["ok"] = False
        result["error"] = f"Base64 操作失败: {str(e)}"
    return result


# ─── 3. URL 编解码 ───
def do_url(params: dict) -> dict:
    action = params.get("action", "encode")
    text = params.get("text", "")
    result = {"ok": True, "action": action}
    try:
        if action == "encode":
            result["result"] = urllib.parse.quote(text, safe="")
        elif action == "decode":
            result["result"] = urllib.parse.unquote(text)
        elif action == "encode_component":
            result["result"] = urllib.parse.quote(text, safe="")
        elif action == "decode_component":
            result["result"] = urllib.parse.unquote(text)
        elif action == "parse":
            parsed = urllib.parse.urlparse(text)
            result["result"] = {
                "scheme": parsed.scheme,
                "netloc": parsed.netloc,
                "path": parsed.path,
                "params": parsed.params,
                "query": parsed.query,
                "fragment": parsed.fragment,
            }
            if parsed.query:
                result["result"]["query_params"] = dict(urllib.parse.parse_qsl(parsed.query))
        else:
            result["ok"] = False
            result["error"] = f"未知 action: {action} (可选: encode/decode/parse)"
    except Exception as e:
        result["ok"] = False
        result["error"] = f"URL 操作失败: {str(e)}"
    return result


# ─── 4. 哈希 (MD5/SHA1/SHA256) ───
def do_hash(params: dict) -> dict:
    algo = params.get("algo", "sha256").lower()
    text = params.get("text", "")
    result = {"ok": True, "algo": algo}
    try:
        algos = {"md5": hashlib.md5, "sha1": hashlib.sha1, "sha256": hashlib.sha256}
        if algo not in algos:
            result["ok"] = False
            result["error"] = f"不支持的算法: {algo} (可选: md5/sha1/sha256)"
        else:
            h = algos[algo](text.encode("utf-8"))
            result["result"] = h.hexdigest()
    except Exception as e:
        result["ok"] = False
        result["error"] = f"哈希计算失败: {str(e)}"
    return result


# ─── 5. 时间戳 ↔ 日期 ───
def do_timestamp(params: dict) -> dict:
    action = params.get("action", "to_date")
    result = {"ok": True, "action": action}
    try:
        if action == "to_date":
            ts = params.get("ts", 0)
            # 自动判断秒/毫秒
            if ts > 1e12:
                ts = ts / 1000.0
            dt = datetime.datetime.fromtimestamp(ts)
            result["result"] = dt.strftime("%Y-%m-%d %H:%M:%S")
            result["iso"] = dt.isoformat()
        elif action == "from_date":
            date_str = params.get("date", "")
            fmt = params.get("fmt", "%Y-%m-%d %H:%M:%S")
            dt = datetime.datetime.strptime(date_str, fmt)
            result["result"] = int(dt.timestamp())
            result["result_ms"] = int(dt.timestamp() * 1000)
        elif action == "now":
            now = datetime.datetime.now()
            result["result"] = int(now.timestamp())
            result["result_ms"] = int(now.timestamp() * 1000)
            result["datetime"] = now.strftime("%Y-%m-%d %H:%M:%S")
            result["iso"] = now.isoformat()
        else:
            result["ok"] = False
            result["error"] = f"未知 action: {action} (可选: to_date/from_date/now)"
    except Exception as e:
        result["ok"] = False
        result["error"] = f"时间戳转换失败: {str(e)}"
    return result


# ─── 6. UUID 生成 ───
def do_uuid(params: dict) -> dict:
    count = params.get("count", 1)
    result = {"ok": True}
    try:
        if count <= 1:
            result["result"] = str(uuid.uuid4())
        else:
            result["result"] = [str(uuid.uuid4()) for _ in range(min(count, 100))]
    except Exception as e:
        result["ok"] = False
        result["error"] = f"UUID 生成失败: {str(e)}"
    return result


# ─── 7. 二维码生成 ───
def do_qrcode(params: dict) -> dict:
    text = params.get("text", "")
    result = {"ok": True}
    try:
        import qrcode
        import io
        qr = qrcode.QRCode(
            version=params.get("version") or None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=params.get("box_size", 10),
            border=params.get("border", 4),
        )
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        result["result"] = base64.b64encode(buf.getvalue()).decode("utf-8")
        result["mime"] = "image/png"
        result["text"] = text
    except ImportError:
        result["ok"] = False
        result["error"] = "缺少 qrcode 库，请执行: pip install qrcode[pil] pillow"
    except Exception as e:
        result["ok"] = False
        result["error"] = f"二维码生成失败: {str(e)}"
    return result


# ─── 8. 文本差异对比 ───
def do_diff(params: dict) -> dict:
    text_a = params.get("text_a", "")
    text_b = params.get("text_b", "")
    fmt = params.get("format", "unified")
    result = {"ok": True, "format": fmt}
    try:
        lines_a = text_a.splitlines(keepends=True)
        lines_b = text_b.splitlines(keepends=True)
        if fmt == "unified":
            diff = difflib.unified_diff(lines_a, lines_b, fromfile="文本A", tofile="文本B")
            result["result"] = "".join(diff)
        elif fmt == "ndiff":
            diff = difflib.ndiff(lines_a, lines_b)
            result["result"] = "".join(diff)
        elif fmt == "html":
            d = difflib.HtmlDiff()
            result["result"] = d.make_table(lines_a, lines_b, fromdesc="文本A", todesc="文本B", context=True, numlines=3)
        elif fmt == "inline":
            # 逐行对比摘要
            sm = difflib.SequenceMatcher(None, text_a, text_b)
            result["similarity"] = round(sm.ratio() * 100, 2)
            result["result"] = f"相似度: {result['similarity']}%"
        else:
            result["ok"] = False
            result["error"] = f"未知 format: {fmt} (可选: unified/ndiff/html/inline)"
    except Exception as e:
        result["ok"] = False
        result["error"] = f"差异对比失败: {str(e)}"
    return result


# ─── 9. 正则测试器 ───
def do_regex(params: dict) -> dict:
    action = params.get("action", "match")
    pattern = params.get("pattern", "")
    text = params.get("text", "")
    flags = params.get("flags", "")
    result = {"ok": True, "action": action, "pattern": pattern}
    try:
        flag_val = 0
        for f in flags:
            if f == "i": flag_val |= re.IGNORECASE
            elif f == "m": flag_val |= re.MULTILINE
            elif f == "s": flag_val |= re.DOTALL
            elif f == "x": flag_val |= re.VERBOSE
        compiled = re.compile(pattern, flag_val)
        if action == "match":
            matches = compiled.findall(text)
            result["result"] = matches
            result["count"] = len(matches)
        elif action == "replace":
            replacement = params.get("replacement", "")
            result["result"] = compiled.sub(replacement, text)
        elif action == "split":
            maxsplit = params.get("maxsplit", 0)
            result["result"] = compiled.split(text, maxsplit=maxsplit)
        elif action == "search":
            m = compiled.search(text)
            if m:
                result["result"] = {
                    "match": m.group(),
                    "span": (m.start(), m.end()),
                    "groups": m.groups(),
                }
            else:
                result["result"] = None
        elif action == "test":
            result["result"] = bool(compiled.search(text))
        else:
            result["ok"] = False
            result["error"] = f"未知 action: {action} (可选: match/replace/split/search/test)"
    except re.error as e:
        result["ok"] = False
        result["error"] = f"正则表达式错误: {str(e)}"
    except Exception as e:
        result["ok"] = False
        result["error"] = f"正则操作失败: {str(e)}"
    return result


# ─── Handler 注册 ───
handlers = {
    "json_fmt":  do_json_fmt,
    "base64":    do_base64,
    "url":       do_url,
    "hash":      do_hash,
    "timestamp": do_timestamp,
    "uuid":      do_uuid,
    "qrcode":    do_qrcode,
    "diff":      do_diff,
    "regex":     do_regex,
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
