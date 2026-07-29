# 开发者：自由的风
"""gbt_gigs/run.py — GBT零工市场
=================================
特殊域 ready — GBT自主接单/完成任务/赚取收益的零工平台。
支持: 代码审查/渗透测试/bug修复/数据分析/爬虫/自动化脚本。
"""
import sys, json, os, time
from pathlib import Path
from datetime import datetime

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIGS_DIR = Path.home() / ".gbt" / "gigs"
GIGS_DIR.mkdir(parents=True, exist_ok=True)

# 零工模板库
GIG_TEMPLATES = {
    "code_review": {
        "title": "代码审查",
        "skills": ["code_scanner", "programming", "security_scan"],
        "pipeline": [
            {"cap": "code_scanner", "action": "scan", "desc": "安全漏洞扫描"},
            {"cap": "security_scan", "action": "scan", "desc": "密钥泄露检查"},
            {"cap": "programming", "action": "code", "desc": "生成审查报告"},
        ],
        "base_price_usd": 15,
    },
    "pentest": {
        "title": "渗透测试",
        "skills": ["strix", "sqli_tester", "xss_tester", "port_scanner"],
        "pipeline": [
            {"cap": "port_scanner", "action": "scan", "desc": "端口扫描"},
            {"cap": "sqli_tester", "action": "test", "desc": "SQL注入检测"},
            {"cap": "xss_tester", "action": "test", "desc": "XSS检测"},
            {"cap": "strix", "action": "test", "desc": "综合渗透"},
        ],
        "base_price_usd": 50,
    },
    "bug_fix": {
        "title": "Bug修复",
        "skills": ["auto_fix", "root_cause_debugger", "programming"],
        "pipeline": [
            {"cap": "root_cause_debugger", "action": "debug", "desc": "根因分析"},
            {"cap": "auto_fix", "action": "fix", "desc": "自动修复"},
            {"cap": "programming", "action": "code", "desc": "生成修复代码"},
        ],
        "base_price_usd": 20,
    },
    "data_analysis": {
        "title": "数据分析",
        "skills": ["data_engine", "deep_reasoner"],
        "pipeline": [
            {"cap": "data_engine", "action": "analyze", "desc": "数据处理"},
            {"cap": "deep_reasoner", "action": "reason", "desc": "分析推理"},
        ],
        "base_price_usd": 10,
    },
    "scraping": {
        "title": "网页爬虫",
        "skills": ["deep_scrape", "precision_scrape", "web_search"],
        "pipeline": [
            {"cap": "web_search", "action": "search", "desc": "信息搜索"},
            {"cap": "deep_scrape", "action": "scrape", "desc": "深度抓取"},
            {"cap": "precision_scrape", "action": "extract", "desc": "精准提取"},
        ],
        "base_price_usd": 12,
    },
    "automation": {
        "title": "自动化脚本",
        "skills": ["programming", "code_exec", "auto_pipeline"],
        "pipeline": [
            {"cap": "programming", "action": "code", "desc": "脚本生成"},
            {"cap": "code_exec", "action": "run", "desc": "执行验证"},
            {"cap": "auto_pipeline", "action": "run", "desc": "流水线编排"},
        ],
        "base_price_usd": 18,
    },
}

def do_list(params):
    """列出可接零工"""
    category = params.get("category", "")
    gigs = {}
    for gid, gig in GIG_TEMPLATES.items():
        if category and category not in gid:
            continue
        gigs[gid] = {
            "title": gig["title"],
            "skills": gig["skills"],
            "steps": len(gig["pipeline"]),
            "price_usd": gig["base_price_usd"],
        }
    return {"ok": True, "cap": "gbt_gigs", "action": "list",
            "domain": "特殊域", "total": len(gigs), "gigs": gigs}

def do_accept(params):
    """接受零工任务"""
    gig_type = params.get("type", params.get("gig", "code_review"))
    if gig_type not in GIG_TEMPLATES:
        return {"ok": False, "error": f"未知任务类型: {gig_type}",
                "available": list(GIG_TEMPLATES.keys())}

    gig = GIG_TEMPLATES[gig_type]
    task_id = f"gig_{gig_type}_{int(time.time())}"
    task = {
        "id": task_id,
        "type": gig_type,
        "title": gig["title"],
        "pipeline": gig["pipeline"],
        "price_usd": gig["base_price_usd"],
        "accepted_at": datetime.now().isoformat(),
        "status": "accepted",
    }

    task_file = GIGS_DIR / f"{task_id}.json"
    task_file.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"ok": True, "cap": "gbt_gigs", "action": "accept",
            "task_id": task_id, "gig": gig["title"],
            "steps": len(gig["pipeline"]), "price_usd": gig["base_price_usd"],
            "pipeline": [s["desc"] for s in gig["pipeline"]]}

def do_complete(params):
    """完成任务"""
    task_id = params.get("task_id", "")
    task_file = GIGS_DIR / f"{task_id}.json"
    if not task_file.exists():
        return {"ok": False, "error": f"任务{task_id}不存在"}

    task = json.loads(task_file.read_text(encoding="utf-8"))
    task["status"] = "completed"
    task["completed_at"] = datetime.now().isoformat()
    task_file.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"ok": True, "cap": "gbt_gigs", "action": "complete",
            "task_id": task_id, "status": "completed",
            "earned_usd": task["price_usd"],
            "note": "零工已完成 GBT收益增加"}

HANDLERS = {"list": do_list, "accept": do_accept, "complete": do_complete}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "list"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
