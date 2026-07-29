# 开发者：自由的风
"""subdomain_enum/run.py — DNS子域名枚举 + 证书透明度 + 源码层关联
================================================================
侦察域 core — 不止枚举子域名，还通过证书透明度日志、DNS记录分析
推断目标技术栈和架构薄弱面。
"""
import sys, json, os, socket, ssl, concurrent.futures, re, time
from urllib.request import urlopen, Request

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 常用子域名字典(精选100个高价值)
SUBDOMAIN_WORDLIST = [
    "www", "mail", "ftp", "admin", "api", "dev", "test", "staging",
    "blog", "shop", "cdn", "static", "media", "docs", "wiki", "portal",
    "vpn", "remote", "gateway", "proxy", "auth", "login", "sso", "oauth",
    "db", "sql", "mysql", "pg", "mongo", "redis", "elastic", "kibana",
    "grafana", "prometheus", "jenkins", "gitlab", "github", "git",
    "docker", "k8s", "kubernetes", "swarm", "registry", "nexus",
    "monitor", "status", "health", "metrics", "logs", "logging",
    "backup", "backups", "snapshot", "archive", "storage", "files",
    "upload", "download", "assets", "images", "img", "video", "videos",
    "webmail", "smtp", "imap", "pop", "ns1", "ns2", "dns", "nameserver",
    "firewall", "fw", "security", "secure", "ssl", "cert",
    "cpanel", "whm", "plesk", "webmin", "phpmyadmin", "adminer",
    "jira", "confluence", "bitbucket", "slack", "chat", "forum",
    "help", "support", "ticket", "service", "services", "api-docs",
    "swagger", "graphql", "rest", "soap", "ws", "websocket",
    "mobile", "m", "app", "apps", "beta", "alpha", "sandbox", "demo",
    "legacy", "old", "new", "v1", "v2", "v3",
]


def _dns_lookup(hostname):
    """DNS A记录查询"""
    try:
        return socket.getaddrinfo(hostname, None, socket.AF_INET)
    except (socket.gaierror, socket.herror):
        return None


def _cert_transparency(domain):
    """通过crt.sh查询证书透明度日志"""
    results = set()
    try:
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        req = Request(url, headers={"User-Agent": "GBT-Neighborhood-Recon/5.0"})
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for entry in data[:200]:
                names = entry.get("name_value", "").split("\n")
                for name in names:
                    name = name.strip().lower().lstrip("*.")
                    if name.endswith(domain) and name != domain:
                        results.add(name)
    except Exception:
        pass
    return list(results)


def do_enum(params):
    """枚举子域名(DNS爆破 + 证书透明度)"""
    domain = params.get("domain", params.get("target", ""))
    if not domain:
        return {"ok": False, "error": "缺少 domain 参数"}

    domain = domain.lower().strip().replace("http://", "").replace("https://", "").rstrip("/")

    wordlist = params.get("wordlist", SUBDOMAIN_WORDLIST)
    threads = params.get("threads", 20)
    use_cert = params.get("cert_transparency", True)

    results = []
    alive = []

    # ① DNS爆破
    def check_subdomain(sub):
        hostname = f"{sub}.{domain}"
        ips = _dns_lookup(hostname)
        if ips:
            ip_list = list(set(addr[4][0] for addr in ips))
            return {"subdomain": hostname, "ips": ip_list, "source": "dns_brute"}
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(check_subdomain, sub): sub for sub in wordlist}
        for f in concurrent.futures.as_completed(futures):
            r = f.result()
            if r:
                results.append(r)
                alive.append(r)

    # ② 证书透明度
    if use_cert:
        try:
            cert_subs = _cert_transparency(domain)
            for sub in cert_subs:
                if sub not in [r["subdomain"] for r in results]:
                    ips = _dns_lookup(sub)
                    ip_list = list(set(addr[4][0] for addr in ips)) if ips else []
                    r = {"subdomain": sub, "ips": ip_list, "source": "cert_transparency"}
                    results.append(r)
                    if ip_list:
                        alive.append(r)
        except Exception:
            pass

    # ③ 架构面分析 — 从子域名模式推断薄弱点
    weakness_hints = []
    subdomain_patterns = {
        r"\b(dev|test|staging|sandbox|beta|alpha)\b": ("存在开发/测试环境", "测试环境通常安全配置较弱"),
        r"\b(admin|administrator|root)\b": ("管理后台暴露", "管理入口应做IP白名单"),
        r"\b(db|sql|mysql|pg|mongo|redis)\b": ("数据库服务暴露在子域名", "严重: 数据库不应直接暴露"),
        r"\b(gitlab|jenkins|nexus|registry|docker)\b": ("DevOps工具暴露", "CI/CD平台应做访问控制"),
        r"\b(grafana|kibana|prometheus)\b": ("监控面板暴露", "监控应限制内网访问"),
        r"\b(phpmyadmin|adminer|webmin|cpanel)\b": ("管理工具暴露", "严重: 管理面板应内网限制"),
        r"\b(api|graphql|rest|swagger)\b": ("API端点暴露", "检查API鉴权+限流"),
    }

    for r in alive:
        for pattern, (label, suggestion) in subdomain_patterns.items():
            if re.search(pattern, r["subdomain"]):
                weakness_hints.append({
                    "subdomain": r["subdomain"],
                    "finding": label,
                    "suggestion": suggestion,
                })

    return {
        "ok": True,
        "cap": "subdomain_enum",
        "action": "enum",
        "domain": "侦察域",
        "target": domain,
        "total_found": len(results),
        "alive_count": len(alive),
        "dns_brute_count": sum(1 for r in results if r.get("source") == "dns_brute"),
        "cert_transparency_count": sum(1 for r in results if r.get("source") == "cert_transparency"),
        "subdomains": [r["subdomain"] for r in results],
        "alive_details": alive,
        "weakness_hints": weakness_hints,
        "weakness_count": len(weakness_hints),
    }


def do_brute(params):
    """暴力枚举子域名(使用自定义字典)"""
    return do_enum({**params, "cert_transparency": False})


HANDLERS = {"enum": do_enum, "brute": do_brute}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "enum"
    params_str = sys.argv[2] if len(sys.argv) > 2 else "{}"
    try:
        params = json.loads(params_str)
    except Exception:
        params = {}
    handler = HANDLERS.get(action)
    if handler:
        result = handler(params)
        print(json.dumps(result, ensure_ascii=False, default=str))
    else:
        print(json.dumps({"ok": False, "error": f"未知动作: {action}", "available": list(HANDLERS.keys())}, ensure_ascii=False))
