# GBT 永久隧道 · 一键安装脚本
# 从临时 trycloudflare.com → 永久 Cloudflare Tunnel
# 运行一次即可，支持重启自动恢复
# ============================================================
"""
用法:
  python setup_permanent_tunnel.py install    — 首次安装
  python setup_permanent_tunnel.py status     — 查看状态
  python setup_permanent_tunnel.py restart    — 重启隧道

前置条件:
  1. cloudflared 已安装 (choco install cloudflared 或手动下载)
  2. Cloudflare API Token 已设置 (环境变量 CLOUDFLARE_API_TOKEN)
     Token 权限: Cloudflare Tunnel:Edit + DNS:Edit
  3. 域名 gbtxiaotudou.com 已在 Cloudflare 上
"""
import subprocess, sys, json, os, time
from pathlib import Path

# ═══════════════ 配置 ═══════════════
TUNNEL_NAME = "gbt-api-tunnel"
DOMAIN = "gbtxiaotudou.com"
CRED_DIR = Path.home() / ".cloudflared"
CRED_FILE = CRED_DIR / f"{TUNNEL_NAME}.json"
CONFIG_FILE = Path(__file__).parent / "config.yml"

# API 子域名
HOSTNAMES = {
    "api-tunnel": 9878,     # web_api 主服务
    "deploy-tunnel": 15888, # 部署代理
}

