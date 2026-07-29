# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""netter/run.py — 网络工具集：HTTP请求/DNS查询/TCP连通性/WHOIS/SSL证书/URL缩短"""
import sys, json, os, socket, ssl, struct, random, time, urllib.request, urllib.error, urllib.parse


# ═══════════════════════════════════════════
# 1. HTTP 请求测试
# ═══════════════════════════════════════════
def do_http(params: dict) -> dict:
    url = params.get("url", "")
    if not url:
        return {"ok": False, "error": "url 必填"}

    method = params.get("method", "GET").upper()
    headers = params.get("headers", {}) or {}
    body = params.get("body", "")
    timeout = params.get("timeout", 15)

    try:
        if isinstance(body, str):
            body = body.encode("utf-8")

        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        t0 = time.perf_counter()

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
            resp_body = resp.read().decode("utf-8", errors="replace")
            return {
                "ok": True,
                "result": {
                    "status": resp.status,
                    "reason": resp.reason,
                    "headers": dict(resp.headers),
                    "body": resp_body[:8192],
                    "elapsed_ms": elapsed_ms,
                },
            }
    except urllib.error.HTTPError as e:
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        err_body = ""
        try:
            err_body = e.read().decode("utf-8", errors="replace")[:2048]
        except Exception:
            pass
        return {
            "ok": False,
            "result": {
                "status": e.code,
                "reason": e.reason,
                "headers": dict(e.headers) if e.headers else {},
                "body": err_body,
                "elapsed_ms": elapsed_ms,
            },
            "error": f"HTTP {e.code} {e.reason}",
        }
    except urllib.error.URLError as e:
        return {"ok": False, "error": f"连接失败: {e.reason}"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


# ═══════════════════════════════════════════
# 2. DNS 查询 (纯标准库实现)
# ═══════════════════════════════════════════
_DNS_TYPES = {"A": 1, "NS": 2, "CNAME": 5, "SOA": 6, "MX": 15, "TXT": 16, "AAAA": 28}
_DNS_TYPE_NAMES = {v: k for k, v in _DNS_TYPES.items()}


def _build_dns_query(domain: str, qtype: int) -> bytes:
    """构建DNS查询报文"""
    tid = random.randint(0, 65535)
    flags = 0x0100  # 标准递归查询
    header = struct.pack("!HHHHHH", tid, flags, 1, 0, 0, 0)

    # 编码域名 (label格式)
    labels = domain.rstrip(".").split(".")
    question = b""
    for label in labels:
        lb = label.encode("ascii", errors="ignore")
        question += struct.pack("B", len(lb)) + lb
    question += b"\x00"  # 终止
    question += struct.pack("!HH", qtype, 1)  # type + class IN

    return header + question


def _parse_dns_name(data: bytes, offset: int) -> tuple[str, int]:
    """解析DNS压缩域名, 返回 (name, next_offset)"""
    parts = []
    jumped = False
    original_offset = offset
    max_loop = 32

    for _ in range(max_loop):
        if offset >= len(data):
            break
        length = data[offset]
        if length == 0:
            offset += 1
            break
        if (length & 0xC0) == 0xC0:
            # 压缩指针
            if offset + 1 >= len(data):
                break
            ptr = ((length & 0x3F) << 8) | data[offset + 1]
            if not jumped:
                original_offset = offset + 2
            jumped = True
            offset = ptr
            continue
        offset += 1
        if offset + length > len(data):
            break
        parts.append(data[offset : offset + length].decode("ascii", errors="replace"))
        offset += length

    if not jumped:
        original_offset = offset
    return ".".join(parts), original_offset


def _parse_dns_response(data: bytes) -> list[dict]:
    """解析DNS响应, 返回记录列表"""
    if len(data) < 12:
        return []

    tid, flags, qdcount, ancount, nscount, arcount = struct.unpack("!HHHHHH", data[:12])
    rcode = flags & 0xF
    if rcode != 0:
        rcode_names = {1: "格式错误", 2: "服务器失败", 3: "NXDOMAIN", 4: "未实现", 5: "拒绝"}
        return [{"error": rcode_names.get(rcode, f"rcode={rcode}")}]

    offset = 12

    # 跳过问题区
    for _ in range(qdcount):
        _, offset = _parse_dns_name(data, offset)
        offset += 4  # type + class

    total_rr = ancount + nscount + arcount
    records = []

    for _ in range(total_rr):
        if offset + 10 > len(data):
            break
        name, offset = _parse_dns_name(data, offset)
        if offset + 10 > len(data):
            break
        rtype, rclass, ttl, rdlength = struct.unpack("!HHIH", data[offset : offset + 10])
        offset += 10
        if offset + rdlength > len(data):
            break

        rdata_raw = data[offset : offset + rdlength]
        offset += rdlength

        type_name = _DNS_TYPE_NAMES.get(rtype, f"TYPE{rtype}")

        if rtype == 1:  # A
            value = socket.inet_ntop(socket.AF_INET, rdata_raw)
        elif rtype == 28:  # AAAA
            value = socket.inet_ntop(socket.AF_INET6, rdata_raw)
        elif rtype in (2, 5, 12):  # NS, CNAME, PTR
            value, _ = _parse_dns_name(data, offset - rdlength)
        elif rtype == 15:  # MX
            if len(rdata_raw) >= 3:
                pref = struct.unpack("!H", rdata_raw[:2])[0]
                mx_name, _ = _parse_dns_name(data, offset - rdlength + 2)
                value = f"{pref} {mx_name}"
            else:
                value = "<invalid>"
        elif rtype == 16:  # TXT
            txts = []
            pos = 0
            while pos < len(rdata_raw):
                txt_len = rdata_raw[pos]
                pos += 1
                if pos + txt_len > len(rdata_raw):
                    break
                txts.append(rdata_raw[pos : pos + txt_len].decode("utf-8", errors="replace"))
                pos += txt_len
            value = " ".join(txts)
        elif rtype == 6:  # SOA
            mname, pos = _parse_dns_name(data, offset - rdlength)
            rname, pos2 = _parse_dns_name(data, pos)
            if pos2 - (offset - rdlength) + 20 <= rdlength:
                soa = struct.unpack("!IIIII", data[pos2 : pos2 + 20])
                value = f"{mname} {rname} serial={soa[0]} refresh={soa[1]} retry={soa[2]} expire={soa[3]} minimum={soa[4]}"
            else:
                value = f"{mname} {rname}"
        else:
            value = rdata_raw.hex()

        records.append({"name": name, "type": type_name, "ttl": ttl, "value": value})

    return records


def do_dns(params: dict) -> dict:
    domain = params.get("domain", "")
    if not domain:
        return {"ok": False, "error": "domain 必填"}

    rtype = params.get("rtype", "A").upper()
    qtype = _DNS_TYPES.get(rtype)
    if qtype is None:
        return {"ok": False, "error": f"不支持的记录类型: {rtype}", "supported": list(_DNS_TYPES.keys())}

    server = params.get("server", "8.8.8.8")
    timeout = params.get("timeout", 5)

    try:
        query = _build_dns_query(domain, qtype)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        t0 = time.perf_counter()
        sock.sendto(query, (server, 53))
        data, _ = sock.recvfrom(4096)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        sock.close()

        records = _parse_dns_response(data)

        if not records:
            return {"ok": True, "result": {"domain": domain, "type": rtype, "records": [], "elapsed_ms": elapsed_ms}}

        # 如果有 error key 说明是rcode错误
        if "error" in records[0]:
            err = records[0]["error"]
            return {"ok": True, "result": {"domain": domain, "type": rtype, "records": [], "error": err, "elapsed_ms": elapsed_ms}}

        return {"ok": True, "result": {"domain": domain, "type": rtype, "records": records, "elapsed_ms": elapsed_ms}}
    except socket.timeout:
        return {"ok": False, "error": f"DNS查询超时({timeout}s)"}
    except socket.gaierror as e:
        return {"ok": False, "error": f"地址解析失败: {e}"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


# ═══════════════════════════════════════════
# 3. TCP Ping (端口连通性)
# ═══════════════════════════════════════════
def do_ping(params: dict) -> dict:
    host = params.get("host", "")
    port = params.get("port", 80)
    timeout = params.get("timeout", 5)

    if not host:
        return {"ok": False, "error": "host 必填"}

    try:
        port = int(port)
        if port < 1 or port > 65535:
            return {"ok": False, "error": "端口范围 1-65535"}

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        t0 = time.perf_counter()
        sock.connect((host, port))
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        sock.close()
        return {"ok": True, "result": {"host": host, "port": port, "reachable": True, "elapsed_ms": elapsed_ms}}
    except socket.timeout:
        return {"ok": True, "result": {"host": host, "port": port, "reachable": False, "error": f"超时({timeout}s)"}}
    except socket.gaierror:
        return {"ok": True, "result": {"host": host, "port": port, "reachable": False, "error": "域名解析失败"}}
    except ConnectionRefusedError:
        return {"ok": True, "result": {"host": host, "port": port, "reachable": False, "error": "连接被拒绝"}}
    except OSError as e:
        return {"ok": True, "result": {"host": host, "port": port, "reachable": False, "error": str(e)[:100]}}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


# ═══════════════════════════════════════════
# 4. WHOIS 查询
# ═══════════════════════════════════════════
_WHOIS_SERVERS = {
    "com": "whois.verisign-grs.com",
    "net": "whois.verisign-grs.com",
    "org": "whois.pir.org",
    "cn": "whois.cnnic.cn",
    "io": "whois.nic.io",
    "cc": "whois.nic.cc",
    "me": "whois.nic.me",
    "co": "whois.nic.co",
    "tv": "whois.nic.tv",
    "info": "whois.afilias.net",
    "biz": "whois.nic.biz",
    "mobi": "whois.nic.mobi",
    "dev": "whois.nic.google",
    "app": "whois.nic.google",
    "ai": "whois.nic.ai",
    "xyz": "whois.nic.xyz",
    "top": "whois.nic.top",
    "tk": "whois.dot.tk",
    "ml": "whois.dot.ml",
    "ga": "whois.dot.ga",
    "cf": "whois.dot.cf",
}


def _whois_query(server: str, domain: str, timeout: int = 10) -> str:
    """向指定WHOIS服务器查询"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect((server, 43))
    sock.sendall(f"{domain}\r\n".encode())
    data = b""
    while True:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
        except socket.timeout:
            break
    sock.close()
    return data.decode("utf-8", errors="replace").strip()


def do_whois(params: dict) -> dict:
    domain = params.get("domain", "")
    if not domain:
        return {"ok": False, "error": "domain 必填"}

    domain = domain.lower().strip()
    timeout = params.get("timeout", 10)

    try:
        # 提取TLD
        parts = domain.split(".")
        if len(parts) < 2:
            return {"ok": False, "error": "无效域名"}

        tld = parts[-1]
        whois_server = _WHOIS_SERVERS.get(tld)

        if whois_server:
            # 直接查询已知服务器
            raw = _whois_query(whois_server, domain, timeout)
            return {"ok": True, "result": {"domain": domain, "raw": raw}}
        else:
            # 通过IANA查询whois服务器
            iana_raw = _whois_query("whois.iana.org", domain, timeout)

            # 从IANA响应中提取whois服务器
            whois_server = None
            for line in iana_raw.split("\n"):
                line_lower = line.lower().strip()
                if line_lower.startswith("whois:"):
                    whois_server = line.split(":", 1)[1].strip()
                    break
                elif line_lower.startswith("refer:"):
                    whois_server = line.split(":", 1)[1].strip()
                    break

            if not whois_server:
                # 返回IANA结果
                return {"ok": True, "result": {"domain": domain, "raw": iana_raw}}

            raw = _whois_query(whois_server, domain, timeout)
            return {"ok": True, "result": {"domain": domain, "whois_server": whois_server, "raw": raw}}

    except socket.timeout:
        return {"ok": False, "error": f"WHOIS查询超时({timeout}s)"}
    except socket.gaierror:
        return {"ok": False, "error": "WHOIS服务器解析失败"}
    except ConnectionRefusedError:
        return {"ok": False, "error": "WHOIS服务器拒绝连接"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


# ═══════════════════════════════════════════
# 5. SSL 证书信息
# ═══════════════════════════════════════════
def do_ssl(params: dict) -> dict:
    hostname = params.get("hostname", "")
    port = params.get("port", 443)

    if not hostname:
        return {"ok": False, "error": "hostname 必填"}

    try:
        port = int(port)
        if port < 1 or port > 65535:
            return {"ok": False, "error": "端口范围 1-65535"}
    except (ValueError, TypeError):
        return {"ok": False, "error": "端口必须为数字"}

    timeout = params.get("timeout", 10)

    try:
        context = ssl.create_default_context()
        # 允许不验证证书以获取证书信息
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        sock = socket.create_connection((hostname, port), timeout=timeout)
        t0 = time.perf_counter()

        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            connect_ms = round((time.perf_counter() - t0) * 1000, 1)
            cert = ssock.getpeercert(binary_form=False)

            if not cert:
                return {"ok": False, "error": "未获取到证书"}

            # 提取证书信息
            subject = dict(x[0] for x in cert.get("subject", []))
            issuer = dict(x[0] for x in cert.get("issuer", []))
            not_before = cert.get("notBefore", "")
            not_after = cert.get("notAfter", "")
            san = cert.get("subjectAltName", [])
            version = cert.get("version", 0)
            serial = cert.get("serialNumber", "")

            # 检查过期
            now = time.time()
            from datetime import datetime
            try:
                # notAfter 格式: "Nov 30 12:00:00 2025 GMT"
                expires = datetime.strptime(not_after.replace(" GMT", ""), "%b %d %H:%M:%S %Y")
                days_left = (expires - datetime.now()).days
            except Exception:
                try:
                    # ISO格式
                    expires = datetime.fromisoformat(not_after.replace("Z", "+00:00"))
                    days_left = (expires - datetime.now()).days
                except Exception:
                    days_left = None
                    expires = None

            return {
                "ok": True,
                "result": {
                    "hostname": hostname,
                    "port": port,
                    "subject": {k: v for k, v in subject.items() if k != "countryName"},
                    "issuer": {k: v for k, v in issuer.items() if k != "countryName"},
                    "valid_from": not_before,
                    "valid_until": not_after,
                    "days_left": days_left,
                    "san": [s[1] for s in san if s[0] == "DNS"],
                    "version": version,
                    "serial_number": serial,
                    "connect_ms": connect_ms,
                },
            }
    except socket.timeout:
        return {"ok": False, "error": f"SSL连接超时({timeout}s)"}
    except ssl.SSLCertVerificationError as e:
        return {"ok": False, "error": f"证书验证失败: {e}"}
    except ssl.SSLError as e:
        return {"ok": False, "error": f"SSL错误: {e}"}
    except socket.gaierror:
        return {"ok": False, "error": "域名解析失败"}
    except ConnectionRefusedError:
        return {"ok": False, "error": "连接被拒绝"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


# ═══════════════════════════════════════════
# 6. URL 缩短
# ═══════════════════════════════════════════
_SHORTEN_SERVICES = {
    "tinyurl": {
        "name": "TinyURL",
        "url": "https://tinyurl.com/api-create.php",
        "params": {"url": "{url}"},
    },
    "isgd": {
        "name": "is.gd",
        "url": "https://is.gd/create.php",
        "params": {"format": "simple", "url": "{url}"},
    },
    "vgd": {
        "name": "v.gd",
        "url": "https://v.gd/create.php",
        "params": {"format": "simple", "url": "{url}"},
    },
}


def do_shorten(params: dict) -> dict:
    url = params.get("url", "")
    if not url:
        return {"ok": False, "error": "url 必填"}

    service = params.get("service", "tinyurl")
    svc = _SHORTEN_SERVICES.get(service)
    if not svc:
        return {"ok": False, "error": f"不支持的服务: {service}", "supported": list(_SHORTEN_SERVICES.keys())}

    timeout = params.get("timeout", 10)

    try:
        query = urllib.parse.urlencode(
            {k: v.replace("{url}", url) for k, v in svc["params"].items()}
        )
        full_url = f"{svc['url']}?{query}"

        req = urllib.request.Request(full_url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            short_url = resp.read().decode("utf-8", errors="replace").strip()

        if not short_url or not short_url.startswith("http"):
            return {"ok": False, "error": f"缩短失败，返回: {short_url}"}

        return {"ok": True, "result": {"original": url, "short": short_url, "service": svc["name"]}}
    except urllib.error.URLError as e:
        return {"ok": False, "error": f"API连接失败: {e.reason}"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


# ═══════════════════════════════════════════
# Handler 注册 & 入口
# ═══════════════════════════════════════════
HANDLERS = {
    "http":    do_http,
    "dns":     do_dns,
    "ping":    do_ping,
    "whois":   do_whois,
    "ssl":     do_ssl,
    "shorten": do_shorten,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else ""
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except Exception:
            pass
    handler = HANDLERS.get(action)
    if handler:
        result = handler(params)
    else:
        result = {
            "ok": False,
            "error": f"未知工具: {action}",
            "available": list(HANDLERS.keys()),
        }
    print(json.dumps(result, ensure_ascii=False, default=str))
