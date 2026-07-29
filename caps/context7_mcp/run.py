"""context7_mcp/run.py — Context7实时文档能力

Context7 = 最广泛采用的MCP服务器 (~58k GitHub stars)
功能: 将库的最新版本特定文档注入AI上下文，终结API幻觉
用法: 在任何prompt前加 "use context7" 即可获得最新文档
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
    _list_tools = mod.do_list_tools
else:
    def do_call_tool(p):
        return {"ok": False, "error": "MCP bridge未找到"}
    def _list_tools(p):
        return {"ok": False, "error": "MCP bridge未找到"}

SERVER = "context7"


def do_resolve_docs(params: dict) -> dict:
    """解析库名, 获取最新版本文档ID"""
    library = params.get("library", params.get("query", ""))
    if not library:
        return {"ok": False, "error": "缺少 library 或 query 参数"}

    result = do_call_tool({
        "server": SERVER,
        "tool": "resolve-library-id",
        "args": {"libraryName": library}
    })
    return result


def do_search_docs(params: dict) -> dict:
    """在已解析的库文档中搜索"""
    topic = params.get("topic", params.get("query", ""))
    library_id = params.get("library_id", "")

    args = {"topic": topic}
    if library_id:
        args["libraryId"] = library_id

    result = do_call_tool({
        "server": SERVER,
        "tool": "get-library-docs",
        "args": args
    })
    return result


HANDLERS = {
    "resolve_docs": do_resolve_docs,
    "search_docs": do_search_docs,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "resolve_docs"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知动作: {action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))
