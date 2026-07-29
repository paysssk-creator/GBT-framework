# 开发者：自由的风
"""agent_reach/run.py — 跨平台信息触达代理
===========================================
信息域 core — 跨平台信息获取、API调用、数据聚合。
统一网关接入Telegram/Discord/Twitter/Reddit/GitHub等平台。
"""
import sys, json, os, time, urllib.request, urllib.error, urllib.parse, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 平台适配器
PLATFORM_ADAPTERS = {
    "github": {
        "api_base": "https://api.github.com",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "env_key": "GITHUB_TOKEN",
        "endpoints": {
            "search_repos": "/search/repositories?q={query}",
            "search_code": "/search/code?q={query}",
            "user": "/users/{username}",
            "repos": "/users/{username}/repos",
            "trending": "/search/repositories?q=stars:>100+pushed:>2026-01-01&sort=stars",
        }
    },
    "reddit": {
        "api_base": "https://www.reddit.com",
        "auth_header": "User-Agent",
        "auth_prefix": "GBT-AgentReach/5.0",
        "env_key": "",
        "endpoints": {
            "search": "/search.json?q={query}&limit=25",
            "subreddit": "/r/{subreddit}/hot.json?limit=25",
            "user": "/user/{username}/about.json",
        }
    },
    "hackernews": {
        "api_base": "https://hacker-news.firebaseio.com/v0",
        "auth_header": "",
        "auth_prefix": "",
        "env_key": "",
        "endpoints": {
            "top": "/topstories.json",
            "new": "/newstories.json",
            "item": "/item/{id}.json",
        }
    },
}

def _api_call(platform, endpoint_key, params_dict, timeout=15):
    """统一API调用"""
    adapter = PLATFORM_ADAPTERS.get(platform)
    if not adapter:
        return {"ok": False, "error": f"未知平台: {platform}"}

    endpoint = adapter["endpoints"].get(endpoint_key, "")
    if not endpoint:
        return {"ok": False, "error": f"未知端点: {endpoint_key}"}

    url = adapter["api_base"] + endpoint.format(**params_dict)
    headers = {"User-Agent": "GBT-AgentReach/5.0"}

    # API认证
    if adapter["auth_header"] and adapter["env_key"]:
        api_key = os.environ.get(adapter["env_key"], "")
        if api_key:
            headers[adapter["auth_header"]] = adapter["auth_prefix"] + api_key

    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = json.loads(resp.read().decode("utf-8"))
        return {"ok": True, "platform": platform, "endpoint": endpoint_key,
                "url": url, "data": data if isinstance(data, dict) else {"items": data[:10] if isinstance(data, list) else data}}
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.code}", "url": url}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100], "url": url}

def do_reach(params):
    """跨平台信息触达"""
    platform = params.get("platform", "github")
    endpoint = params.get("endpoint", "search_repos")
    query = params.get("query", params.get("q", ""))
    subreddit = params.get("subreddit", "")
    username = params.get("username", "")

    result = _api_call(platform, endpoint,
                      {"query": urllib.parse.quote(query),
                       "subreddit": subreddit, "username": username, "id": params.get("id", "")})
    return {**result, "cap": "agent_reach", "action": "reach", "domain": "信息域"}

def do_scrape(params):
    """抓取信息"""
    url = params.get("url", "")
    if not url:
        return {"ok": False, "error": "缺少url"}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GBT-AgentReach/5.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        body = resp.read().decode("utf-8", errors="replace")
        # 提取文本内容
        text = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return {"ok": True, "cap": "agent_reach", "action": "scrape",
                "url": url, "text": text[:3000], "text_len": len(text)}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}

def do_transmit(params):
    """传输数据"""
    return {"ok": True, "cap": "agent_reach", "action": "transmit", "note": "数据已聚合，待指定传输目标"}

# ══════════════════════════════════════════════════════
# 协作触达 · 广播/心跳/中继
# ══════════════════════════════════════════════════════

