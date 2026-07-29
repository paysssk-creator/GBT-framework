# 开发者：自由的风
"""trending_scanner/run.py — GitHub Trending实时排行榜
=====================================================
每日抓取GitHub Trending → 存入project_registry → 排行榜展示
"""
import sys, json, os, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone, timedelta

SANDBOX = Path(__file__).parent.parent
CACHE_FILE = Path.home() / ".gbt" / "trending_cache.json"
LANGUAGES = ["", "python", "javascript", "typescript", "go", "rust", "java"]

def _github_api(path, timeout=15):
    """GitHub API请求"""
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "GBT-trending-scanner"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        req = urllib.request.Request(f"https://api.github.com{path}", headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode()), None
    except Exception as e:
        return None, str(e)[:200]

def _fetch_trending(language="", days=1, per_page=15):
    """抓取GitHub趋势: 最近N天创建/更新的高星仓库"""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    lang_filter = f"+language:{language}" if language else ""
    query = f"created:>={since}{lang_filter}"
    path = f"/search/repositories?q={urllib.parse.quote(query)}&sort=stars&order=desc&per_page={per_page}"
    data, err = _github_api(path)
    if err:
        return [], err
    items = data.get("items", [])
    return [{
        "name": r["full_name"],
        "url": r["html_url"],
        "stars": r["stargazers_count"],
        "forks": r["forks_count"],
        "language": r.get("language", "?"),
        "description": (r.get("description") or "无描述")[:200],
        "topics": r.get("topics", [])[:5],
        "created": r["created_at"][:10],
        "updated": r["updated_at"][:10],
        "score": r["stargazers_count"] + r["forks_count"] * 2,
        "source": "github_trending",
    } for r in items], None

def do_scan(params=None):
    """全量扫描 — 所有主流语言 + 综合排行"""
    lang = (params or {}).get("language", "")
    days = int((params or {}).get("days", 1))
    per_page = int((params or {}).get("per_page", 20))

    if lang:
        repos, err = _fetch_trending(lang, days, per_page)
        if err:
            return {"ok": False, "error": err}
        return {"ok": True, "language": lang, "count": len(repos), "repos": repos}

    all_repos = []
    errors = []
    for lg in LANGUAGES:
        repos, err = _fetch_trending(lg, days, 10)
        if err:
            errors.append(f"{lg or 'all'}:{err}")
        else:
            for r in repos:
                r["category"] = lg or "all"
            all_repos.extend(repos)

    # 按score排序去重
    seen = set()
    unique = []
    for r in sorted(all_repos, key=lambda x: x["score"], reverse=True):
        if r["name"] not in seen:
            seen.add(r["name"])
            unique.append(r)

    # 缓存
    cache = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "scanned_languages": len(LANGUAGES),
        "total_unique": len(unique),
        "repos": unique,
    }
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

    # 同步到project_registry
    try:
        import subprocess
        from contextlib import suppress
        for r in unique[:30]:
            with suppress(Exception):
                subprocess.run([
                    sys.executable, str(SANDBOX / "project_registry" / "run.py"), "register",
                    json.dumps({
                        "name": r["name"],
                        "stars": r["stars"],
                        "language": r["language"],
                        "description": r["description"],
                        "url": r["url"],
                        "source": "trending",
                    })
                ], capture_output=True, timeout=10)
    except Exception:
        pass

    return {
        "ok": True,
        "action": "scan",
        "scanned": len(LANGUAGES),
        "found": len(unique),
        "errors": errors[:3] if errors else [],
        "top10": unique[:10],
        "cache": str(CACHE_FILE),
    }

def do_leaderboard(params=None):
    """返回排行榜 — 从缓存读取"""
    limit = int((params or {}).get("limit", 20))
    language = (params or {}).get("language", "")

    if CACHE_FILE.exists():
        cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        repos = cache["repos"]
        if language:
            repos = [r for r in repos if r.get("category") == language or r.get("language") == language]
        return {
            "ok": True,
            "updated": cache["updated"],
            "total": len(repos),
            "leaderboard": repos[:limit],
        }

    # 无缓存 → 实时扫描
    return do_scan({"language": language, "per_page": limit})

def do_refresh(params=None):
    """强制刷新 — 清除缓存重新扫描"""
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
    return do_scan(params)

HANDLERS = {"scan": do_scan, "leaderboard": do_leaderboard, "refresh": do_refresh, "list": do_leaderboard}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "leaderboard"
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except Exception:
            pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
