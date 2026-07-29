# GBT Cloudflare 一键配置 · 收口脚本
# 配置 DNS / Bulk Redirects / Tunnel / 验证全部连接点
# ============================================================
"""
用法:
  python cf_setup.py --key YOUR_GLOBAL_API_KEY
  
Global API Key 获取:
  https://dash.cloudflare.com/profile/api-tokens → Global API Key → View

功能:
  1. 创建 api.gbtxiaotudou.com DNS CNAME 记录
  2. 创建 www → 根域名 301 跳转
  3. 创建 Bulk Redirects 列表
  4. 创建永久 Tunnel
  5. 验证所有 API 连接点
"""
import json, os, sys, time, urllib.request, urllib.error, subprocess
from pathlib import Path

# ═══════════════ 配置 ═══════════════
EMAIL = os.environ.get("CF_EMAIL", "")
ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID", "")
ZONE_ID = os.environ.get("CF_ZONE_ID", "")
DOMAIN = os.environ.get("CF_DOMAIN", "gbtxiaotudou.com")

def api(method, path, body=None):
    """Cloudflare API v4 调用"""
    url = f"https://api.cloudflare.com/client/v4{path}"
    headers = {
        "X-Auth-Email": EMAIL,
        "X-Auth-Key": API_KEY,
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"success": False, "errors": [{"message": f"HTTP {e.code}: {e.read().decode()[:200]}"}]}

def check(msg, result):
    ok = result.get("success", False)
    status = "✅" if ok else "❌"
    error = result.get("errors", [{}])[0].get("message", "") if not ok else ""
    print(f"  {status} {msg} {error}")
    return ok

# ═══════════════ 步骤 ═══════════════
def step1_dns():
    """创建 DNS 记录"""
    print("\n[1/5] DNS 记录", flush=True)
    
    records = [
        # api 子域名 → Worker 路由
        {"type": "CNAME", "name": f"api.{DOMAIN}", "content": DOMAIN, "proxied": True, "comment": "GBT API Gateway Worker"},
        # www → 根域名
        {"type": "CNAME", "name": f"www.{DOMAIN}", "content": DOMAIN, "proxied": True, "comment": "WWW redirect"},
    ]
    
    for rec in records:
        result = api("POST", f"/zones/{ZONE_ID}/dns_records", rec)
        name = rec["name"]
        if not result.get("success"):
            # 可能已存在, 尝试更新
            existing = api("GET", f"/zones/{ZONE_ID}/dns_records?type={rec['type']}&name={name}")
            if existing.get("success") and existing.get("result"):
                rid = existing["result"][0]["id"]
                result = api("PUT", f"/zones/{ZONE_ID}/dns_records/{rid}", rec)
        check(f"DNS {name} → {rec['content']}", result)

def step2_bulk_redirects():
    """创建 Bulk Redirects"""
    print("\n[2/5] Bulk Redirects", flush=True)
    
    # 创建重定向列表
    list_name = "gbt_redirects"
    list_result = api("POST", f"/accounts/{ACCOUNT_ID}/rules/lists", {
        "name": list_name,
        "kind": "redirect",
        "description": "GBT platform URL redirects",
    })
    
    list_id = None
    if list_result.get("success"):
        list_id = list_result["result"]["id"]
    else:
        # 已存在, 查找
        existing = api("GET", f"/accounts/{ACCOUNT_ID}/rules/lists")
        for item in existing.get("result", []):
            if item.get("name") == list_name:
                list_id = item["id"]
                break
    
    if list_id:
        # 批量添加重定向项
        items_result = api("POST", f"/accounts/{ACCOUNT_ID}/rules/lists/{list_id}/items", [
            {
                "redirect": {
                    "source_url": f"www.{DOMAIN}/",
                    "target_url": f"https://{DOMAIN}/",
                    "status_code": 301,
                }
            },
            {
                "redirect": {
                    "source_url": f"www.{DOMAIN}/*",
                    "target_url": f"https://{DOMAIN}/$1",
                    "status_code": 301,
                }
            },
            {
                "redirect": {
                    "source_url": f"{DOMAIN}/dashboard",
                    "target_url": f"https://{DOMAIN}/dashboard.html",
                    "status_code": 301,
                }
            },
        ])
        check("Bulk Redirect 列表项", items_result)
        
        # 创建 Bulk Redirect Rule
        rule_result = api("POST", f"/accounts/{ACCOUNT_ID}/rulesets", {
            "name": "gbt-redirects",
            "kind": "root",
            "phase": "http_request_redirect",
            "rules": [{
                "expression": "http.request.full_uri in $gbt_redirects",
                "action": "redirect",
            }]
        })
        check("Bulk Redirect Rule", rule_result)
    else:
        print("  ❌ 无法创建重定向列表")

