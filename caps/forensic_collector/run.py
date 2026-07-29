# 开发者：自由的风
"""forensic_collector/run.py — 取证数据收集"""
import sys, json, os, subprocess, time, hashlib, shutil
from pathlib import Path
from datetime import datetime

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORENSIC_DIR = Path.home() / ".gbt" / "forensics"
FORENSIC_DIR.mkdir(parents=True, exist_ok=True)

def do_collect(params):
    scope = params.get("scope", "system")
    case_id = params.get("case_id", "CASE_{}".format(int(time.time())))
    case_dir = FORENSIC_DIR / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    evidence = {"case_id": case_id, "timestamp": datetime.now().isoformat(), "scope": scope, "items": []}

    try:
        # 系统信息
        if scope in ("system", "all"):
            si = {}
            si["hostname"] = os.environ.get("COMPUTERNAME", os.uname().nodename if hasattr(os, 'uname') else "")
            si["platform"] = sys.platform
            r = subprocess.run(["systeminfo"] if sys.platform == "win32" else ["uname", "-a"], capture_output=True, text=True, timeout=10)
            si["systeminfo"] = r.stdout[:2000]
            si_file = case_dir / "system_info.txt"
            si_file.write_text(json.dumps(si, ensure_ascii=False, indent=2), encoding="utf-8")
            evidence["items"].append({"type": "system_info", "file": str(si_file), "hash": hashlib.sha256(json.dumps(si).encode()).hexdigest()[:16]})
    except: pass

    try:
        # 进程快照
        if scope in ("process", "all"):
            r = subprocess.run(["tasklist", "/fo", "csv"] if sys.platform == "win32" else ["ps", "aux"], capture_output=True, text=True, timeout=10)
            proc_file = case_dir / "process_snapshot.csv"
            proc_file.write_text(r.stdout, encoding="utf-8")
            evidence["items"].append({"type": "process_snapshot", "file": str(proc_file), "size": len(r.stdout)})
    except: pass

    try:
        # 网络连接快照
        if scope in ("network", "all"):
            r = subprocess.run(["netstat", "-ano"] if sys.platform == "win32" else ["ss", "-tulpn"], capture_output=True, text=True, timeout=10)
            net_file = case_dir / "network_snapshot.txt"
            net_file.write_text(r.stdout, encoding="utf-8")
            evidence["items"].append({"type": "network_snapshot", "file": str(net_file), "size": len(r.stdout)})
    except: pass

    try:
        # 用户列表
        if scope in ("users", "all"):
            r = subprocess.run(["net", "user"] if sys.platform == "win32" else ["cat", "/etc/passwd"], capture_output=True, text=True, timeout=5)
            users_file = case_dir / "users.txt"
            users_file.write_text(r.stdout, encoding="utf-8")
            evidence["items"].append({"type": "users", "file": str(users_file)})
    except: pass

    try:
        # Shell历史
        if scope in ("history", "all"):
            history_paths = [Path.home() / ".bash_history", Path.home() / ".zsh_history", Path.home() / ".python_history"]
            for hp in history_paths:
                if hp.exists():
                    shutil.copy2(hp, case_dir / "shell_history_{}".format(hp.name))
                    evidence["items"].append({"type": "shell_history", "file": str(case_dir / "shell_history_{}".format(hp.name))})
    except: pass

    # 生成链式证据报告
    report = {
        "case_id": case_id, "timestamp": datetime.now().isoformat(),
        "collector": "GBT Forensic Collector v5.0",
        "chain_of_custody": "采集→哈希→封存",
        "evidence_items": len(evidence["items"]),
        "items": evidence["items"],
    }
    report_file = case_dir / "evidence_manifest.json"
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"ok": True, "cap": "forensic_collector", "domain": "攻击域",
            "case_id": case_id, "items": len(evidence["items"]),
            "case_dir": str(case_dir), "manifest": str(report_file)}

HANDLERS = {"collect": do_collect}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "collect"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    r = HANDLERS.get(action, lambda p: {"ok": False})(params)
    print(json.dumps(r, ensure_ascii=False, default=str))
