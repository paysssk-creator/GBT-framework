# 开发者：自由的风
"""remote_deploy/run.py — 远程操控部署
=======================================
SSH连接/远程命令/文件传输/一键部署到远程生产环境

主机配置: ~/.gbt/hosts.json
格式: {"hosts":[{"name":"prod","host":"1.2.3.4","port":22,"user":"root","key":"~/.ssh/id_rsa"}]}
"""
import sys, json, os, subprocess, shutil, tempfile
from pathlib import Path
from datetime import datetime, timezone

HOSTS_FILE = Path.home() / ".gbt" / "hosts.json"
HOSTS_FILE.parent.mkdir(parents=True, exist_ok=True)
SANDBOX_DIR = Path(__file__).parent.parent.parent

def _load_hosts():
    if HOSTS_FILE.exists():
        try:
            return json.loads(HOSTS_FILE.read_text(encoding="utf-8")).get("hosts", [])
        except Exception:
            pass
    return []

def _find_host(name=None, host=None):
    hosts = _load_hosts()
    for h in hosts:
        if name and h.get("name") == name:
            return h
        if host and h.get("host") == host:
            return h
    return None

def _ssh_args(host_cfg):
    args = ["ssh"]
    port = host_cfg.get("port", 22)
    if port != 22:
        args.extend(["-p", str(port)])
    key = host_cfg.get("key", "")
    if key:
        args.extend(["-i", os.path.expanduser(key)])
    args.extend(["-o", "StrictHostKeyChecking=accept-new"])
    args.extend(["-o", "ConnectTimeout=10"])
    args.append(f"{host_cfg['user']}@{host_cfg['host']}")
    return args

def _scp_args(host_cfg):
    args = ["scp"]
    port = host_cfg.get("port", 22)
    if port != 22:
        args.extend(["-P", str(port)])
    key = host_cfg.get("key", "")
    if key:
        args.extend(["-i", os.path.expanduser(key)])
    args.extend(["-o", "StrictHostKeyChecking=accept-new"])
    args.extend(["-o", "ConnectTimeout=10"])
    return args

