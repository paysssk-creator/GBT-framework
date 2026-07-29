# 开发者：自由的风
"""threat_hunter/run.py — 主动威胁狩猎"""
import sys, json, os, subprocess, re, time
from pathlib import Path

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUNT_DIR = Path.home() / ".gbt" / "threat_hunts"
HUNT_DIR.mkdir(parents=True, exist_ok=True)

IOC_PATTERNS = {
    "suspicious_process": [r'cmd\.exe.*/c.*powershell', r'wscript\.exe', r'cscript\.exe', r'mshta\.exe', r'rundll32\.exe.*javascript'],
    "persistence": [r'\\Run\\', r'\\RunOnce\\', r'\\Services\\', r'schtasks.*create', r'Startup'],
    "lateral_movement": [r'psexec', r'wmic.*process.*call.*create', r'winrm', r'Invoke-Command'],
    "data_exfil": [r'\.upload', r'\.post.*\.read', r'nc\s+.*>\s+/dev/tcp'],
    "c2_communication": [r'https?://\d+\.\d+\.\d+\.\d+', r'\.onion', r'\.ddns\.net', r'reverse_.*shell'],
}

def do_hunt(params):
    scope = params.get("scope", "process")
    findings = []

    if scope == "process" or scope == "all":
        try:
            if sys.platform == "win32":
                r = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True, timeout=10)
                processes = r.stdout
            else:
                r = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=10)
                processes = r.stdout
            for category, patterns in IOC_PATTERNS.items():
                for pattern in patterns:
                    for m in re.finditer(pattern, processes, re.IGNORECASE):
                        findings.append({"category": category, "match": m.group(0)[:120], "source": "process_list"})
        except Exception:
            pass

    if scope == "network" or scope == "all":
        try:
            if sys.platform == "win32":
                r = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, timeout=10)
            else:
                r = subprocess.run(["ss", "-tulpn"], capture_output=True, text=True, timeout=10)
            connections = r.stdout
            suspicious_ports = [4444, 5555, 6666, 7777, 8888, 9999, 31337, 1337]
            for port in suspicious_ports:
                if ":{}".format(port) in connections:
                    findings.append({"category": "c2_port", "match": "Suspicious port {}".format(port), "source": "network"})
            known_c2 = [r'\d+\.\d+\.\d+\.\d+:4444', r'ESTABLISHED.*\d+\.\d+\.\d+\.\d+']
            for pattern in known_c2:
                for m in re.finditer(pattern, connections):
                    findings.append({"category": "c2_connection", "match": m.group(0), "source": "network"})
        except Exception:
            pass

    if scope == "registry" or scope == "all":
        if sys.platform == "win32":
            for hive in [r"HKLM\Software\Microsoft\Windows\CurrentVersion\Run",
                         r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run"]:
                try:
                    r = subprocess.run(["reg", "query", hive], capture_output=True, text=True, timeout=5)
                    if r.returncode == 0 and r.stdout.strip():
                        entries = re.findall(r'REG_SZ\s+(.+)', r.stdout)
                        for entry in entries:
                            if any(s in entry.lower() for s in ["powershell", "cmd", "vbs", "js", "tmp", "temp"]):
                                findings.append({"category": "suspicious_autorun", "match": entry[:120], "source": "registry"})
                except Exception:
                    pass

    ts = time.strftime("%Y%m%d_%H%M%S")
    report_file = HUNT_DIR / "hunt_{}.json".format(ts)
    report = {"timestamp": ts, "scope": scope, "findings": findings, "total": len(findings),
              "verdict": "发现威胁" if findings else "未发现活跃威胁"}
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"ok": True, "cap": "threat_hunter", "domain": "攻击域", "scope": scope,
            "findings": findings[:20], "total": len(findings), "report": str(report_file)}

HANDLERS = {"hunt": do_hunt}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "hunt"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    r = HANDLERS.get(action, lambda p: {"ok": False})(params)
    print(json.dumps(r, ensure_ascii=False, default=str))
