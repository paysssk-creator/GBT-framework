# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
# relay_agent.py — GBT 公网中继代理
# ============================================
# 远程机器运行此脚本 → 轮询公网命令 → 执行 → 回报
# 本机通过 relay_send.py 发送命令 → 读取结果
# 
# 部署: 复制此文件到远程机器，运行:
#   python relay_agent.py
# 或:
#   python relay_agent.py --once  (执行一次待处理命令后退出)
# ============================================
import json, os, sys, time, subprocess, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime

# ── 配置 ──
RELAY_URL = os.environ.get("GBT_RELAY_URL", "https://gbt-relay.example.com")
AGENT_ID = os.environ.get("GBT_AGENT_ID", "")
POLL_INTERVAL = int(os.environ.get("GBT_POLL_INTERVAL", "5"))  # 秒
WORK_DIR = Path(os.environ.get("GBT_WORK_DIR", os.getcwd()))

# ── 如果 RELAY_URL 未配置，使用本地文件模式 (同一台机器测试用) ──
USE_LOCAL = not RELAY_URL or "example.com" in RELAY_URL
LOCAL_INBOX = WORK_DIR / ".gbt" / "relay_inbox"
LOCAL_OUTBOX = WORK_DIR / ".gbt" / "relay_outbox"
LOCAL_INBOX.mkdir(parents=True, exist_ok=True)
LOCAL_OUTBOX.mkdir(parents=True, exist_ok=True)


def fetch_command():
    """从公网中继拉取待执行命令"""
    if USE_LOCAL:
        files = sorted(LOCAL_INBOX.glob("cmd_*.json"))
        if not files:
            return None
        cmd_file = files[0]
        cmd = json.loads(cmd_file.read_text(encoding="utf-8"))
        cmd["_file"] = str(cmd_file)
        return cmd
    
    try:
        url = f"{RELAY_URL}/api/agent/{AGENT_ID}/command"
        req = urllib.request.Request(url, headers={"User-Agent": "GBT-Agent/5.0"})
        resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return resp if resp.get("id") else None
    except Exception as e:
        return None


def report_result(cmd_id, result):
    """回报执行结果到公网中继"""
    if USE_LOCAL:
        # 删除命令文件，写入结果
        if "_file" in result:
            Path(result.pop("_file")).unlink(missing_ok=True)
        out_file = LOCAL_OUTBOX / f"result_{cmd_id}.json"
        out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    
    try:
        url = f"{RELAY_URL}/api/agent/{AGENT_ID}/result"
        data = json.dumps({"id": cmd_id, "result": result}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={
            "User-Agent": "GBT-Agent/5.0",
            "Content-Type": "application/json"
        })
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        return False


def execute_command(cmd):
    """执行命令"""
    cmd_id = cmd.get("id", str(int(time.time())))
    command = cmd.get("command", cmd.get("cmd", ""))
    timeout = cmd.get("timeout", 60)
    
    if not command:
        return {"id": cmd_id, "ok": False, "error": "空命令", "time": datetime.now().isoformat()}
    
    try:
        r = subprocess.run(
            command, shell=True,
            capture_output=True, text=True,
            timeout=timeout,
            cwd=str(WORK_DIR),
            encoding="utf-8", errors="replace"
        )
        return {
            "id": cmd_id,
            "ok": r.returncode == 0,
            "code": r.returncode,
            "stdout": r.stdout[-10000:],
            "stderr": r.stderr[-2000:],
            "time": datetime.now().isoformat(),
        }
    except subprocess.TimeoutExpired:
        return {"id": cmd_id, "ok": False, "error": f"超时({timeout}s)", "time": datetime.now().isoformat()}
    except Exception as e:
        return {"id": cmd_id, "ok": False, "error": str(e), "time": datetime.now().isoformat()}


def run_loop():
    """主循环：轮询→执行→回报"""
    print(f"🥔 GBT Relay Agent v5.0 [{AGENT_ID}]")
    print(f"   模式: {'本地文件' if USE_LOCAL else RELAY_URL}")
    print(f"   工作目录: {WORK_DIR}")
    print(f"   轮询间隔: {POLL_INTERVAL}s")
    print()
    
    while True:
        cmd = fetch_command()
        if cmd:
            cmd_id = cmd.get("id", "?")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 执行: {cmd.get('command','')[:80]}")
            result = execute_command(cmd)
            report_result(cmd_id, result)
            status = "✅" if result.get("ok") else "❌"
            print(f"  {status} {result.get('stdout','')[:100].strip()}")
        else:
            sys.stdout.write("."); sys.stdout.flush()
        time.sleep(POLL_INTERVAL)


def run_once():
    """只执行一次待处理命令"""
    cmd = fetch_command()
    if cmd:
        cmd_id = cmd.get("id", "?")
        print(f"执行: {cmd.get('command','')[:80]}")
        result = execute_command(cmd)
        report_result(cmd_id, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("无待处理命令")


if __name__ == "__main__":
    if "--once" in sys.argv:
        run_once()
    else:
        run_loop()
