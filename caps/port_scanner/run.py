# 开发者：自由的风
"""port_scanner/run.py — TCP/UDP端口探测 + 服务指纹 + 源码层分析
===============================================================
侦察域 core — 不只是"端口是否开放"，而是穿透到服务响应层，
从banner/错误页/headers中提取框架版本、技术栈、潜在薄弱点。
"""
import sys, json, os, socket, ssl, struct, time, concurrent.futures, re

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 知名服务指纹库
SERVICE_FINGERPRINTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 111: "RPC", 135: "MS-RPC", 139: "NetBIOS",
    143: "IMAP", 443: "HTTPS", 445: "SMB", 993: "IMAPS", 995: "POP3S",
    1433: "MSSQL", 1521: "Oracle", 2049: "NFS", 3306: "MySQL",
    3389: "RDP", 5432: "PostgreSQL", 5900: "VNC", 6379: "Redis",
    8080: "HTTP-Alt", 8443: "HTTPS-Alt", 9090: "Web-Alt",
    27017: "MongoDB", 50000: "SAP", 50070: "Hadoop",
}

# 源码层薄弱点特征 — 从服务响应中提取
WEAKNESS_PATTERNS = [
    (r"Apache/([\d.]+)", "Apache {v}", "检查CVE对应版本"),
    (r"nginx/([\d.]+)", "Nginx {v}", "检查CVE对应版本"),
    (r"PHP/([\d.]+)", "PHP {v}", "版本过旧可能远程执行"),
    (r"Server:.*Microsoft-IIS/([\d.]+)", "IIS {v}", "检查HTTP.sys漏洞"),
    (r"X-Powered-By:.*PHP/([\d.]+)", "PHP {v} header泄露", "移除X-Powered-By"),
    (r"X-Drupal-", "Drupal站点", "检查Drupalgeddon"),
    (r"wp-content", "WordPress站点", "检查wp-json/wp-admin暴露"),
    (r"laravel_session", "Laravel框架", "检查debug模式/.env泄露"),
    (r"JSESSIONID", "Java/Tomcat", "检查Struts/Log4j"),
    (r"debug", "Debug模式开启", "严重: 生产环境不应开debug"),
    (r"stacktrace|stack trace", "堆栈泄露", "严重: 异常信息泄露源码路径"),
    (r"SQL syntax.*MySQL", "SQL语法错误泄露", "SQL注入探测点"),
    (r"mysql_fetch|pg_query|sqlsrv_", "数据库函数名泄露", "源码片段泄露"),
    (r"Exception in.*\.(py|java|php):\d+", "异常泄露{file}:{line}", "源码路径+行号泄露"),
]


def _tcp_connect(host, port, timeout=3):
    """TCP连接 + banner抓取 + 源码层分析"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))

        if result != 0:
            sock.close()
            return {"port": port, "open": False}

        banner = ""
        analysis = []

        # 尝试抓取banner
        try:
            if port in (80, 443, 8080, 8443, 9090):
                # HTTP: 发送HEAD请求
                if port in (443, 8443):
                    try:
                        ctx = ssl.create_default_context()
                        ctx.check_hostname = False
                        ctx.verify_mode = ssl.CERT_NONE
                        ssl_sock = ctx.wrap_socket(sock, server_hostname=host)
                        ssl_sock.settimeout(timeout)
                        ssl_sock.send(f"HEAD / HTTP/1.0\r\nHost: {host}\r\n\r\n".encode())
                        banner = ssl_sock.recv(2048).decode("utf-8", errors="replace")
                        ssl_sock.close()
                        sock = None
                    except Exception:
                        pass
                if banner == "":
                    sock.send(f"HEAD / HTTP/1.0\r\nHost: {host}\r\n\r\n".encode())
                    banner = sock.recv(2048).decode("utf-8", errors="replace")
            else:
                banner = sock.recv(1024).decode("utf-8", errors="replace")
        except (socket.timeout, UnicodeDecodeError):
            banner = "(binary/no banner)"

        # 源码层分析
        for pattern, label, suggestion in WEAKNESS_PATTERNS:
            m = re.search(pattern, banner, re.IGNORECASE)
            if m:
                groups = m.groups()
                desc = label
                if groups:
                    desc = label.replace("{v}", groups[0]).replace("{file}", groups[0] if len(groups) > 0 else "")
                analysis.append({"finding": desc, "suggestion": suggestion, "severity": "critical" if "严重" in suggestion else "warning"})

        if sock:
            sock.close()

        service = SERVICE_FINGERPRINTS.get(port, "Unknown")

        return {
            "port": port,
            "open": True,
            "service": service,
            "banner": banner[:300] if banner else "",
            "weakness_analysis": analysis,
            "weakness_count": len(analysis),
        }
    except Exception as e:
        return {"port": port, "open": False, "error": str(e)[:80]}


def do_scan(params):
    """端口扫描 + 源码层穿透分析"""
    host = params.get("host", params.get("target", "127.0.0.1"))
    ports_str = params.get("ports", "22,80,443,3306,5432,6379,8080,8443")
    timeout = params.get("timeout", 3)
    threads = params.get("threads", 20)

    # 解析端口列表
    ports = []
    for part in ports_str.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            ports.extend(range(int(lo), int(hi) + 1))
        else:
            try:
                ports.append(int(part))
            except ValueError:
                pass

    results = []
    open_count = 0
    weakness_total = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(_tcp_connect, host, port, timeout): port for port in ports}
        for f in concurrent.futures.as_completed(futures):
            r = f.result()
            if r.get("open"):
                open_count += 1
                weakness_total += r.get("weakness_count", 0)
            results.append(r)

    results.sort(key=lambda x: (not x.get("open"), x["port"]))

    return {
        "ok": True,
        "cap": "port_scanner",
        "action": "scan",
        "domain": "侦察域",
        "host": host,
        "scanned": len(results),
        "open_ports": open_count,
        "weakness_findings": weakness_total,
        "results": results,
    }


def do_tcp(params):
    """TCP端口扫描(单端口深度分析)"""
    return do_scan({**params, "ports": str(params.get("port", 80))})


def do_udp(params):
    """UDP端口探测"""
    host = params.get("host", "127.0.0.1")
    port = params.get("port", 53)
    timeout = params.get("timeout", 2)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        sock.sendto(b"\x00", (host, port))
        try:
            data, addr = sock.recvfrom(1024)
            sock.close()
            return {"ok": True, "cap": "port_scanner", "action": "udp",
                    "host": host, "port": port, "open": True, "response_len": len(data)}
        except socket.timeout:
            sock.close()
            return {"ok": True, "cap": "port_scanner", "action": "udp",
                    "host": host, "port": port, "open": False, "note": "无响应(可能开放但未响应探测)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}


HANDLERS = {"scan": do_scan, "tcp": do_tcp, "udp": do_udp}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "scan"
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