def step3_tunnel():
    """创建永久 Tunnel"""
    print("\n[3/5] 永久 Tunnel", flush=True)
    
    # 检查 cloudflared
    cf = None
    for p in ["cloudflared", "cloudflared.exe"]:
        try:
            r = subprocess.run([p, "version"], capture_output=True, text=True)
            if r.returncode == 0:
                cf = p
                break
        except:
            pass
    
    if not cf:
        print("  ⚠️  cloudflared 未安装, 跳过 Tunnel 创建")
        print("  安装: winget install Cloudflare.cloudflared")
        return
    
    # 创建 Tunnel
    r = subprocess.run([cf, "tunnel", "create", "gbt-api-tunnel"], 
                       capture_output=True, text=True)
    if r.returncode != 0 and "already exists" not in r.stderr:
        print(f"  ⚠️  Tunnel 创建: {r.stderr[:200]}")
    else:
        print("  ✅ Tunnel gbt-api-tunnel 已就绪")
    
    # DNS 路由
    for hostname in ["api-tunnel", "deploy-tunnel"]:
        r = subprocess.run([cf, "tunnel", "route", "dns", "--overwrite-dns",
                           "gbt-api-tunnel", f"{hostname}.{DOMAIN}"],
                          capture_output=True, text=True)
        ok = r.returncode == 0
        print(f"  {'✅' if ok else '⚠️'} Tunnel DNS {hostname}.{DOMAIN}")

def step4_verify():
    """验证所有 API 连接点"""
    print("\n[4/5] 验证 API 连接点", flush=True)
    
    endpoints = [
        ("GET",  "/api/health",        "健康检查"),
        ("GET",  "/api/status",        "系统状态"),
        ("GET",  "/api/caps",          "能力列表"),
        ("GET",  "/api/payment/coins", "支付币种"),
        ("POST", "/api/eye/screenshot","眼睛截图"),
        ("POST", "/api/eye/scan",      "眼睛扫描"),
        ("POST", "/api/ask",           "AI问答"),
        ("GET",  "/api/metrics/ai",    "AI指标"),
    ]
    
    base = f"https://api.{DOMAIN}"
    ok_count = 0
    
    for method, path, desc in endpoints:
        url = f"{base}{path}"
        try:
            if method == "GET":
                req = urllib.request.Request(url)
            else:
                req = urllib.request.Request(url, data=b"{}", 
                    headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            ok = data.get("ok") == True
            if ok: ok_count += 1
            print(f"  {'✅' if ok else '⚠️'} {method} {path} ({desc})")
        except Exception as e:
            print(f"  ❌ {method} {path} ({desc}): {str(e)[:80]}")
    
    print(f"\n  结果: {ok_count}/{len(endpoints)} 端点正常")

def step5_deploy_all():
    import sys; sys.path.insert(0, str(Path(__file__).parent.parent))
    from brain.chain_kernel import enforce_chain
    enforce_chain("cloudflare.deploy_worker")
    workers = [
        ("_web/api-gateway", "gbt-api-gateway"),
    ]
    
    for wdir, wname in workers:
        r = subprocess.run(["wrangler", "deploy"], cwd=wdir,
                          capture_output=True, text=True)
        ok = "Deployed" in r.stdout or "deployed" in r.stdout
        print(f"  {'✅' if ok else '⚠️'} {wname}")

# ═══════════════ 入口 ═══════════════
if __name__ == "__main__":
    missing = []
    if not EMAIL: missing.append("CF_EMAIL (Cloudflare 账户邮箱)")
    if not ACCOUNT_ID: missing.append("CF_ACCOUNT_ID (Cloudflare 账户ID)")
    if not ZONE_ID: missing.append("CF_ZONE_ID (Cloudflare 区域ID)")

    if missing or "--key" not in sys.argv:
        print(__doc__)
        if missing:
            print("缺少以下环境变量:")
            for m in missing:
                print(f"  ❌ {m}")
        if "--key" not in sys.argv:
            print("请提供 --key YOUR_GLOBAL_API_KEY")
        print("\n必需环境变量:")
        print("  CF_EMAIL          Cloudflare 账户邮箱")
        print("  CF_ACCOUNT_ID     Cloudflare 账户ID")
        print("  CF_ZONE_ID        Cloudflare 区域ID")
        print("  CF_DOMAIN         域名 (默认: gbtxiaotudou.com)")
        sys.exit(1)

    API_KEY = sys.argv[sys.argv.index("--key") + 1]

    print("🥔 GBT Cloudflare 一键配置")
    print(f"   账户: {EMAIL}")
    print(f"   域名: {DOMAIN}")

    step1_dns()
    step2_bulk_redirects()
    step3_tunnel()
    step4_verify()
    step5_deploy_all()

    print(f"\n🎉 配置完成! 访问 https://{DOMAIN}")
