# 开发者：自由的风
"""report_generator/run.py — 自动化报告生成"""
import sys, json, os, time
from pathlib import Path
from datetime import datetime

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_DIR = Path.home() / ".gbt" / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

REPORT_TYPES = ["渗透测试", "安全审计", "漏洞扫描", "代码审查", "威胁狩猎", "合规检查", "取证分析"]

def do_generate(params):
    rtype = params.get("type", "渗透测试")
    target = params.get("target", "未指定")
    findings = params.get("findings", [])
    author = params.get("author", "GBT小土豆 v5.0")
    if isinstance(findings, dict): findings = [findings]

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# {} 报告".format(rtype),
        "",
        "| 项目 | 内容 |",
        "|---|---|",
        "| 目标 | {} |".format(target),
        "| 日期 | {} |".format(ts),
        "| 生成者 | {} |".format(author),
        "| 类型 | {} |".format(rtype),
        "",
        "## 发现汇总",
        "",
        "| # | 严重性 | 发现 | 建议 |",
        "|---|---|---|---|",
    ]
    stats = {"critical": 0, "high": 0, "warning": 0, "info": 0}
    for i, f in enumerate(findings[:50], 1):
        sev = f.get("severity", f.get("level", "warning"))
        stats[sev] = stats.get(sev, 0) + 1
        desc = f.get("finding", f.get("description", f.get("match", str(f)[:80])))
        fix = f.get("fix", f.get("suggestion", "-"))
        lines.append("| {} | {} | {} | {} |".format(i, sev.upper(), desc[:80], fix[:60]))

    lines += [
        "",
        "## 统计",
        "- 严重: {}".format(stats.get("critical", 0)),
        "- 高危: {}".format(stats.get("high", 0)),
        "- 警告: {}".format(stats.get("warning", 0)),
        "- 信息: {}".format(stats.get("info", 0)),
        "- 总计: {}".format(len(findings)),
        "",
        "---",
        "*报告由 {} 自动生成 · {}*".format(author, ts),
    ]
    report = "\n".join(lines)
    fname = "{}_{}.md".format(rtype.replace(" ", "_"), int(time.time()))
    fpath = REPORT_DIR / fname
    fpath.write_text(report, encoding="utf-8")

    return {"ok": True, "cap": "report_generator", "domain": "AI编程",
            "type": rtype, "file": str(fpath), "findings_count": len(findings), "stats": stats}

def do_types(params):
    return {"ok": True, "types": REPORT_TYPES, "total": len(REPORT_TYPES)}

HANDLERS = {"generate": do_generate, "types": do_types}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "types"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    r = HANDLERS.get(action, lambda p: {"ok": False})(params)
    print(json.dumps(r, ensure_ascii=False, default=str))
