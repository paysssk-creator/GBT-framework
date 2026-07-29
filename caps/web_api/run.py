# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""web_api/run.py — GBT Web API服务器
=====================================
连接网站前端到后端cap: 支付·OAuth·部署·分账
"""
import sys, json, os, subprocess, urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

SANDBOX = Path(__file__).parent.parent
sys.path.insert(0, str(SANDBOX))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "integrations" / "payment")); from wallet_safe import rate_check, safe_error
PORT = int(os.environ.get("GBT_API_PORT", "9878"))
API_TOKEN = os.environ.get("GBT_API_TOKEN", "")

RATE_LIMIT_FINANCIAL = int(os.environ.get("GBT_RATE_LIMIT_FINANCIAL", "10"))
PORT_MGMT = int(os.environ.get("GBT_MGMT_PORT", "9879"))


def _call_cap(cap, action, params=None, timeout=30):
    """调用任意cap"""
    # Search caps/ + _payment/ + _deploy/
    search = [SANDBOX / cap, SANDBOX.parent / "_payment" / cap, SANDBOX.parent / "_deploy" / cap]
    rp = None
    for s in search:
        if (s / "run.py").exists():
            rp = s / "run.py"
            break
    if not rp:
        return {"ok": False, "error": f"cap {cap} 不存在"}
    try:
        params_json = json.dumps(params or {}, ensure_ascii=False)
        r = subprocess.run(
            [sys.executable, str(rp), action, params_json],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(SANDBOX), encoding="utf-8", errors="replace"
        )
        if r.stdout.strip():
            return json.loads(r.stdout)
        return {"ok": False, "error": r.stderr[:200]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"超时({timeout}s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

class APIHandler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass

    def _check_auth(self):
        if not API_TOKEN:
            return True
        auth_header = self.headers.get("Authorization", "")
        return auth_header == f"Bearer {API_TOKEN}"

    def _require_auth(self):
        """严格认证: 始终要求有效token, 不降级"""
        if not API_TOKEN:
            return False
        return self.headers.get("Authorization", "") == f"Bearer {API_TOKEN}"

    def _financial_guard(self, body):
        """金融操作守卫: 认证+限流+body校验+幂等键. 返回(status, error_data)或None"""
        if not self._require_auth():
            return 401, {"ok": False, "error": "未授权"}
        client_ip = self.client_address[0]
        if not rate_check(f"api:{client_ip}", RATE_LIMIT_FINANCIAL):
            return 429, {"ok": False, "error": "请求过于频繁"}
        if not body:
            return 400, {"ok": False, "error": "请求体不能为空"}
        nonce = body.get("nonce") or body.get("idempotency_key")
        if not nonce:
            return 400, {"ok": False, "error": "缺少nonce或idempotency_key"}
        return None

    def _cors(self):
        origin = os.environ.get("GBT_CORS_ORIGIN", "https://gbtxiaotudou.com")
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,Authorization")
    def do_OPTIONS(self):
        self.send_response(200); self._cors(); self.end_headers()

    def _json(self, data, status=200):
        if isinstance(data, dict) and "error" in data:
            data = {**data, "error": safe_error(str(data["error"]))}
        self.send_response(status); self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))

        if path == "/api/health":
            self._json({"ok": True, "status": "running"})

        elif path == "/api/status":
            self._json(_call_cap("gbt_brain", "status"))

        elif path == "/api/caps":
            self._json(_call_cap("devourer", "gaps"))

        elif path == "/api/payment/coins":
            self._json(_call_cap("cryptapi_pay", "coins"))

        elif path == "/api/help":
            topic = params.get("topic", params.get("t", "index"))
            self._json(_call_cap("ai_service", "help", {"topic": topic}))


        elif path == "/api/leaderboard":
            self._json(_call_cap("trending_scanner", "leaderboard", params, timeout=30))

        elif path in ("/api/oauth/status", "/api/revenue/stats",
                      "/api/projects", "/api/nexus"):
            if not self._check_auth():
                self._json({"ok": False, "error": "未授权"}, status=401)
                return
            routes = {
                "/api/oauth/status": ("github_oauth", "status", {}),
                "/api/revenue/stats": ("revenue_split", "stats", {}),
                "/api/projects": ("project_registry", "list", {}),
                "/api/nexus": ("nexus_monitor", "check", {}),
            }
            cap, action, extra = routes[path]
            self._json(_call_cap(cap, action, extra))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length)) if length > 0 else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._json({"ok": False, "error": "请求格式无效"}, status=400)
            return
        path = self.path.split("?")[0]

        # ── 金融操作端点: 完整守卫(认证+限流+body+幂等键) ──
        if path == "/api/payment/create":
            guard = self._financial_guard(body)
            if guard is not None: self._json(guard[1], status=guard[0]); return
            result = _call_cap("payments", "crypto", body)
            if result.get("ok"):
                _call_cap("platform_account", "incoming", {
                    "amount": float(body.get("amount", 0)),
                    "user_id": body.get("developer", body.get("order_id", "unknown")),
                    "order_id": body.get("order_id", ""),
                })
            self._json(result)

        elif path == "/api/wallet/transfer":
            guard = self._financial_guard(body)
            if guard is not None: self._json(guard[1], status=guard[0]); return
            self._json(_call_cap("virtual_wallet", "transfer", body))

        elif path == "/api/wallet/withdraw":
            guard = self._financial_guard(body)
            if guard is not None: self._json(guard[1], status=guard[0]); return
            self._json(_call_cap("virtual_wallet", "withdraw", body))

        elif path == "/api/wallet/swap":
            guard = self._financial_guard(body)
            if guard is not None: self._json(guard[1], status=guard[0]); return
            self._json(_call_cap("virtual_wallet", "swap", body))

        elif path == "/api/wallet/deposit":
            guard = self._financial_guard(body)
            if guard is not None: self._json(guard[1], status=guard[0]); return
            self._json(_call_cap("virtual_wallet", "deposit_address", body))

        elif path == "/api/wallet/invoice":
            guard = self._financial_guard(body)
            if guard is not None: self._json(guard[1], status=guard[0]); return
            self._json(_call_cap("virtual_wallet", "invoice", body))

        elif path == "/api/wallet/pay":
            guard = self._financial_guard(body)
            if guard is not None: self._json(guard[1], status=guard[0]); return
            self._json(_call_cap("virtual_wallet", "pay_invoice", body))

        elif path == "/api/interest/deposit":
            guard = self._financial_guard(body)
            if guard is not None: self._json(guard[1], status=guard[0]); return
            self._json(_call_cap("interest_pool", "deposit", body))

        elif path == "/api/interest/withdraw":
            guard = self._financial_guard(body)
            if guard is not None: self._json(guard[1], status=guard[0]); return
            self._json(_call_cap("interest_pool", "withdraw", body))

        elif path == "/api/admin/freeze":
            guard = self._financial_guard(body)
            if guard is not None: self._json(guard[1], status=guard[0]); return
            self._json(_call_cap("platform_account", "sub_freeze", body))

        elif path == "/api/admin/ban":
            guard = self._financial_guard(body)
            if guard is not None: self._json(guard[1], status=guard[0]); return
            self._json(_call_cap("platform_account", "sub_ban", body))

        # ── 管理员端点: 严格认证(无body空/限流检查) ──
        elif path == "/api/admin/accounts":
            if not self._require_auth():
                self._json({"ok": False, "error": "需要管理员权限"}, status=401); return
            self._json(_call_cap("platform_account", "sub_list", body))

        elif path == "/api/admin/unfreeze":
            if not self._require_auth():
                self._json({"ok": False, "error": "需要管理员权限"}, status=401); return
            self._json(_call_cap("platform_account", "sub_unfreeze", body))

        elif path == "/api/admin/status":
            if not self._require_auth():
                self._json({"ok": False, "error": "需要管理员权限"}, status=401); return
            self._json(_call_cap("platform_account", "status", {}))

        elif path == "/api/wallet/admin":
            if not self._require_auth():
                self._json({"ok": False, "error": "管理员权限"}, status=401); return
            self._json(_call_cap("virtual_wallet", "admin_pool", {}))

        # ── 非金融/非管理员端点(无需认证) ──
        elif path == "/api/payment/check":
            self._json(_call_cap("payments", "webhook", {"source": "cryptapi", **body}))

        elif path == "/api/oauth/login":
            self._json(_call_cap("github_oauth", "login_url", body))

        elif path == "/api/oauth/exchange":
            self._json(_call_cap("github_oauth", "exchange", body))

        elif path == "/api/oauth/repos":
            action = body.get("action", "list_repos")
            if action == "browse":
                self._json(_call_cap("github_oauth", "browse", body, timeout=30))
            elif action == "read_file":
                self._json(_call_cap("github_oauth", "read_file", body, timeout=20))
            else:
                self._json(_call_cap("github_oauth", "list_repos", body))

        elif path == "/api/oauth/submit":
            result = _call_cap("github_oauth", "submit", body)
            if result.get("ok"):
                _call_cap("revenue_split", "record", {
                    "project": body.get("repo_name", ""),
                    "developer": body.get("developer", ""),
                    "hours": 0,
                    "rate": result.get("suggested_price_per_hour", 0.5)
                })
            self._json(result)

        elif path == "/api/deploy":
            project = body.get("project", "")
            if not project: self._json({"ok": False, "error": "缺少project参数"}); return
            result = {"ok": True, "project": project, "steps": []}
            pay_result = _call_cap("payments", "crypto", {
                "coin": body.get("coin", "USDT"), "amount": float(body.get("amount", 1.0)),
                "order_id": f"GBT-{project}-{int(__import__('time').time())}"
            })
            result["steps"].append({"step": "payment", "ok": pay_result.get("ok", False)})
            if pay_result.get("ok"):
                _call_cap("platform_account", "incoming", {
                    "amount": float(body.get("amount", 1.0)),
                    "user_id": body.get("developer", "marketplace"),
                })
                result["payment"] = pay_result
                result["steps"].append({"step": "platform_ledger", "ok": True})
            self._json(result)

        elif path == "/api/revenue/settle":
            self._json(_call_cap("platform_account", "distribute", body))

        elif path == "/api/interest/status":
            self._json(_call_cap("interest_pool", "status", {}))

        elif path == "/api/interest/ledger":
            user_id = body.get("user_id", "") if body else ""
            self._json(_call_cap("interest_pool", "ledger", {"user_id": user_id}))

        elif path == "/api/wallet/balance":
            self._json(_call_cap("virtual_wallet", "balance", body))
        elif path == "/api/wallet/rates":
            self._json(_call_cap("virtual_wallet", "rates", body))
        elif path == "/api/wallet/ledger":
            self._json(_call_cap("virtual_wallet", "ledger", body))

        elif path == "/api/ask":
            if body.get("image") or body.get("mode") == "vision":
                self._json(_call_cap("ai_service", "vision", body, timeout=60))
            else:
                self._json(_call_cap("ai_service", "chat", body))

        elif path == "/api/deploy/oneclick":
            repo_url = body.get("repo_url", "")
            mode = body.get("mode", "local")
            if not repo_url:
                self._json({"ok": False, "error": "缺少repo_url"}); return
            if mode == "remote":
                result = _call_cap("oneclick_deploy", "deploy_remote", {
                    "repo_url": repo_url,
                    "customer": body.get("customer", "anonymous"),
                }, timeout=600)
            else:
                result = _call_cap("oneclick_deploy", "deploy", {
                    "repo_url": repo_url,
                    "customer": body.get("customer", "anonymous"),
                }, timeout=300)
            self._json(result)

        elif path == "/api/deploy/tunnel-handshake":
            session_id = body.get("session_id", "")
            tunnel_url = body.get("tunnel_url", "")
            token = body.get("token", "")
            if not session_id or not tunnel_url:
                self._json({"ok": False, "error": "缺少session_id/tunnel_url"}); return
            import json as _j
            from pathlib import Path as _P
            tunnels_file = _P.home() / ".gbt" / "active_tunnels.json"
            tunnels_file.parent.mkdir(parents=True, exist_ok=True)
            tunnels = _j.loads(tunnels_file.read_text(encoding="utf-8")) if tunnels_file.exists() else {}
            tunnels[session_id] = {
                "tunnel_url": tunnel_url, "token": token,
                "hostname": body.get("hostname", ""),
                "platform": body.get("platform", ""),
                "created": __import__('time').time(),
            }
            tunnels_file.write_text(_j.dumps(tunnels, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"🔗 隧道已注册: {session_id} → {tunnel_url}", file=sys.stderr)
            self._json({"ok": True, "session_id": session_id, "message": "隧道已注册, GBT正在连接..."})

        elif path == "/api/suggest":
            self._json(_call_cap("ai_service", "suggest", body))

        # ── 眼睛API: 同步AI视觉能力到网站 ──
        elif path == "/api/eye/screenshot":
            self._json(_call_cap("ai_service", "screenshot", body, timeout=15))

        elif path == "/api/eye/see":
            self._json(_call_cap("omni_eye", body.get("action", "see"), body, timeout=15))

        elif path == "/api/eye/scan":
            self._json(_call_cap("local_eye", body.get("action", "scan"), body, timeout=15))

        elif path == "/api/eye/vision":
            self._json(_call_cap("ai_vision", body.get("action", "screen"), body, timeout=60))

        else:
            self._json({"ok": False, "error": "未知端点"}, status=404)

class ManagementHandler(BaseHTTPRequestHandler):
    """轻量级管理API — 外部监控/控制"""
    def log_message(self, *args): pass

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,Authorization")
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,Authorization")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/health":
            self._json({"ok": True, "status": "running", "server": "management_api", "version": "5.0"})

        elif path == "/status":
            result = _call_cap("gbt_brain", "status")
            self._json(result)

        elif path == "/logs/recent":
            self._recent_logs()

        else:
            self._json({"ok": False, "error": "未知端点"}, status=404)

    def do_POST(self):
        path = self.path.split("?")[0]

        if path.startswith("/trigger/"):
            parts = path.split("/")
            if len(parts) >= 4 and parts[2] and parts[3]:
                cap = parts[2]
                action = parts[3]
                length = int(self.headers.get("Content-Length", 0))
                try:
                    body = json.loads(self.rfile.read(length)) if length > 0 else {}
                except (json.JSONDecodeError, UnicodeDecodeError):
                    self._json({"ok": False, "error": "请求格式无效"}, status=400)
                    return
                timeout = body.pop("_timeout", 60) if isinstance(body, dict) else 60
                result = _call_cap(cap, action, body, timeout=timeout)
                self._json(result)
            else:
                self._json({"ok": False, "error": "格式: /trigger/{cap}/{action}"}, status=400)
        else:
            self._json({"ok": False, "error": "未知端点"}, status=404)

    def _recent_logs(self):
        """读取最近的日志/数据文件"""
        gbt_dir = Path.home() / ".gbt"
        files = []
        if gbt_dir.exists():
            for f in gbt_dir.rglob("*"):
                if f.is_file() and f.suffix in (".json", ".jsonl", ".log", ".md"):
                    try:
                        files.append((f.stat().st_mtime, f))
                    except OSError:
                        pass
        files.sort(key=lambda x: x[0], reverse=True)
        recent = []
        for _, f in files[:20]:
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                recent.append({
                    "file": str(f.relative_to(gbt_dir)),
                    "size": len(content),
                    "preview": content[:500],
                })
            except Exception:
                pass
        self._json({"ok": True, "files": len(recent), "logs": recent})

def do_serve(params=None):
    port = int((params or {}).get("port", PORT))
    host = (params or {}).get("host", "127.0.0.1")
    print(f"🌐 GBT Web API: http://{host}:{port}", file=sys.stderr)
    import logging
    logging.warning("CORS 已启用 * (允许所有来源) — 仅用于开发环境")
    print(f"   /api/health  /api/payment/*  /api/oauth/*  /api/deploy  /api/revenue/*  /api/leaderboard", file=sys.stderr)
    server = HTTPServer((host, port), APIHandler)
    try: server.serve_forever()
    except KeyboardInterrupt: server.shutdown()
    return {"ok": True, "stopped": True}



def do_list(params=None):
    """列出所有 API 端点"""
    return {
        "ok": True,
        "action": "list",
        "server": "GBT Web API",
        "port": PORT,
        "mgmt_port": PORT_MGMT,
        "endpoints": {
            "GET": [
                {"path": "/api/health", "desc": "服务健康检查", "auth": False},
                {"path": "/api/status", "desc": "GBT Brain 状态", "auth": False},
                {"path": "/api/caps", "desc": "能力模块列表", "auth": False},
                {"path": "/api/payment/coins", "desc": "支持的加密货币", "auth": False},
                {"path": "/api/help", "desc": "帮助文档", "auth": False},
                {"path": "/api/leaderboard", "desc": "排行榜", "auth": False},
                {"path": "/api/oauth/status", "desc": "OAuth 状态", "auth": True},
                {"path": "/api/revenue/stats", "desc": "收益统计", "auth": True},
                {"path": "/api/projects", "desc": "项目列表", "auth": True},
                {"path": "/api/nexus", "desc": "Nexus 监控", "auth": True},
            ],
            "POST": [
                {"path": "/api/payment/create", "desc": "创建支付", "auth": "financial"},
                {"path": "/api/payment/check", "desc": "支付回调", "auth": False},
                {"path": "/api/wallet/transfer", "desc": "钱包转账", "auth": "financial"},
                {"path": "/api/wallet/withdraw", "desc": "提现", "auth": "financial"},
                {"path": "/api/wallet/swap", "desc": "币种兑换", "auth": "financial"},
                {"path": "/api/wallet/deposit", "desc": "获取充值地址", "auth": "financial"},
                {"path": "/api/wallet/invoice", "desc": "创建发票", "auth": "financial"},
                {"path": "/api/wallet/pay", "desc": "支付发票", "auth": "financial"},
                {"path": "/api/wallet/balance", "desc": "查询余额", "auth": False},
                {"path": "/api/wallet/rates", "desc": "汇率查询", "auth": False},
                {"path": "/api/wallet/ledger", "desc": "账本查询", "auth": False},
                {"path": "/api/wallet/admin", "desc": "管理资金池", "auth": "admin"},
                {"path": "/api/interest/deposit", "desc": "利息存款", "auth": "financial"},
                {"path": "/api/interest/withdraw", "desc": "利息提取", "auth": "financial"},
                {"path": "/api/interest/status", "desc": "利息池状态", "auth": False},
                {"path": "/api/interest/ledger", "desc": "利息账本", "auth": False},
                {"path": "/api/admin/freeze", "desc": "冻结账户", "auth": "financial"},
                {"path": "/api/admin/ban", "desc": "封禁账户", "auth": "financial"},
                {"path": "/api/admin/accounts", "desc": "账户列表", "auth": "admin"},
                {"path": "/api/admin/unfreeze", "desc": "解冻账户", "auth": "admin"},
                {"path": "/api/admin/status", "desc": "平台状态", "auth": "admin"},
                {"path": "/api/oauth/login", "desc": "OAuth 登录", "auth": False},
                {"path": "/api/oauth/exchange", "desc": "OAuth 令牌交换", "auth": False},
                {"path": "/api/oauth/repos", "desc": "仓库操作", "auth": False},
                {"path": "/api/oauth/submit", "desc": "提交代码", "auth": False},
                {"path": "/api/deploy", "desc": "部署项目", "auth": False},
                {"path": "/api/deploy/oneclick", "desc": "一键部署", "auth": False},
                {"path": "/api/deploy/tunnel-handshake", "desc": "隧道注册", "auth": False},
                {"path": "/api/revenue/settle", "desc": "收益结算", "auth": False},
                {"path": "/api/ask", "desc": "AI 问答", "auth": False},
                {"path": "/api/suggest", "desc": "AI 建议", "auth": False},
                {"path": "/api/eye/screenshot", "desc": "屏幕截图", "auth": False},
                {"path": "/api/eye/see", "desc": "视觉识别", "auth": False},
                {"path": "/api/eye/scan", "desc": "屏幕扫描", "auth": False},
                {"path": "/api/eye/vision", "desc": "AI 视觉", "auth": False},
            ],
        },
        "actions": {
            "serve": "启动 API 服务器",
            "stop": "停止 API 服务器",
            "list": "本列表",
            "self_test": "核心组件自检",
            "help": "帮助信息 (同 list)",
        },
        "auth_modes": {
            "false": "无需认证",
            "true": "需要 Bearer token",
            "financial": "需要 Bearer token + 限流 + 幂等键",
            "admin": "需要管理员权限",
        },
    }


def do_self_test(params=None):
    """自检: 端口可用性 + 依赖检查"""
    results = {}

    # 1. JSON 模块
    try:
        json.dumps({})
        results["json_module"] = "ok"
    except Exception as e:
        results["json_module"] = f"fail: {e}"

    # 2. http.server 可用
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
        results["http_server"] = "ok"
    except Exception as e:
        results["http_server"] = f"fail: {e}"

    # 3. API_TOKEN 配置检查
    if API_TOKEN:
        results["api_token"] = "ok (已配置)"
    else:
        results["api_token"] = "warn: 未配置 (认证关闭)"

    # 4. 后端 cap 检查
    caps_to_check = ["gbt_brain", "devourer", "payments", "virtual_wallet",
                     "platform_account", "interest_pool", "github_oauth",
                     "ai_service", "oneclick_deploy", "omni_eye",
                     "local_eye", "ai_vision", "cryptapi_pay",
                     "revenue_split", "project_registry", "nexus_monitor",
                     "trending_scanner"]
    cap_results = {}
    for c in caps_to_check:
        try:
            r = _call_cap(c, "list", timeout=10)
            cap_results[c] = "ok" if r.get("ok") else f"warn: {r.get('error', 'unknown')}"
        except Exception as e:
            cap_results[c] = f"fail: {e}"
    results["backend_caps"] = cap_results

    # 5. wallet_safe 导入检查
    try:
        from wallet_safe import rate_check, safe_error
        results["wallet_safe"] = "ok"
    except Exception as e:
        results["wallet_safe"] = f"fail: {e}"

    # 6. subprocess 可用
    try:
        import subprocess as _sp
        results["subprocess"] = "ok"
    except Exception as e:
        results["subprocess"] = f"fail: {e}"

    # 7. 数据目录可写
    try:
        data_dir = Path.home() / ".gbt"
        data_dir.mkdir(parents=True, exist_ok=True)
        test_file = data_dir / ".web_api_write_test"
        test_file.write_text("test")
        test_file.unlink()
        results["data_dir_writable"] = "ok"
    except Exception as e:
        results["data_dir_writable"] = f"fail: {e}"

    cap_oks = sum(1 for v in cap_results.values() if v == "ok")
    cap_total = len(cap_results)
    all_ok = all(
        results.get(k) == "ok" or results.get(k, "").startswith("ok")
        for k in results if k != "backend_caps"
    )

    return {
        "ok": all_ok,
        "action": "self_test",
        "components": results,
        "backend_caps_summary": {"ok": cap_oks, "total": cap_total},
        "verdict": "PASS" if all_ok else "FAIL",
    }


do_help = do_list  # help 同 list

HANDLERS = {"serve": do_serve, "run": do_serve, "list": do_list, "self_test": do_self_test, "help": do_help}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "serve"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知:{action}"})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
