# 开发者：自由的风
"""packet_crafter/run.py — 自定义数据包构造"""
import sys, json, socket, struct, time

def do_craft(params):
    ptype = params.get("type", "tcp_syn")
    dst_ip = params.get("dst", params.get("target", "127.0.0.1"))
    dst_port = params.get("port", 80)
    try:
        if ptype == "tcp_syn":
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            src_ip = socket.gethostbyname(socket.gethostname())
            ip_header = struct.pack('!BBHHHBBH4s4s', 0x45, 0, 40, 54321, 0, 64, socket.IPPROTO_TCP, 0, socket.inet_aton(src_ip), socket.inet_aton(dst_ip))
            tcp_header = struct.pack('!HHLLBBHHH', 12345, dst_port, 100, 0, 5 << 4, 2, 5840, 0, 0)
            sock.sendto(ip_header + tcp_header, (dst_ip, 0))
            sock.close()
            return {"ok": True, "cap": "packet_crafter", "domain": "攻击域", "type": "TCP SYN", "dst": "{}:{}".format(dst_ip, dst_port)}
        elif ptype == "udp":
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(params.get("payload", "GBT_PROBE").encode(), (dst_ip, dst_port))
            sock.close()
            return {"ok": True, "type": "UDP", "dst": "{}:{}".format(dst_ip, dst_port)}
        elif ptype == "icmp":
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            payload = b"GBT_ECHO_" + struct.pack("d", time.time())
            icmp = struct.pack("!BBHHH", 8, 0, 0, 1, 1) + payload
            sock.sendto(icmp, (dst_ip, 1))
            sock.close()
            return {"ok": True, "type": "ICMP Echo", "dst": dst_ip}
    except PermissionError:
        return {"ok": False, "error": "需管理员权限(raw socket)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

HANDLERS = {"craft": do_craft}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "craft"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    r = HANDLERS.get(action, lambda p: {"ok": False, "error": "未知:{}".format(action)})(params)
    print(json.dumps(r, ensure_ascii=False, default=str))