# ═══════════════ 工具函数 ═══════════════
def cloudflared(*args):
    """执行 cloudflared 命令"""
    cmd = ["cloudflared"] + list(args)
    print(f"  → {' '.join(cmd)}", flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ✗ 失败: {r.stderr[:300]}", flush=True)
    return r

def get_account_id():
    """从 cloudflared 获取 account ID"""
    # 尝试从已有凭证读取
    for f in CRED_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            if "AccountTag" in data:
                return data["AccountTag"]
        except:
            pass
    return None

def get_zone_id(domain):
    """通过 API 获取 zone ID"""
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    if not token:
        return None
    import urllib.request
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/zones?name={domain}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            if data.get("success") and data.get("result"):
                return data["result"][0]["id"]
    except:
        pass
    return None

# ═══════════════ 安装流程 ═══════════════
def cmd_install():
    print("🥔 GBT 永久隧道安装\n" + "=" * 60, flush=True)

    # 1. 检查 cloudflared
    r = cloudflared("version")
    if r.returncode != 0:
        print("\n❌ cloudflared 未安装!")
        print("   下载: https://github.com/cloudflare/cloudflared/releases")
        print("   或: winget install Cloudflare.cloudflared")
        return {"ok": False, "error": "cloudflared 未安装"}

    print("✅ cloudflared 已安装\n", flush=True)

    # 2. 确保凭证目录存在
    CRED_DIR.mkdir(parents=True, exist_ok=True)

    # 3. 登录 Cloudflare (如需要)
    if not CRED_FILE.exists():
        print("[2/5] 登录 Cloudflare...", flush=True)
        r = cloudflared("tunnel", "login")
        if r.returncode != 0:
            print("❌ 登录失败，请确保已设置 CLOUDFLARE_API_TOKEN", flush=True)
            print("   或手动运行: cloudflared tunnel login")
            return {"ok": False, "error": "登录失败"}
        print("✅ 已登录\n", flush=True)

    # 4. 创建永久隧道
    print(f"[3/5] 创建隧道: {TUNNEL_NAME}...", flush=True)
    r = cloudflared("tunnel", "create", TUNNEL_NAME)
    if r.returncode != 0:
        if "already exists" in r.stderr.lower() or "already exists" in r.stdout.lower():
            print(f"⚠️  隧道 {TUNNEL_NAME} 已存在，复用", flush=True)
        else:
            print(f"❌ 创建失败:\n{r.stderr}", flush=True)
            return {"ok": False, "error": "隧道创建失败"}

    # 等待凭证文件
    for _ in range(20):
        if CRED_FILE.exists():
            break
        time.sleep(0.5)

    if not CRED_FILE.exists():
        print("❌ 隧道凭证文件未生成", flush=True)
        return {"ok": False, "error": "凭证文件缺失"}

    print(f"✅ 隧道 {TUNNEL_NAME} 已创建\n", flush=True)

    # 5. 配置 DNS 路由
    print("[4/5] 配置 DNS 记录...", flush=True)
    zone_id = get_zone_id(DOMAIN)
    if zone_id:
        for hostname, port in HOSTNAMES.items():
            fqdn = f"{hostname}.{DOMAIN}"
            r = cloudflared(
                "tunnel", "route", "dns",
                "--overwrite-dns",
                TUNNEL_NAME, fqdn
            )
            if r.returncode == 0:
                print(f"  ✅ {fqdn} → localhost:{port}", flush=True)
            else:
                print(f"  ⚠️  {fqdn} DNS 配置: {r.stderr[:100]}", flush=True)
    else:
        print("  ⚠️  无法获取 Zone ID，请手动配置 DNS:", flush=True)
        for hostname in HOSTNAMES:
            print(f"    cloudflared tunnel route dns {TUNNEL_NAME} {hostname}.{DOMAIN}", flush=True)

    # 6. 安装为 Windows 服务
    print(f"\n[5/5] 安装 Windows 服务...", flush=True)

    # 复制 config.yml 到 .cloudflared
    target_config = CRED_DIR / "config.yml"
    import shutil
    shutil.copy(CONFIG_FILE, target_config)
    print(f"  ✅ 配置已复制到 {target_config}", flush=True)

    if sys.platform == "win32":
        r = cloudflared("service", "install")
        if r.returncode == 0:
            print("✅ cloudflared 已安装为 Windows 服务", flush=True)
            print("   服务名: Cloudflare Tunnel", flush=True)
            print("   开机自启: 是", flush=True)
        else:
            # 可能已经安装, 尝试直接启动
            r2 = cloudflared("service", "start")
            if r2.returncode != 0:
                print(f"⚠️  服务安装/启动: {r.stderr[:200]}", flush=True)
                print("   手动安装: cloudflared service install", flush=True)
    else:
        print("  非 Windows，请手动安装服务:", flush=True)
        print("   sudo cloudflared service install", flush=True)

    print("\n" + "=" * 60, flush=True)
    print("🎉 GBT 永久隧道安装完成!", flush=True)
    print(f"   API 端点: https://api-tunnel.{DOMAIN}", flush=True)
    print(f"   部署端点: https://deploy-tunnel.{DOMAIN}", flush=True)
    print("   管理: https://dash.cloudflare.com/ → Zero Trust → Tunnels", flush=True)

    return {"ok": True, "tunnel": TUNNEL_NAME, "hostnames": list(HOSTNAMES.keys())}

def cmd_status():
    """查看隧道状态"""
    print("📊 GBT 隧道状态\n" + "=" * 45, flush=True)
    r = cloudflared("tunnel", "info", TUNNEL_NAME)
    if r.returncode == 0:
        print(r.stdout, flush=True)

    # 检查服务
    if sys.platform == "win32":
        r2 = subprocess.run(["sc", "query", "Cloudflared"], capture_output=True, text=True)
        if "RUNNING" in r2.stdout:
            print("✅ Windows 服务: 运行中", flush=True)
        else:
            print("⚠️  Windows 服务: 未运行", flush=True)

    # 检查端口
    for hostname, port in HOSTNAMES.items():
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(("127.0.0.1", port))
        s.close()
        status = "✅ 监听中" if result == 0 else "❌ 未监听"
        print(f"   localhost:{port} ({hostname}) → {status}", flush=True)

def cmd_restart():
    """重启隧道服务"""
    if sys.platform == "win32":
        subprocess.run(["sc", "stop", "Cloudflared"], capture_output=True)
        time.sleep(2)
        subprocess.run(["sc", "start", "Cloudflared"], capture_output=True)
        print("✅ 隧道服务已重启", flush=True)
    else:
        cloudflared("service", "restart")
        print("✅ 隧道服务已重启", flush=True)

# ═══════════════ 入口 ═══════════════
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "install"
    handlers = {"install": cmd_install, "status": cmd_status, "restart": cmd_restart}
    handler = handlers.get(cmd, cmd_install)
    result = handler()
    if isinstance(result, dict):
        print(json.dumps(result, ensure_ascii=False, indent=2))
