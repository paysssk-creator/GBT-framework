"""firecrawl_mcp/run.py — Firecrawl网页抓取能力

Firecrawl = 最强大的AI网页抓取工具 (~143k GitHub stars)
功能: 任意网站→干净Markdown, 整站爬取, LLM结构化提取
需要: FIRECRAWL_API_KEY 环境变量
"""
import json
import sys
import importlib.util
from pathlib import Path

# 通过MCP桥接调用
_mcp_path = Path(__file__).resolve().parent.parent / "mcp_bridge" / "run.py"
spec = importlib.util.spec_from_file_location("mcp_bridge", str(_mcp_path))
if spec and spec.loader:
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    do_call_tool = mod.do_call_tool
else:
    def do_call_tool(p):
        return {"ok": False, "error": "MCP bridge未找到"}
SERVER = "firecrawl"


def do_scrape(params: dict) -> dict:
    """抓取单个URL"""
    url = params.get("url", "")
    if not url:
        return {"ok": False, "error": "缺少 url 参数"}

    result = do_call_tool({
        "server": SERVER,
        "tool": "firecrawl_scrape",
        "args": {
            "url": url,
            "formats": params.get("formats", ["markdown"]),
            "onlyMainContent": params.get("only_main", True)
        }
    })
    return result


def do_crawl(params: dict) -> dict:
    """爬取整个网站"""
    url = params.get("url", "")
    if not url:
        return {"ok": False, "error": "缺少 url 参数"}

    result = do_call_tool({
        "server": SERVER,
        "tool": "firecrawl_crawl",
        "args": {
            "url": url,
            "maxDepth": params.get("max_depth", 3),
            "limit": params.get("limit", 50)
        }
    })
    return result


def do_extract(params: dict) -> dict:
    """LLM结构化提取"""
    urls = params.get("urls", [])
    prompt = params.get("prompt", "Extract the main content")
    schema = params.get("schema")

    if not urls:
        return {"ok": False, "error": "缺少 urls 参数"}

    args = {
        "urls": urls if isinstance(urls, list) else [urls],
        "prompt": prompt
    }
    if schema:
        args["schema"] = schema

    result = do_call_tool({
        "server": SERVER,
        "tool": "firecrawl_extract",
        "args": args
    })
    return result


HANDLERS = {
    "scrape": do_scrape,
    "crawl": do_crawl,
    "extract": do_extract,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "scrape"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知动作: {action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
