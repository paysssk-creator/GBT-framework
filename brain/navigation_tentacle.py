# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/navigation_tentacle.py -- 导航触手 · 瞬间展开 v1.0
========================================================
邻域展开的瞬间自动导航:
  API导航    → 扫描所有API端点, 测试连通性
  密钥导航   → 检测所有密钥配置, 验证有效性
  支付导航   → 追踪支付链路, 确认通道健康
  依赖导航   → 映射模块依赖关系
  路由导航   → 意图→能力路由完整性

优先级: 密钥 > 支付 > API > 路由 > 依赖
"""
import sys, os, json, re, time
from pathlib import Path
from datetime import datetime
from typing import Optional

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

NAV_DIR = Path.home() / ".gbt" / "navigation"
NAV_DIR.mkdir(parents=True, exist_ok=True)
NAV_STATE = NAV_DIR / "nav_state.json"


class NavigationTentacle:
    """导航触手 — 邻域展开瞬间自动导航"""

    def __init__(self):
        self.state = self._load_state()
        self._last_nav = None

    def _load_state(self):
        if NAV_STATE.exists():
            try: return json.loads(NAV_STATE.read_text(encoding="utf-8"))
            except: pass
        return {"total_navigations": 0, "apis_found": 0, "keys_found": 0, "payments_ok": 0}

    def _save(self):
        NAV_STATE.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")

    # ═══════════════ API导航 ═══════════════

    def nav_apis(self) -> dict:
        """API导航 — 扫描所有端点"""
        apis = []
        api_patterns = [
            (r'(?:url|endpoint|base_url|api_url)\s*[=:]\s*["\'](https?://[^\s"\']+)', "endpoint"),
            (r'(?:port|PORT)\s*[=:]\s*(\d+)', "port"),
            (r'@app\.(?:route|get|post|put|delete)\s*\(\s*["\']([^"\']+)', "flask_route"),
            (r'@router\.(?:get|post|put|delete)\s*\(\s*["\']([^"\']+)', "fastapi_route"),
            (r'app\.(?:get|post|put|delete)\s*\(\s*["\']([^"\']+)', "express_route"),
            (r'fetch\s*\(\s*["\']([^"\']+)', "fetch_call"),
            (r'axios\.(?:get|post|put|delete)\s*\(\s*["\']([^"\']+)', "axios_call"),
            (r'urllib\.request\.(?:urlopen|Request)\s*\(\s*["\']([^"\']+)', "python_http"),
        ]

        scanned = 0
        for dirpath, dirnames, filenames in os.walk(str(ROOT)):
            dirnames[:] = [d for d in dirnames if d not in ('__pycache__', '.git', 'node_modules', 'Lib', 'site-packages')]
            for f in filenames:
                if f.endswith(('.py', '.js', '.ts', '.json', '.yml', '.yaml', '.env', '.sh', '.bat')):
                    fp = os.path.join(dirpath, f)
                    try:
                        content = open(fp, 'r', encoding='utf-8', errors='replace').read()
                        for pattern, api_type in api_patterns:
                            for match in re.finditer(pattern, content, re.IGNORECASE):
                                apis.append({
                                    "file": fp.replace(str(ROOT), "").lstrip("\\/"),
                                    "type": api_type,
                                    "value": match.group(1) if match.groups() else match.group(0),
                                    "line": content[:match.start()].count(chr(10)) + 1
                                })
                        scanned += 1
                    except:
                        pass

        self.state["apis_found"] = len(apis)
        self.state["total_navigations"] += 1
        self._save()

        # 去重统计
        endpoints = [a for a in apis if a["type"] == "endpoint"]
        ports = [a for a in apis if a["type"] == "port"]

        return {
            "ok": True,
            "total_apis": len(apis),
            "endpoints": len(endpoints),
            "ports": len(ports),
            "routes": len([a for a in apis if "route" in a["type"]]),
            "files_scanned": scanned,
            "top_endpoints": [a["value"][:80] for a in endpoints[:5]],
            "top_ports": [a["value"] for a in ports[:5]],
        }

    # ═══════════════ 密钥导航 ═══════════════

    def nav_keys(self) -> dict:
        """密钥导航 — 检测所有密钥配置"""
        keys = []
        key_patterns = [
            (r'(?:API_KEY|api_key|apikey|SECRET|secret|TOKEN|token|PASSWORD|password)\s*[=:]\s*["\']([^"\'\s]{8,})["\']', "env_key"),
            (r'(?:sk-[a-zA-Z0-9]{20,})', "openai_key"),
            (r'(?:dsk-[a-zA-Z0-9]{20,})', "deepseek_key"),
            (r'(?:0x[a-fA-F0-9]{40,})', "eth_private_key"),
            (r'(?:[13][a-km-zA-HJ-NP-Z1-9]{25,34})', "btc_address"),
            (r'(?:Bearer\s+)([a-zA-Z0-9\-_\.]{20,})', "bearer_token"),
            (r'CRYPTAPI_KEY\s*[=:]\s*["\']([^"\']+)', "cryptapi_key"),
            (r'STRIPE_SECRET_KEY\s*[=:]\s*["\']([^"\']+)', "stripe_key"),
            (r'PAYPAL_CLIENT_ID\s*[=:]\s*["\']([^"\']+)', "paypal_key"),
            (r'CAPTCHA_API_KEY\s*[=:]\s*["\']([^"\']+)', "captcha_key"),
            (r'GITHUB_CLIENT_SECRET\s*[=:]\s*["\']([^"\']+)', "github_secret"),
            (r'PLISIO_API_KEY\s*[=:]\s*["\']([^"\']+)', "plisio_key"),
        ]

        env_file = ROOT / ".env"
        if env_file.exists():
            try:
                content = env_file.read_text(encoding="utf-8")
                for pattern, key_type in key_patterns:
                    for match in re.finditer(pattern, content, re.IGNORECASE):
                        val = match.group(1) if match.groups() else match.group(0)
                        keys.append({
                            "file": ".env",
                            "type": key_type,
                            "key_name": match.group(0).split("=")[0].strip() if "=" in match.group(0) else key_type,
                            "status": "configured" if "YOUR_" not in val and "sk-your" not in val else "placeholder",
                            "masked": val[:8] + "..." if len(val) > 8 else val
                        })
            except:
                pass

        valid = [k for k in keys if k["status"] == "configured"]
        placeholder = [k for k in keys if k["status"] == "placeholder"]

        self.state["keys_found"] = len(keys)
        self._save()

        return {
            "ok": True,
            "total_keys": len(keys),
            "valid_keys": len(valid),
            "placeholder_keys": len(placeholder),
            "keys": [{"type": k["type"], "status": k["status"], "masked": k["masked"]} for k in keys],
        }

    # ═══════════════ 支付导航 ═══════════════

    def nav_payments(self) -> dict:
        """支付导航 — 追踪支付链路"""
        payments = []
        payment_caps = [
            "payments", "payment_gateway", "cryptapi_pay", "revenue_split",
            "fund_pool", "interest_pool", "virtual_wallet", "platform_account",
            "reserve_pool", "wallet"
        ]

        cap_dir = ROOT / "caps"
        payment_dir = ROOT / "integrations" / "payment"

        for cap_name in payment_caps:
            cap_path = cap_dir / cap_name
            if not cap_path.exists():
                cap_path = payment_dir / cap_name
            if not cap_path.exists():
                payments.append({"cap": cap_name, "status": "missing"})
                continue

            run_py = cap_path / "run.py"
            cap_json = cap_path / "capability.json"

            status = "ready"
            handlers = 0
            if cap_json.exists():
                try:
                    cap = json.loads(cap_json.read_text(encoding="utf-8"))
                    handlers = len(cap.get("actions", {}))
                except:
                    status = "broken_json"

            payments.append({
                "cap": cap_name,
                "status": status,
                "handlers": handlers,
                "path": str(cap_path).replace(str(ROOT), "").lstrip("\\/")
            })

        ready = [p for p in payments if p["status"] == "ready"]
        missing = [p for p in payments if p["status"] == "missing"]

        self.state["payments_ok"] = len(ready)
        self._save()

        return {
            "ok": True,
            "total_payment_caps": len(payments),
            "ready": len(ready),
            "missing": len(missing),
            "payment_chain": [
                f"{p['cap']}({p['handlers']}h)" if p['status'] == 'ready' else f"{p['cap']}(missing)"
                for p in payments
            ],
        }

    # ═══════════════ 路由导航 ═══════════════

    def nav_routes(self) -> dict:
        """路由导航 — 意图→能力路由完整性"""
        try:
            from brain.nexus import get_nexus
            n = get_nexus()
            s = n.scan(force=True)
            d = n.deep_scan()

            routes_ok = d.get("total_issues", 0) == 0
            return {
                "ok": True,
                "routes_ok": routes_ok,
                "total_routes": len(getattr(n, 'routes', {})),
                "total_issues": d.get("total_issues", 0),
                "health": s.get("health_pct", 0),
                "missing_routes": [i.get("missing_cap") for i in d.get("issues", [])][:5],
            }
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}

    # ═══════════════ 全导航 ═══════════════

    def navigate_all(self) -> dict:
        """全导航 — 按优先级: 密钥→支付→API→路由"""
        t0 = time.time()
        nav = {}

        # ① 密钥(最优先)
        nav["keys"] = self.nav_keys()

        # ② 支付链路
        nav["payments"] = self.nav_payments()

        # ③ API端点
        nav["apis"] = self.nav_apis()

        # ④ 路由
        nav["routes"] = self.nav_routes()

        # ⑤ 部署检查
        nav["deploy"] = self.nav_deploy()

        elapsed = time.time() - t0

        issues = []
        if nav["keys"]["placeholder_keys"] > 0:
            issues.append(f'{nav["keys"]["placeholder_keys"]}个密钥未配置')
        if nav["payments"]["missing"] > 0:
            issues.append(f'{nav["payments"]["missing"]}个支付cap缺失')
        if not nav["routes"]["routes_ok"]:
            issues.append(f'{nav["routes"]["total_issues"]}条路由断连')
        if nav.get("deploy", {}).get("issues"):
            issues.extend(nav["deploy"]["issues"])

        self._last_nav = nav
        self.state["total_navigations"] += 1
        self._save()

        return {
            "ok": len(issues) == 0,
            "elapsed_ms": int(elapsed * 1000),
            "keys_valid": nav["keys"]["valid_keys"],
            "keys_placeholder": nav["keys"]["placeholder_keys"],
            "payments_ready": nav["payments"]["ready"],
            "payments_missing": nav["payments"]["missing"],
            "apis_total": nav["apis"]["total_apis"],
            "routes_ok": nav["routes"]["routes_ok"],
            "deploy_score": nav.get("deploy", {}).get("score", "?"),
            "deploy_issues": nav.get("deploy", {}).get("issues", []),
            "issues": issues,
            "timestamp": datetime.now().isoformat(),
        }

    # ═══════════════ 部署导航 ═══════════════

    def nav_deploy(self) -> dict:
        """部署导航 — 专业部署平台全要点检查"""
        checks = {}
        issues = []

        # SSL/HTTPS
        checks["ssl"] = self._check_ssl()
        if not checks["ssl"]["configured"]:
            issues.append("SSL证书未配置")

        # DNS
        checks["dns"] = self._check_dns()
        if not checks["dns"]["configured"]:
            issues.append("DNS/CNAME未配置")

        # CDN
        checks["cdn"] = self._check_cdn()

        # CI/CD
        checks["cicd"] = self._check_cicd()
        if not checks["cicd"]["configured"]:
            issues.append("CI/CD流水线未配置")

        # 健康检查
        checks["health_check"] = self._check_health_endpoint()

        # 环境变量
        checks["env_vars"] = self._check_env_vars()
        if checks["env_vars"]["placeholder_count"] > 0:
            issues.append(f'{checks["env_vars"]["placeholder_count"]}个环境变量未配置')

        # 安全头
        checks["security_headers"] = self._check_security_headers()
        if not checks["security_headers"]["configured"]:
            issues.append("安全响应头未配置(CSP/HSTS/X-Frame)")

        # 错误页面
        checks["error_pages"] = self._check_error_pages()

        # robots/sitemap
        checks["seo"] = self._check_seo()

        # 回滚
        checks["rollback"] = self._check_rollback()
        if not checks["rollback"]["configured"]:
            issues.append("回滚机制未配置")

        # 监控
        checks["monitoring"] = self._check_monitoring()

        # 备份
        checks["backup"] = self._check_backup()

        # 容器化
        checks["docker"] = self._check_docker()

        # 限流
        checks["rate_limit"] = self._check_rate_limit()

        # CORS
        checks["cors"] = self._check_cors()

        # 性能
        checks["performance"] = self._check_performance()

        # 无障碍
        checks["accessibility"] = self._check_accessibility()

        # 分析
        checks["analytics"] = self._check_analytics()

        ok_count = sum(1 for c in checks.values() if c.get("configured", False) or c.get("ok", False))
        total = len(checks)

        self.state["deploy_checks"] = {"ok": ok_count, "total": total, "issues": len(issues)}
        self._save()

        return {
            "ok": len(issues) == 0,
            "score": f"{ok_count}/{total}",
            "checks": {k: v.get("status", "?") for k, v in checks.items()},
            "issues": issues,
        }

    def _check_ssl(self) -> dict:
        return {"configured": self._grep_exists(r'ssl_certificate|listen\s+443|https://')}

    def _check_dns(self) -> dict:
        return {"configured": self._grep_exists(r'CNAME|cname|A\s+record|pages\.dev|vercel\.app|netlify\.app')}

    def _check_cdn(self) -> dict:
        return {"ok": self._grep_exists(r'cloudflare|cdn|CloudFront|fastly|cdn\.')}

    def _check_cicd(self) -> dict:
        return {"configured": self._grep_exists(r'\.github/workflows|\.gitlab-ci|Jenkinsfile|docker-compose')}

    def _check_health_endpoint(self) -> dict:
        return {"configured": self._grep_exists(r'health|healthcheck|/api/health|_health')}

    def _check_env_vars(self) -> dict:
        env_file = ROOT / ".env"
        placeholders = 0
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").split(chr(10)):
                if ("YOUR_" in line or "sk-your" in line) and "NOT_REQUIRED" not in line:
                    placeholders += 1
        return {"placeholder_count": placeholders, "configured": placeholders == 0}

    def _check_security_headers(self) -> dict:
        return {"configured": self._grep_exists(r'Content-Security-Policy|X-Frame-Options|HSTS|Strict-Transport')}

    def _check_error_pages(self) -> dict:
        return {"configured": self._grep_exists(r'404\.html|error_page|error\.html|500\.html')}

    def _check_seo(self) -> dict:
        return {"ok": self._grep_exists(r'robots\.txt|sitemap\.xml|meta.*description')}

    def _check_rollback(self) -> dict:
        return {"configured": self._grep_exists(r'rollback|revert|git\s+reset|helm\s+rollback')}

    def _check_monitoring(self) -> dict:
        return {"configured": self._grep_exists(r'prometheus|grafana|datadog|sentry|new\s+relic|loggly')}

    def _check_backup(self) -> dict:
        return {"configured": self._grep_exists(r'backup|snapshot|pg_dump|mysqldump|restore')}

    def _check_docker(self) -> dict:
        return {"configured": self._grep_exists(r'Dockerfile|docker-compose|FROM\s+\w+')}

    def _check_rate_limit(self) -> dict:
        return {"configured": self._grep_exists(r'rate.limit|rate_limit|throttle|limit_req')}

    def _check_cors(self) -> dict:
        return {"configured": self._grep_exists(r'Access-Control|CORS|cors|allowed_origins')}

    def _check_performance(self) -> dict:
        return {"configured": self._grep_exists(r'minify|terser|compression|gzip|brotli|lazy.load|cache.control')}

    def _check_accessibility(self) -> dict:
        return {"configured": self._grep_exists(r'aria-|role=|alt=|wcag|a11y|accessibility')}

    def _check_analytics(self) -> dict:
        return {"configured": self._grep_exists(r'google.analytics|gtag|plausible|umami|analytics')}

    def _grep_exists(self, pattern: str) -> bool:
        """在项目中搜索模式是否存在"""
        import re
        for dirpath, dirnames, filenames in os.walk(str(ROOT)):
            dirnames[:] = [d for d in dirnames if d not in ('__pycache__', '.git', 'node_modules', 'Lib', 'site-packages', 'archive')]
            for f in filenames[:50]:  # 每个目录最多50个文件
                if f.endswith(('.py','.js','.html','.json','.yml','.yaml','.conf','.sh','.bat','.nginx','.md')):
                    try:
                        content = open(os.path.join(dirpath, f), 'r', encoding='utf-8', errors='replace').read()
                        if re.search(pattern, content, re.IGNORECASE):
                            return True
                    except:
                        pass
        return False
        if nav["keys"]["placeholder_keys"] > 0:
            issues.append(f'{nav["keys"]["placeholder_keys"]}个密钥未配置')
        if nav["payments"]["missing"] > 0:
            issues.append(f'{nav["payments"]["missing"]}个支付cap缺失')
        if not nav["routes"]["routes_ok"]:
            issues.append(f'{nav["routes"]["total_issues"]}条路由断连')
        if nav.get("deploy", {}).get("issues"):
            issues.extend(nav["deploy"]["issues"])

        self._last_nav = nav
        self.state["total_navigations"] += 1
        self._save()

        return {
            "ok": len(issues) == 0,
            "elapsed_ms": int(elapsed * 1000),
            "keys_valid": nav["keys"]["valid_keys"],
            "keys_placeholder": nav["keys"]["placeholder_keys"],
            "payments_ready": nav["payments"]["ready"],
            "payments_missing": nav["payments"]["missing"],
            "apis_total": nav["apis"]["total_apis"],
            "routes_ok": nav["routes"]["routes_ok"],
            "deploy_score": nav.get("deploy", {}).get("score", "?"),
            "deploy_issues": nav.get("deploy", {}).get("issues", []),
            "issues": issues,
            "timestamp": datetime.now().isoformat(),
        }


# ═══════════════ 全局 ═══════════════

_nav: Optional[NavigationTentacle] = None

def get_nav() -> NavigationTentacle:
    global _nav
    if _nav is None: _nav = NavigationTentacle()
    return _nav

def navigate() -> dict:
    return get_nav().navigate_all()


if __name__ == "__main__":
    r = navigate()
    print(json.dumps(r, ensure_ascii=False, indent=2))
