# 开发者：自由的风
"""dir_buster/run.py — 目录/文件爆破扫描 + 源码层分析
===================================================
侦察域 ready — 爆破网站目录/文件，从响应中推断技术栈和薄弱点。
"""
import sys, json, os, urllib.request, urllib.error, concurrent.futures, re

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 高价值路径字典(精选)
DIR_WORDLIST = [
    # 敏感文件
    ".git/HEAD", ".env", ".env.backup", ".env.example",
    "config.php", "config.php.bak", "config.yml", "config.json",
    "wp-config.php", "wp-config.php.bak",
    "backup.zip", "backup.sql", "dump.sql", "database.sql",
    "admin", "administrator", "login", "wp-admin", "phpmyadmin",
    # API/调试
    "api", "api/v1", "graphql", "swagger", "api-docs",
    "debug", "phpinfo.php", "info.php", "test.php",
    "actuator", "actuator/health", "actuator/env",
    # 版本控制
    ".git/config", ".svn/entries", ".DS_Store",
    "robots.txt", "sitemap.xml", "crossdomain.xml",
    # 常见框架路径
    "wp-content", "wp-includes", "wp-json",
    "sites/default/settings.php",  # Drupal
    "app/etc/local.xml",           # Magento
    "vendor/autoload.php",         # Composer
    "node_modules", "package.json",
    "WEB-INF/web.xml",             # Java
    # 备份
    "backup", "backups", "old", "temp", "tmp",
    "upload", "uploads", "files", "assets",
]


def _check_path(base_url, path, timeout=8):
    """检查单个路径"""
    url = base_url.rstrip("/") + "/" + path.lstrip("/")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GBT-DirBuster/5.0"})
        resp = urllib.request.urlopen(req, timeout=timeout)
        body = resp.read().decode("utf-8", errors="replace")[:500]
        return {
            "url": url,
            "status": resp.status,
            "size": len(body),
            "content_type": resp.headers.get("Content-Type", ""),
            "body_preview": body[:200],
        }
    except urllib.error.HTTPError as e:
        if e.code in (403, 401):
            return {"url": url, "status": e.code, "note": "存在但需认证"}
        return None
    except Exception:
        return None


def do_scan(params):
    """目录爆破扫描"""
    url = params.get("url", params.get("target", ""))
    if not url:
        return {"ok": False, "error": "缺少 url 参数"}
    if not url.startswith("http"):
        url = "http://" + url

    wordlist = params.get("wordlist", DIR_WORDLIST)
    threads = params.get("threads", 15)

    found = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(_check_path, url, path): path for path in wordlist}
        for f in concurrent.futures.as_completed(futures):
            r = f.result()
            if r:
                found.append(r)

    found.sort(key=lambda x: (x["status"], -x.get("size", 0)))

    # 源码层分析
    weaknesses = []
    for f in found:
        body = f.get("body_preview", "")
        if f["url"].endswith(".env") and f["status"] == 200:
            weaknesses.append({"finding": ".env文件可访问", "severity": "critical",
                              "detail": "环境变量泄露(数据库密码/API密钥)"})
        if ".git" in f["url"] and f["status"] == 200:
            weaknesses.append({"finding": "Git仓库暴露", "severity": "critical",
                              "detail": "源码可被下载"})
        if "phpinfo" in body.lower():
            weaknesses.append({"finding": "phpinfo()暴露", "severity": "critical",
                              "detail": "PHP配置信息完全泄露"})
        if "debug" in body.lower() and "true" in body.lower():
            weaknesses.append({"finding": "Debug模式开启", "severity": "high"})

    return {
        "ok": True,
        "cap": "dir_buster",
        "action": "scan",
        "domain": "侦察域",
        "url": url,
        "paths_checked": len(wordlist),
        "found_count": len(found),
        "found": found,
        "weaknesses": weaknesses,
        "weakness_count": len(weaknesses),
    }


def do_brute(params):
    return do_scan(params)


HANDLERS = {"scan": do_scan, "brute": do_brute}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "scan"
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