def do_connect(params):
    name = params.get("name", "")
    host_ip = params.get("host", "")
    h = _find_host(name=name) or _find_host(host=host_ip)
    if not h:
        return {"ok": False, "error": "未找到主机。先用 gbt db 管理主机列表，或传入 host/user 参数"}
    # 如果没有配置，支持命令行直接传参
    user = params.get("user") or h.get("user", "root")
    host = params.get("host") or h.get("host", "")
    port = params.get("port") or h.get("port", 22)
    key = params.get("key") or h.get("key", "")
    if not host:
        return {"ok": False, "error": "缺少 host 参数"}
    try:
        args = _ssh_args({"host": host, "port": port, "user": user, "key": key})
        args.append("echo OK && uname -a")
        r = subprocess.run(args, capture_output=True, text=True, timeout=15,
                          encoding="utf-8", errors="replace")
        return {
            "ok": r.returncode == 0 and "OK" in r.stdout,
            "host": host,
            "output": r.stdout.strip(),
            "exit_code": r.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "连接超时", "host": host}
    except FileNotFoundError:
        return {"ok": False, "error": "ssh 未安装。Windows: 安装 OpenSSH 客户端"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def do_exec(params):
    cmd = params.get("cmd", params.get("command", ""))
    name = params.get("name", "")
    host_ip = params.get("host", "")
    user = params.get("user", "")
    port = params.get("port", 22)
    key = params.get("key", "")
    if not cmd:
        return {"ok": False, "error": "缺少 cmd/command 参数"}
    h = _find_host(name=name) or _find_host(host=host_ip)
    cfg = {"host": host_ip or (h.get("host") if h else ""),
           "port": port or (h.get("port", 22) if h else 22),
           "user": user or (h.get("user", "root") if h else "root"),
           "key": key or (h.get("key", "") if h else "")}
    if not cfg["host"]:
        return {"ok": False, "error": "缺少 host — 请配置主机或传入 host 参数"}
    try:
        args = _ssh_args(cfg)
        args.append(cmd)
        r = subprocess.run(args, capture_output=True, text=True, timeout=60,
                          encoding="utf-8", errors="replace")
        return {
            "ok": r.returncode == 0,
            "host": cfg["host"],
            "output": r.stdout.strip(),
            "stderr": r.stderr.strip()[:500],
            "exit_code": r.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "命令执行超时 (60s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def do_upload(params):
    local = params.get("local", params.get("source", ""))
    remote = params.get("remote", params.get("dest", ""))
    name = params.get("name", "")
    host_ip = params.get("host", "")
    if not local or not remote:
        return {"ok": False, "error": "缺少 local/source 和 remote/dest 参数"}
    h = _find_host(name=name) or _find_host(host=host_ip)
    if not h and not host_ip:
        return {"ok": False, "error": "缺少主机配置"}
    cfg = {"host": host_ip or h.get("host", ""),
           "port": params.get("port", h.get("port", 22)),
           "user": params.get("user", h.get("user", "root")),
           "key": params.get("key", h.get("key", ""))}
    try:
        args = _scp_args(cfg)
        args.extend(["-r", local, f"{cfg['user']}@{cfg['host']}:{remote}"])
        r = subprocess.run(args, capture_output=True, text=True, timeout=120,
                          encoding="utf-8", errors="replace")
        return {
            "ok": r.returncode == 0,
            "local": local,
            "remote": f"{cfg['host']}:{remote}",
            "exit_code": r.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "上传超时 (120s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def do_download(params):
    remote = params.get("remote", params.get("source", ""))
    local = params.get("local", params.get("dest", ""))
    name = params.get("name", "")
    host_ip = params.get("host", "")
    if not remote or not local:
        return {"ok": False, "error": "缺少 remote/source 和 local/dest 参数"}
    h = _find_host(name=name) or _find_host(host=host_ip)
    if not h and not host_ip:
        return {"ok": False, "error": "缺少主机配置"}
    cfg = {"host": host_ip or h.get("host", ""),
           "port": params.get("port", h.get("port", 22)),
           "user": params.get("user", h.get("user", "root")),
           "key": params.get("key", h.get("key", ""))}
    try:
        args = _scp_args(cfg)
        args.extend(["-r", f"{cfg['user']}@{cfg['host']}:{remote}", local])
        r = subprocess.run(args, capture_output=True, text=True, timeout=120,
                          encoding="utf-8", errors="replace")
        return {
            "ok": r.returncode == 0,
            "remote": f"{cfg['host']}:{remote}",
            "local": local,
            "exit_code": r.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "下载超时 (120s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def do_deploy(params):
    """一键部署: 本地打包 → 上传 → 远程解压 → 重启"""
    name = params.get("name", "")
    host_ip = params.get("host", "")
    local_dir = params.get("local", str(SANDBOX_DIR.parent))
    remote_dir = params.get("remote", "/opt/gbt")
    restart_cmd = params.get("restart", "sudo systemctl restart gbt 2>/dev/null || sudo supervisorctl restart gbt 2>/dev/null || echo 'no restart cmd'")
    h = _find_host(name=name) or _find_host(host=host_ip)
    if not h and not host_ip:
        return {"ok": False, "error": "缺少主机配置"}
    cfg = {"host": host_ip or h.get("host", ""),
           "port": params.get("port", h.get("port", 22)),
           "user": params.get("user", h.get("user", "root")),
           "key": params.get("key", h.get("key", ""))}
    if not cfg["host"]:
        return {"ok": False, "error": "缺少 host"}
    steps = []
    # 1. 打包
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"gbt_deploy_{ts}.tar.gz"
    archive_path = Path(tempfile.gettempdir()) / archive_name
    try:
        r = subprocess.run(
            ["tar", "-czf", str(archive_path), "-C", str(Path(local_dir).parent),
             Path(local_dir).name, "--exclude=__pycache__", "--exclude=.git",
             "--exclude=node_modules", "--exclude=.venv", "--exclude=dist"],
            capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace"
        )
        if r.returncode != 0:
            return {"ok": False, "error": f"打包失败: {r.stderr[:200]}", "step": "pack"}
        size_kb = round(archive_path.stat().st_size / 1024, 1)
        steps.append({"step": "pack", "ok": True, "size_kb": size_kb})
    except FileNotFoundError:
        # tar 不可用，尝试 zip
        import zipfile
        archive_path = Path(tempfile.gettempdir()) / f"gbt_deploy_{ts}.zip"
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in Path(local_dir).rglob("*"):
                if any(p in str(f) for p in ['__pycache__', '.git', 'node_modules', '.venv', 'dist']):
                    continue
                if f.is_file():
                    zf.write(f, f.relative_to(Path(local_dir).parent))
        size_kb = round(archive_path.stat().st_size / 1024, 1)
        steps.append({"step": "pack", "ok": True, "size_kb": size_kb, "format": "zip"})
        archive_name = f"gbt_deploy_{ts}.zip"
    # 2. 上传
    try:
        args = _scp_args(cfg)
        args.extend([str(archive_path), f"{cfg['user']}@{cfg['host']}:/tmp/{archive_name}"])
        r = subprocess.run(args, capture_output=True, text=True, timeout=120,
                          encoding="utf-8", errors="replace")
        if r.returncode != 0:
            return {"ok": False, "error": f"上传失败: {r.stderr[:200]}", "step": "upload", "steps": steps}
        steps.append({"step": "upload", "ok": True})
    except Exception as e:
        return {"ok": False, "error": str(e), "step": "upload", "steps": steps}
    # 3. 远程解压 + 重启
    try:
        if archive_name.endswith(".tar.gz"):
            remote_cmd = f"mkdir -p {remote_dir} && cd {remote_dir} && tar -xzf /tmp/{archive_name} --strip-components=1 && rm /tmp/{archive_name} && {restart_cmd}"
        else:
            remote_cmd = f"mkdir -p {remote_dir} && cd {remote_dir} && unzip -o /tmp/{archive_name} && rm /tmp/{archive_name} && {restart_cmd}"
        args = _ssh_args(cfg)
        args.append(remote_cmd)
        r = subprocess.run(args, capture_output=True, text=True, timeout=120,
                          encoding="utf-8", errors="replace")
        steps.append({"step": "deploy", "ok": r.returncode == 0, "output": r.stdout.strip()[:500]})
    except Exception as e:
        steps.append({"step": "deploy", "ok": False, "error": str(e)})
    # 4. 清理本地
    archive_path.unlink(missing_ok=True)
    return {
        "ok": all(s.get("ok") for s in steps),
        "host": cfg["host"],
        "remote_dir": remote_dir,
        "steps": steps,
    }

def do_hosts(params=None):
    hosts = _load_hosts()
    return {"ok": True, "hosts": hosts, "count": len(hosts),
            "config_file": str(HOSTS_FILE),
            "help": "编辑 ~/.gbt/hosts.json 添加主机"}

HANDLERS = {
    "connect": do_connect, "exec": do_exec, "upload": do_upload,
    "download": do_download, "deploy": do_deploy, "hosts": do_hosts,
}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 else "run"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知动作: {action}", "available": list(HANDLERS.keys())})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
