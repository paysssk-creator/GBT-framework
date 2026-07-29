# 开发者：自由的风
"""web_search/run.py — 全网搜索·三足鼎立数据源
=============================================
AI知识域 core — 真正的搜索返回结构化结果，不是跳转浏览器。
支持DuckDuckGo(免费)+ Google(备用)。供四脑推理调用。
"""
import sys, json, urllib.request, urllib.parse, urllib.error, re, html as _html

SANDBOX = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))


def _search_ddg(query, max_results=10):
    """DuckDuckGo HTML搜索(无需API key)"""
    results = []
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")

        # 解析DDG HTML结果
        result_blocks = re.findall(r'class="result__body">(.*?)</div>\s*</div>\s*</div>', body, re.DOTALL)
        for block in result_blocks[:max_results]:
            title_m = re.search(r'class="result__a"[^>]*>([^<]+)', block)
            link_m = re.search(r'class="result__url"[^>]*>([^<]+)', block)
            snippet_m = re.search(r'class="result__snippet"[^>]*>([^<]+(?:<[^>]+>[^<]*)*)', block)

            if title_m:
                title = _html.unescape(title_m.group(1).strip())
                link = _html.unescape(link_m.group(1).strip()) if link_m else ""
                snippet = _html.unescape(re.sub(r'<[^>]+>', '', snippet_m.group(1)).strip()) if snippet_m else ""

                results.append({
                    "title": title,
                    "url": link,
                    "snippet": snippet[:300],
                })

    except Exception as e:
        return [], str(e)[:100]

    return results, None


def _search_google_fallback(query, max_results=5):
    """Google搜索降级方案"""
    results = []
    try:
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num={max_results}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")

        blocks = re.findall(r'<div class="g".*?<a href="([^"]+)"[^>]*>\s*<h3[^>]*>([^<]+)', body, re.DOTALL)
        for url, title in blocks[:max_results]:
            results.append({
                "title": _html.unescape(re.sub(r'<[^>]+>', '', title).strip()),
                "url": url,
                "snippet": "",
            })
    except Exception:
        pass
    return results, None


def do_search(params):
    """全网搜索 — 返回结构化结果"""
    query = params.get("query", params.get("q", ""))
    if not query:
        return {"ok": False, "error": "缺少 query 参数"}

    max_results = params.get("max_results", params.get("limit", 10))
    engine = params.get("engine", "ddg")

    if engine == "ddg":
        results, err = _search_ddg(query, max_results)
        if not results:
            results, err2 = _search_google_fallback(query, max_results)
            if err2 and not results:
                return {"ok": False, "error": f"搜索失败: ddg={err}, google={err2}"}
    else:
        results, err = _search_google_fallback(query, max_results)
        if not results:
            return {"ok": False, "error": f"搜索失败: {err}"}

    # 提取核心知识点(去重+排序)
    keywords = set()
    for r in results:
        for word in re.findall(r'[A-Z][a-z]{2,}', r.get("title", "") + " " + r.get("snippet", "")):
            if len(word) > 3:
                keywords.add(word)

    return {
        "ok": True,
        "cap": "web_search",
        "action": "search",
        "domain": "AI知识",
        "query": query,
        "engine": engine,
        "total_results": len(results),
        "results": results,
        "core_keywords": list(keywords)[:20],
        "source": "duckduckgo" if engine == "ddg" else "google",
    }


HANDLERS = {"search": do_search}

if __name__ == "__main__":
    action = __import__("sys").argv[1] if len(__import__("sys").argv) > 1 and not __import__("sys").argv[1].startswith("-") else "search"
    params_str = __import__("sys").argv[2] if len(__import__("sys").argv) > 2 else "{}"
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