def do_broadcast_task(params):
    """向多个 agent 端点同时发送任务。

    params:
        task:      dict — 要广播的任务负载
        endpoints: [str] — 目标 URL 列表
        timeout:   int  — 单次请求超时(秒), 默认 10
    """
    task      = params.get("task", {})
    endpoints = params.get("endpoints", [])
    timeout   = params.get("timeout", 10)

    if not isinstance(endpoints, list) or len(endpoints) == 0:
        return {"ok": False, "error": "缺少 endpoints 列表或为空"}

    payload = json.dumps(task, ensure_ascii=False).encode("utf-8")
    results = [None] * len(endpoints)

    def _send_one(idx, url):
        try:
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "GBT-AgentReach/5.0"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                return idx, {"ok": True, "status": resp.status, "url": url,
                             "response": body[:500]}
        except urllib.error.HTTPError as e:
            return idx, {"ok": False, "status": e.code, "url": url,
                         "error": f"HTTP {e.code}"}
        except Exception as e:
            return idx, {"ok": False, "url": url, "error": str(e)[:100]}

    with ThreadPoolExecutor(max_workers=min(len(endpoints), 8)) as pool:
        futures = {pool.submit(_send_one, i, u): i for i, u in enumerate(endpoints)}
        for fut in as_completed(futures):
            i, r = fut.result()
            results[i] = r

    ok_count = sum(1 for r in results if r and r.get("ok"))
    return {
        "ok":          ok_count > 0,
        "total":       len(endpoints),
        "ok_count":    ok_count,
        "fail_count":  len(endpoints) - ok_count,
        "results":     results,
        "cap":         "agent_reach",
        "action":      "broadcast_task",
    }


def do_heartbeat_check(params):
    """Ping 所有已注册 agent 并报告健康状况。

    params:
        agents:  [ {id, url, timeout?}, ... ]
        timeout: int — 单次 ping 超时(秒), 默认 5
    """
    agents  = params.get("agents", [])
    timeout = params.get("timeout", 5)

    if not isinstance(agents, list):
        return {"ok": False, "error": "agents 必须是列表"}
    if not agents:
        return {"ok": True, "total": 0, "healthy": 0, "unhealthy": 0,
                "results": [], "cap": "agent_reach", "action": "heartbeat_check"}

    results = [None] * len(agents)

    def _ping_one(idx, a):
        aid  = a.get("id", f"agent-{idx}")
        url  = a.get("url", "")
        t    = a.get("timeout", timeout)
        t0   = time.time()
        if not url:
            return idx, {"id": aid, "healthy": False, "error": "缺少 url", "latency_ms": 0}
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "GBT-AgentReach/5.0"}, method="GET"
            )
            with urllib.request.urlopen(req, timeout=t) as resp:
                lat = round((time.time() - t0) * 1000)
                return idx, {"id": aid, "healthy": resp.status < 500,
                             "status": resp.status, "latency_ms": lat, "url": url}
        except urllib.error.HTTPError as e:
            lat = round((time.time() - t0) * 1000)
            return idx, {"id": aid, "healthy": e.code < 500,
                         "status": e.code, "latency_ms": lat, "url": url}
        except Exception as e:
            lat = round((time.time() - t0) * 1000)
            return idx, {"id": aid, "healthy": False,
                         "error": str(e)[:80], "latency_ms": lat, "url": url}

    with ThreadPoolExecutor(max_workers=min(len(agents), 8)) as pool:
        futures = {pool.submit(_ping_one, i, a): i for i, a in enumerate(agents)}
        for fut in as_completed(futures):
            i, r = fut.result()
            results[i] = r

    healthy   = [r for r in results if r and r.get("healthy")]
    unhealthy = [r for r in results if r and not r.get("healthy")]
    return {
        "ok":         len(unhealthy) == 0,
        "total":      len(agents),
        "healthy":    len(healthy),
        "unhealthy":  len(unhealthy),
        "healthy_ids":   [r["id"] for r in healthy],
        "unhealthy_ids": [r["id"] for r in unhealthy],
        "results":    results,
        "cap":        "agent_reach",
        "action":     "heartbeat_check",
    }


def do_relay_result(params):
    """将 agent 结果转发到 event_bus。

    params:
        result:    dict — 要转发的 agent 结果
        event_bus: str  — event_bus 端点 URL
        topic:     str  — 事件主题 (可选)
        timeout:   int  — 请求超时(秒), 默认 10
    """
    result    = params.get("result", {})
    event_bus = params.get("event_bus", "")
    topic     = params.get("topic", "agent.result")
    timeout   = params.get("timeout", 10)

    if not event_bus:
        return {"ok": False, "error": "缺少 event_bus URL"}

    envelope = {
        "topic":     topic,
        "timestamp": time.time(),
        "payload":   result,
        "source":    "agent_reach",
    }
    payload = json.dumps(envelope, ensure_ascii=False).encode("utf-8")

    try:
        req = urllib.request.Request(
            event_bus, data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "GBT-AgentReach/5.0"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return {
                "ok":       True,
                "status":   resp.status,
                "topic":    topic,
                "event_bus": event_bus,
                "response": body[:500],
                "cap":      "agent_reach",
                "action":   "relay_result",
            }
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.code}", "event_bus": event_bus}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100], "event_bus": event_bus}

HANDLERS = {
    "reach":          do_reach,
    "scrape":         do_scrape,
    "transmit":       do_transmit,
    "broadcast_task": do_broadcast_task,
    "heartbeat_check": do_heartbeat_check,
    "relay_result":   do_relay_result,
}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "reach"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
