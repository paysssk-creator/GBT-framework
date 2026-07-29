# 开发者：自由的风
"""stress_test/run.py — 压力测试/性能测试
=========================================
特殊域 ready — HTTP/TCP压力测试，多线程并发，延迟统计。
"""
import sys, json, os, time, threading, urllib.request, urllib.error, socket, concurrent.futures
from collections import defaultdict

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _http_request(url, timeout=10):
    start = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GBT-StressTest/5.0"})
        resp = urllib.request.urlopen(req, timeout=timeout)
        elapsed = time.time() - start
        return {"status": resp.status, "elapsed": round(elapsed, 3), "ok": True}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "elapsed": round(time.time() - start, 3), "ok": False, "error": "HTTP Error"}
    except Exception as e:
        return {"elapsed": round(time.time() - start, 3), "ok": False, "error": str(e)[:50]}

def do_run(params):
    url = params.get("url", params.get("target", ""))
    if not url:
        return {"ok": False, "error": "缺少url/target"}
    if not url.startswith("http"):
        url = "http://" + url

    concurrency = params.get("concurrency", 10)
    total_requests = params.get("requests", 100)
    timeout = params.get("timeout", 10)

    results = []
    latencies = []
    status_counts = defaultdict(int)
    errors = 0

    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(_http_request, url, timeout) for _ in range(total_requests)]
        for f in concurrent.futures.as_completed(futures):
            r = f.result()
            if r.get("ok"):
                latencies.append(r["elapsed"])
                status_counts[r["status"]] += 1
            else:
                errors += 1
                status_counts[r.get("status", "error")] += 1
            results.append(r)

    total_time = round(time.time() - start_time, 1)
    latencies.sort()

    stats = {
        "total_time_sec": total_time,
        "requests_per_sec": round(total_requests / total_time, 1) if total_time > 0 else 0,
        "total_requests": total_requests,
        "concurrency": concurrency,
        "errors": errors,
        "error_rate": round(errors / total_requests * 100, 1),
    }

    if latencies:
        stats["latency"] = {
            "min_ms": round(latencies[0] * 1000),
            "max_ms": round(latencies[-1] * 1000),
            "avg_ms": round(sum(latencies) / len(latencies) * 1000),
            "p50_ms": round(latencies[len(latencies)//2] * 1000),
            "p95_ms": round(latencies[int(len(latencies)*0.95)] * 1000) if len(latencies) >= 20 else None,
            "p99_ms": round(latencies[int(len(latencies)*0.99)] * 1000) if len(latencies) >= 100 else None,
        }

    stats["status_codes"] = dict(status_counts)

    return {
        "ok": True,
        "cap": "stress_test",
        "action": "run",
        "domain": "特殊域",
        "target": url,
        "stats": stats,
        "verdict": "高负载" if stats.get("error_rate", 0) > 10 else
                   "中度负载" if stats.get("error_rate", 0) > 1 else
                   "正常运行",
    }

def do_report(params):
    return do_run(params)

HANDLERS = {"run": do_run, "report": do_report}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "run"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
