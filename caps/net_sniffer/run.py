# 开发者：自由的风
"""net_sniffer/run.py — 网络流量嗅探分析
========================================
侦察域 ready — 捕获网络数据包，分析协议/端口/流量模式以发现薄弱点。
"""
import sys, json, os, subprocess, time, threading, socket, struct

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_sniffer_state = {"running": False, "thread": None, "packets": [], "stats": {}}

try:
    import scapy.all as scapy
    HAS_SCAPY = True
except ImportError:
    HAS_SCAPY = False


def _sniff_scapy(interface, count, timeout, filter_str):
    """Scapy嗅探"""
    packets = []
    try:
        captured = scapy.sniff(iface=interface, count=count, timeout=timeout, filter=filter_str)
        for pkt in captured:
            info = {"time": pkt.time, "size": len(pkt)}
            if pkt.haslayer(scapy.IP):
                info["src"] = pkt[scapy.IP].src
                info["dst"] = pkt[scapy.IP].dst
                info["proto"] = pkt[scapy.IP].proto
            if pkt.haslayer(scapy.TCP):
                info["sport"] = pkt[scapy.TCP].sport
                info["dport"] = pkt[scapy.TCP].dport
                info["flags"] = str(pkt[scapy.TCP].flags)
            elif pkt.haslayer(scapy.UDP):
                info["sport"] = pkt[scapy.UDP].sport
                info["dport"] = pkt[scapy.UDP].dport
            packets.append(info)
    except Exception as e:
        packets = [{"error": str(e)}]
    return packets


def _sniff_raw(count, timeout):
    """Raw socket嗅探(降级)"""
    packets = []
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
        sock.settimeout(timeout if timeout else 10)
        sock.bind(("0.0.0.0", 0))
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        # 启用混杂模式(Windows)
        if sys.platform == "win32":
            sock.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

        for _ in range(count or 20):
            try:
                data, addr = sock.recvfrom(65535)
                packets.append({"src": addr[0], "size": len(data),
                               "time": time.time(), "raw_len": len(data)})
            except socket.timeout:
                break
            except Exception:
                break

        if sys.platform == "win32":
            try:
                sock.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
            except Exception:
                pass
        sock.close()
    except PermissionError:
        packets = [{"error": "需要管理员权限运行"}]
    except Exception as e:
        packets = [{"error": str(e)}]
    return packets


def do_start(params):
    """开始嗅探"""
    global _sniffer_state
    if _sniffer_state["running"]:
        return {"ok": True, "cap": "net_sniffer", "action": "start", "status": "already_running"}

    interface = params.get("interface", params.get("iface", None))
    count = params.get("count", 50)
    timeout = params.get("timeout", 30)
    filter_str = params.get("filter", "tcp or udp")

    def _sniff_thread():
        if HAS_SCAPY:
            pkts = _sniff_scapy(interface, count, timeout, filter_str)
        else:
            pkts = _sniff_raw(count, timeout)
        _sniffer_state["packets"] = pkts
        _sniffer_state["running"] = False

        # 统计
        stats = {"total": len(pkts), "protocols": {}, "ports": {}, "ips": {}}
        for p in pkts:
            proto = p.get("proto", "unknown")
            stats["protocols"][proto] = stats["protocols"].get(proto, 0) + 1
            dport = p.get("dport", 0)
            if dport:
                stats["ports"][str(dport)] = stats["ports"].get(str(dport), 0) + 1
            src = p.get("src", "")
            if src:
                stats["ips"][src] = stats["ips"].get(src, 0) + 1
        _sniffer_state["stats"] = stats

    _sniffer_state["running"] = True
    _sniffer_state["packets"] = []
    _sniffer_state["stats"] = {}

    t = threading.Thread(target=_sniff_thread, daemon=True)
    t.start()
    _sniffer_state["thread"] = t

    return {
        "ok": True,
        "cap": "net_sniffer",
        "action": "start",
        "domain": "侦察域",
        "status": "started",
        "engine": "scapy" if HAS_SCAPY else "raw_socket",
        "count": count, "timeout": timeout,
    }


def do_stop(params):
    """停止嗅探"""
    global _sniffer_state
    _sniffer_state["running"] = False

    stats = _sniffer_state.get("stats", {})
    packets = _sniffer_state.get("packets", [])

    return {
        "ok": True,
        "cap": "net_sniffer",
        "action": "stop",
        "domain": "侦察域",
        "packets_captured": len(packets),
        "stats": stats,
        "packets": packets[:30],
    }


def do_analyze(params):
    """分析已捕获的流量"""
    packets = _sniffer_state.get("packets", [])
    stats = _sniffer_state.get("stats", {})

    if not packets:
        return {"ok": True, "cap": "net_sniffer", "action": "analyze",
                "note": "无已捕获数据包，先调用start开始嗅探"}

    # 薄弱点分析
    weaknesses = []
    ports = stats.get("ports", {})
    if "23" in ports:
        weaknesses.append({"finding": "Telnet流量(明文密码)", "severity": "critical"})
    if "21" in ports:
        weaknesses.append({"finding": "FTP流量(明文密码)", "severity": "critical"})
    if "1433" in ports:
        weaknesses.append({"finding": "MSSQL流量(可能远程数据库连接)", "severity": "warning"})
    if "3306" in ports:
        weaknesses.append({"finding": "MySQL远程连接", "severity": "warning"})

    return {
        "ok": True,
        "cap": "net_sniffer",
        "action": "analyze",
        "domain": "侦察域",
        "total_packets": len(packets),
        "protocols": stats.get("protocols", {}),
        "top_ports": dict(sorted(stats.get("ports", {}).items(), key=lambda x: -x[1])[:10]),
        "weaknesses": weaknesses,
    }


HANDLERS = {"start": do_start, "stop": do_stop, "analyze": do_analyze}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "analyze"
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
