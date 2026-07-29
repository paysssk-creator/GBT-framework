# 开发者：自由的风
"""wifi_scanner/run.py — WiFi网络扫描
======================================
侦察域 ready — 扫描附近WiFi网络(SSID/BSSID/信号强度/加密/信道)
"""
import sys, json, os, subprocess, re
from pathlib import Path

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def do_scan(params):
    networks = []
    try:
        if sys.platform == "win32":
            r = subprocess.run(["netsh", "wlan", "show", "networks", "mode=Bssid"], capture_output=True, text=True, timeout=15)
            ssid, bssid, signal, channel, auth = "", "", "", "", ""
            for line in r.stdout.split("\n"):
                if "SSID" in line and "BSSID" not in line:
                    m = re.search(r'SSID\s+\d+\s*:\s*(.+)', line)
                    if m: ssid = m.group(1).strip()
                if "BSSID" in line:
                    m = re.search(r'BSSID\s+\d+\s*:\s*([0-9a-f:]+)', line, re.I)
                    if m: bssid = m.group(1)
                if "Signal" in line:
                    m = re.search(r'Signal\s*:\s*(\d+)', line)
                    if m: signal = m.group(1) + "%"
                if "Channel" in line:
                    m = re.search(r'Channel\s*:\s*(\d+)', line)
                    if m: channel = m.group(1)
                if "Authentication" in line:
                    m = re.search(r'Authentication\s*:\s*(.+)', line)
                    if m: auth = m.group(1).strip()
                if ssid and bssid:
                    networks.append({"ssid": ssid, "bssid": bssid, "signal": signal, "channel": channel, "auth": auth})
                    ssid = bssid = signal = channel = auth = ""
        else:
            r = subprocess.run(["nmcli", "-t", "-f", "SSID,BSSID,SIGNAL,CHAN,SECURITY", "dev", "wifi", "list"], capture_output=True, text=True, timeout=15)
            for line in r.stdout.strip().split("\n"):
                parts = line.split(":")
                if len(parts) >= 5:
                    networks.append({"ssid": parts[0], "bssid": parts[1], "signal": parts[2], "channel": parts[3], "auth": parts[4]})
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
    networks.sort(key=lambda n: n.get("signal","0%").replace("%",""), reverse=True)
    return {"ok": True, "cap": "wifi_scanner", "action": "scan", "domain": "侦察域", "networks": networks, "total": len(networks)}

HANDLERS = {"scan": do_scan}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "scan"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
