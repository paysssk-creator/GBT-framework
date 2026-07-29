# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
codebase_memory/run.py — Codebase Memory 代码知识图谱引擎
================================================================
集成 DeusData/codebase-memory-mcp (arXiv:2603.27277):
  - 纯C实现, 158语言, 子毫秒查询, 120x token节省
  - 14 MCP工具: 搜索/追踪/架构/影响/死代码/HTTP路由
  - 二进制安装: curl -fsSL install.sh | bash (或下载release)

本模块: 封装CBM调用 + Python纯代码回退
"""
import sys, json, os, subprocess, re
from pathlib import Path

SANDBOX = Path(__file__).parent.parent.parent
CBM_BIN = None

# 自动发现 CBM 二进制
for p in [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "codebase-memory-mcp" / "codebase-memory-mcp.exe",
    SANDBOX.parent / "codebase-memory-mcp" / "codebase-memory-mcp.exe",
    Path.home() / ".local" / "bin" / "codebase-memory-mcp",
    Path("codebase-memory-mcp.exe"),
]:
    if p.exists():
        CBM_BIN = str(p)
        break

# 也检查 PATH
if not CBM_BIN:
    try:
        r = subprocess.run(["where", "codebase-memory-mcp"], capture_output=True, text=True, timeout=3)
        if r.returncode == 0 and r.stdout.strip():
            CBM_BIN = r.stdout.strip().split("\n")[0]
    except Exception:
        pass

_tracked_procs = []
import atexit as _atexit
def _cleanup_graph_procs():
    for proc in _tracked_procs:
        try:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
_atexit.register(_cleanup_graph_procs)


def _run_cbm(args: list, timeout: int = 30) -> dict:
    """调用CBM二进制"""
    if not CBM_BIN:
        return {"ok": False, "error": "codebase-memory-mcp 未安装。安装: curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash"}
    try:
        r = subprocess.run([CBM_BIN] + args, capture_output=True, text=True, timeout=timeout, cwd=str(SANDBOX))
        return {"ok": r.returncode == 0, "stdout": r.stdout[:5000], "stderr": r.stderr[:1000]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "超时"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ═══ Python 回退分析 ═══

def _py_search_symbol(query: str, path: str = None) -> dict:
    """Python回退: 搜索符号定义"""
    target = Path(path) if path else SANDBOX
    results = []
    patterns = [
        (r"^def\s+(" + re.escape(query) + r")\s*\(", "python_function"),
        (r"^class\s+(" + re.escape(query) + r")\s*[:\(]", "python_class"),
        (r"^(?:async\s+)?function\s+(" + re.escape(query) + r")\s*\(", "js_function"),
        (r"^func\s+(" + re.escape(query) + r")\s*\(", "go_function"),
    ]
    for ext, pats in {
        ".py": [patterns[0], patterns[1]],
        ".js": [patterns[2]],
        ".ts": [patterns[2]],
        ".go": [patterns[3]],
    }.items():
        for fp in list(target.rglob(f"*{ext}"))[:200]:
            try:
                for i, line in enumerate(fp.read_text("utf-8", errors="replace").split("\n"), 1):
                    for pat, kind in pats:
                        m = re.search(pat, line)
                        if m:
                            results.append({"file": str(fp.relative_to(target)), "line": i, "kind": kind, "name": m.group(1)})
            except Exception:
                pass
    return {"ok": True, "query": query, "found": len(results), "results": results[:30], "method": "python_regex_fallback"}


def _py_trace_callchain(symbol: str, path: str = None) -> dict:
    """Python回退: 追踪调用链"""
    target = Path(path) if path else SANDBOX
    callers = []
    callees = []
    for fp in list(target.rglob("*.py"))[:200]:
        try:
            content = fp.read_text("utf-8", errors="replace")
            rel = str(fp.relative_to(target))
            for i, line in enumerate(content.split("\n"), 1):
                if symbol + "(" in line and "def " + symbol not in line:
                    callers.append({"file": rel, "line": i, "call": line.strip()[:100]})
                if f"def {symbol}" in line:
                    # 找函数内调用
                    body = content.split(f"def {symbol}")[1].split("\ndef ")[0] if f"def {symbol}" in content else ""
                    for m in re.finditer(r"(\w+)\s*\(", body):
                        name = m.group(1)
                        if name not in ("if", "for", "while", "print", "len", "range", "int", "str", "isinstance"):
                            callees.append(name)
        except Exception:
            pass
    return {"ok": True, "symbol": symbol, "callers": len(callers), "callees": list(set(callees))[:20], "method": "python_regex_fallback"}


def _py_dead_code(path: str = None) -> dict:
    """Python回退: 检测疑似死代码"""
    target = Path(path) if path else SANDBOX
    defined = {}
    called = set()
    for fp in list(target.rglob("*.py"))[:200]:
        try:
            content = fp.read_text("utf-8", errors="replace")
            rel = str(fp.relative_to(target))
            for m in re.finditer(r"^def\s+(\w+)\s*\(", content, re.MULTILINE):
                defined[m.group(1)] = rel
            for m in re.finditer(r"(?<!def\s)(\w+)\s*\(", content):
                called.add(m.group(1))
        except Exception:
            pass
    dead = {k: v for k, v in defined.items() if k not in called and not k.startswith("_")}
    return {"ok": True, "total_defined": len(defined), "dead_functions": len(dead), "dead": dead, "method": "python_regex_fallback"}


def _py_arch_analysis(path: str = None) -> dict:
    """Python回退: 模块依赖分析"""
    target = Path(path) if path else SANDBOX
    imports = {}
    for fp in list(target.rglob("*.py"))[:200]:
        try:
            content = fp.read_text("utf-8", errors="replace")
            rel = str(fp.relative_to(target))
            mod_imports = []
            for m in re.finditer(r"^(?:from|import)\s+([\w.]+)", content, re.MULTILINE):
                mod_imports.append(m.group(1))
            if mod_imports:
                imports[rel] = mod_imports
        except Exception:
            pass
    # 找循环依赖
    cycles = []
    for mod, deps in imports.items():
        for dep in deps:
            dep_mod = dep.replace(".", "/") + ".py"
            if dep_mod in imports:
                for subdep in imports.get(dep_mod, []):
                    sub_mod = subdep.replace(".", "/") + ".py"
                    if sub_mod == mod:
                        cycles.append({"a": mod, "b": dep_mod, "type": "direct_cycle"})
    return {
        "ok": True,
        "modules": len(imports),
        "total_imports": sum(len(v) for v in imports.values()),
        "cycles": cycles[:10],
        "top_deps": sorted(((k, len(v)) for k, v in imports.items()), key=lambda x: x[1], reverse=True)[:10],
        "method": "python_regex_fallback",
    }


# ═══ 处理函数 ═══

def do_search(params: dict) -> dict:
    query = params.get("query", "")
    path = params.get("path", str(SANDBOX))
    if not query:
        return {"ok": False, "error": "缺少 query"}
    r = _run_cbm(["cli", "search_graph", json.dumps({"query": query, "project": Path(path).name})], timeout=15)
    if not r.get("ok"):
        return _py_search_symbol(query, path)
    return {"ok": True, "method": "cbm_binary", "result": r.get("stdout", "")}


def do_trace(params: dict) -> dict:
    symbol = params.get("symbol", params.get("query", ""))
    path = params.get("path", str(SANDBOX))
    if not symbol:
        return {"ok": False, "error": "缺少 symbol"}
    r = _run_cbm(["trace", symbol, "--path", path], timeout=30)
    if not r.get("ok"):
        return _py_trace_callchain(symbol, path)
    return {"ok": True, "method": "cbm_binary", "result": r.get("stdout", "")}


def do_analyze(params: dict) -> dict:
    path = params.get("path", str(SANDBOX))
    r = _run_cbm(["analyze", "--path", path], timeout=30)
    if not r.get("ok"):
        return _py_arch_analysis(path)
    return {"ok": True, "method": "cbm_binary", "result": r.get("stdout", "")}


def do_deadcode(params: dict) -> dict:
    path = params.get("path", str(SANDBOX))
    r = _run_cbm(["dead-code", "--path", path], timeout=30)
    if not r.get("ok"):
        return _py_dead_code(path)
    return {"ok": True, "method": "cbm_binary", "result": r.get("stdout", "")}


def do_info(params: dict) -> dict:
    installed = CBM_BIN is not None
    return {
        "ok": True,
        "installed": installed,
        "binary": CBM_BIN or "未安装",
        "features": {
            "languages": 158,
            "mcp_tools": 14,
            "index_speed": "Linux kernel 28M LOC in 3min",
            "query_speed": "sub-ms",
            "token_saving": "120x vs file-by-file",
            "dependencies": "zero (pure C static binary)",
        },
        "install_cmd": "curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash",
        "paper": "arXiv:2603.27277",
        "note": "已集成Python回退分析 (regex-based)" if not installed else "CBM二进制可用",
    }


def do_architecture(params: dict) -> dict:
    """架构全景"""
    r = _run_cbm(["get_architecture", "--project", str(SANDBOX.parent), "--json"])
    if r["ok"]: return json.loads(r["stdout"]) if r["stdout"].strip().startswith("{") else {"ok": True, "data": r["stdout"]}
    return r

def do_semantic(params: dict) -> dict:
    """语义搜索"""
    query = params.get("query", params.get("q", ""))
    if not query: return {"ok": False, "error": "缺少 query 参数"}
    r = _run_cbm(["semantic_query", "--query", query, "--project", str(SANDBOX.parent), "--json"])
    if r["ok"]: return json.loads(r["stdout"]) if r["stdout"].strip().startswith("{") else {"ok": True, "data": r["stdout"]}
    return r

def do_changes(params: dict) -> dict:
    """变更影响分析"""
    return _run_cbm(["detect_changes", "--project", str(SANDBOX.parent), "--json"])

def do_cypher(params: dict) -> dict:
    """Cypher 图查询"""
    query = params.get("query", params.get("q", ""))
    if not query: return {"ok": False, "error": "缺少 query 参数"}
    r = _run_cbm(["query_graph", "--query", query, "--project", str(SANDBOX.parent), "--json"])
    if r["ok"]: return json.loads(r["stdout"]) if r["stdout"].strip().startswith("{") else {"ok": True, "data": r["stdout"]}
    return r

def do_snippet(params: dict) -> dict:
    """获取代码片段"""
    name = params.get("name", params.get("function", params.get("class", "")))
    if not name: return {"ok": False, "error": "缺少 name/function 参数"}
    r = _run_cbm(["get_code_snippet", "--name", name, "--project", str(SANDBOX.parent)])
    return r

def do_routes(params: dict) -> dict:
    """HTTP路由"""
    return _run_cbm(["get_architecture", "--project", str(SANDBOX.parent), "--json"])


def do_auto_index(params: dict) -> dict:
    """auto_index — 自动爬取GBT项目源码并构建代码知识图谱"""
    target = params.get("path", str(SANDBOX))
    patterns = params.get("patterns", ["*.py", "*.js", "*.ts", "*.go", "*.rs", "*.java", "*.cpp", "*.c", "*.h"])
    depth = params.get("depth", None)

    root = Path(target)
    if not root.exists():
        return {"ok": False, "error": f"路径不存在: {target}"}

    graph: dict[str, dict] = {}  # symbol → {path, kind, deps, line}
    edges: list[dict] = []  # {from, to, kind}
    files_indexed: list[str] = []

    # Regex extractors per language
    extractors = {
        ".py": {
            "func": re.compile(r'^\s*def\s+(\w+)\s*\(', re.MULTILINE),
            "class": re.compile(r'^\s*class\s+(\w+)\s*[(:]', re.MULTILINE),
            "import": re.compile(r'^(?:from\s+(\S+)\s+)?import\s+((?:\w+(?:\s*,\s*)?)+)', re.MULTILINE),
            "call": re.compile(r'(\w+)\s*\(', re.MULTILINE),
        },
        ".js": {
            "func": re.compile(r'(?:function\s+(\w+)|(\w+)\s*=\s*(?:async\s+)?function|\b(\w+)\s*=\s*\([^)]*\)\s*=>)', re.MULTILINE),
            "class": re.compile(r'class\s+(\w+)', re.MULTILINE),
            "import": re.compile(r'(?:import\s+.*?\bfrom\s+[\'"](.+?)[\'"]|require\s*\(\s*[\'"](.+?)[\'"]\s*\))', re.MULTILINE),
        },
        ".ts": {
            "func": re.compile(r'(?:function\s+(\w+)|(\w+)\s*=\s*\([^)]*\)\s*=>)', re.MULTILINE),
            "class": re.compile(r'class\s+(\w+)', re.MULTILINE),
            "import": re.compile(r'import\s+.*?\bfrom\s+[\'"](.+?)[\'"]', re.MULTILINE),
        },
        ".go": {
            "func": re.compile(r'^func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(', re.MULTILINE),
            "type": re.compile(r'^type\s+(\w+)\s+(?:struct|interface)', re.MULTILINE),
            "import": re.compile(r'"([^"]+)"', re.MULTILINE),
        },
        ".rs": {
            "func": re.compile(r'^\s*(?:pub\s+)?fn\s+(\w+)\s*[<\(]', re.MULTILINE),
            "struct": re.compile(r'^\s*(?:pub\s+)?struct\s+(\w+)', re.MULTILINE),
            "import": re.compile(r'use\s+([\w:]+)', re.MULTILINE),
        },
    }

    default_extractor = {
        "func": re.compile(r'\b(?:def|function|func|fn|sub)\s+(\w+)', re.MULTILINE),
        "class": re.compile(r'\b(?:class|struct|interface|type)\s+(\w+)', re.MULTILINE),
    }

    # Crawl project files
    for pat in patterns:
        for fpath in root.rglob(pat):
            if depth is not None:
                try:
                    rel = fpath.relative_to(root)
                    if len(rel.parts) > depth:
                        continue
                except ValueError:
                    continue

            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            ext = fpath.suffix
            ex = extractors.get(ext, default_extractor)
            rel_path = str(fpath.relative_to(SANDBOX))
            files_indexed.append(rel_path)

            # Extract function definitions
            for m in ex.get("func", []).finditer(content):
                name = next((g for g in m.groups() if g), None)
                if not name or len(name) < 2:
                    continue
                line_no = content[:m.start()].count("\n") + 1
                if name not in graph:
                    graph[name] = {"kind": "function", "paths": [], "lines": []}
                graph[name]["paths"].append(rel_path)
                graph[name]["lines"].append(line_no)

            # Extract class/type definitions
            for kind_key in ["class", "type", "struct"]:
                if kind_key not in ex:
                    continue
                for m in ex[kind_key].finditer(content):
                    name = next((g for g in m.groups() if g), None)
                    if not name or len(name) < 2:
                        continue
                    line_no = content[:m.start()].count("\n") + 1
                    if name not in graph:
                        graph[name] = {"kind": kind_key, "paths": [], "lines": []}
                    else:
                        graph[name]["kind"] = kind_key
                    graph[name]["paths"].append(rel_path)
                    graph[name]["lines"].append(line_no)

            # Extract import edges
            import_pat = ex.get("import")
            if import_pat:
                for m in import_pat.finditer(content):
                    target = next((g for g in m.groups() if g), None)
                    if not target:
                        continue
                    # Find containing symbol for this import region
                    for sym_name, sym_info in graph.items():
                        if sym_info.get("paths") and rel_path in sym_info["paths"]:
                            edges.append({"from": sym_name, "to": target, "kind": "import"})

    # Also try CBM binary index
    cbm_result = None
    try:
        cbm_result = _run_cbm(["index", "--project", str(SANDBOX.parent)], timeout=300)
    except Exception:
        pass

    # Build summary stats
    total_symbols = len(graph)
    total_edges = len(edges)
    kind_counts = {}
    for info in graph.values():
        k = info["kind"]
        kind_counts[k] = kind_counts.get(k, 0) + 1

    return {
        "ok": True,
        "action": "auto_index",
        "project": str(root),
        "files_indexed": len(files_indexed),
        "symbols": total_symbols,
        "edges": total_edges,
        "by_kind": kind_counts,
        "graph": graph if total_symbols <= 200 else {"_truncated": True, "_count": total_symbols},
        "edges_sample": edges[:200] if total_edges > 200 else edges,
        "cbm_index": cbm_result.get("ok") if cbm_result else None,
    }


def do_find_pattern(params: dict) -> dict:
    """find_pattern — 在代码库中搜索相似代码模式"""
    query = params.get("query", params.get("pattern", ""))
    path = params.get("path", str(SANDBOX))
    kind = params.get("kind", "any")  # function, class, error_handling, retry, singleton, etc.
    max_results = params.get("max", 50)

    if not query:
        return {"ok": False, "error": "需要 query 或 pattern 参数"}

    root = Path(path)
    results = []

    # Pre-built structural patterns
    structural_patterns = {
        "error_handling": re.compile(r'(?:try)\s*:\s*\n(?:\s+.+\n)*?\s*(?:except\s+(?:\w+(?:\s+as\s+\w+)?)\s*:\s*\n(?:\s+.+\n)*?)*', re.MULTILINE),
        "retry_loop": re.compile(r'(?:for|while).*\n\s*try\s*:', re.MULTILINE),
        "singleton": re.compile(r'(?:__new__|getInstance|singleton|_instance)', re.IGNORECASE),
        "decorator": re.compile(r'@\w+', re.MULTILINE),
        "context_manager": re.compile(r'(?:with\s+.+\s+as\s+\w+\s*:|__enter__|__exit__)', re.MULTILINE),
        "api_endpoint": re.compile(r'@(?:app|router|bp)\.(?:route|get|post|put|delete|patch)\s*\(', re.MULTILINE),
        "list_comprehension": re.compile(r'\[[^\[\]]*\bfor\b[^\[\]]*\]', re.MULTILINE),
    }

    struct_pat = structural_patterns.get(kind)
    query_pat = re.compile(re.escape(query), re.IGNORECASE)

    for fpath in root.rglob("*.py"):
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        rel_path = str(fpath.relative_to(SANDBOX))
        matches = []

        # Check structural pattern if specified
        if struct_pat:
            for m in struct_pat.finditer(content):
                line_no = content[:m.start()].count("\n") + 1
                snippet = content[m.start():m.end()][:200]
                matches.append({"line": line_no, "snippet": snippet, "kind": kind})

        # Check text query
        for m in query_pat.finditer(content):
            if m.group():
                line_no = content[:m.start()].count("\n") + 1
                line = content.split("\n")[line_no - 1].strip()[:200]
                if not any(x["line"] == line_no for x in matches):
                    matches.append({"line": line_no, "snippet": line, "kind": "text_match"})

        if matches:
            results.append({"file": rel_path, "matches": matches[:20]})
            if len(results) >= max_results:
                break

    return {
        "ok": True,
        "action": "find_pattern",
        "query": query,
        "kind": kind,
        "total_matches": sum(len(r["matches"]) for r in results),
        "files_found": len(results),
        "results": results,
    }


def do_impact_analysis(params: dict) -> dict:
    """impact_analysis — 分析给定符号的依赖者和影响范围"""
    symbol = params.get("symbol", params.get("query", ""))
    path = params.get("path", str(SANDBOX))

    if not symbol:
        return {"ok": False, "error": "需要 symbol 参数"}

    root = Path(path)

    # Phase 1: find the symbol definition
    definition = None
    symbol_pat = re.compile(r'^\s*(?:def|class|async def)\s+' + re.escape(symbol) + r'\b', re.MULTILINE)

    for fpath in root.rglob("*.py"):
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        m = symbol_pat.search(content)
        if m:
            line_no = content[:m.start()].count("\n") + 1
            line_text = content.split("\n")[line_no - 1].strip()
            rel_path = str(fpath.relative_to(SANDBOX))
            definition = {
                "file": rel_path,
                "line": line_no,
                "declaration": line_text,
            }
            break

    # Phase 2: find all references (callers/dependents)
    dependents: list[dict] = []
    call_pat = re.compile(r'\b' + re.escape(symbol) + r'\s*\(', re.MULTILINE)
    ref_pat = re.compile(r'\b' + re.escape(symbol) + r'\b', re.MULTILINE)

    for fpath in root.rglob("*.py"):
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        rel_path = str(fpath.relative_to(SANDBOX))

        # Skip the definition file for counting references within it
        is_def_file = definition and rel_path == definition["file"]

        for m in call_pat.finditer(content):
            line_no = content[:m.start()].count("\n") + 1
            line_text = content.split("\n")[line_no - 1].strip()
            # Find the enclosing function
            enclosing = _find_enclosing_function(content, line_no)
            dependents.append({
                "file": rel_path,
                "line": line_no,
                "usage": line_text[:200],
                "enclosing": enclosing,
                "kind": "call",
                "same_file": is_def_file,
            })

        # Also catch non-call references (imports, assignments, etc.)
        for m in ref_pat.finditer(content):
            line_no = content[:m.start()].count("\n") + 1
            line_text = content.split("\n")[line_no - 1].strip()
            # Skip if it's the definition line or already caught as call
            if definition and rel_path == definition["file"] and line_no == definition["line"]:
                continue
            if any(d["file"] == rel_path and d["line"] == line_no for d in dependents):
                continue
            enclosing = _find_enclosing_function(content, line_no)
            dependents.append({
                "file": rel_path,
                "line": line_no,
                "usage": line_text[:200],
                "enclosing": enclosing,
                "kind": "reference",
                "same_file": is_def_file,
            })

    # Analyze impact score
    unique_files = len(set(d["file"] for d in dependents))
    external_files = len(set(d["file"] for d in dependents if not d.get("same_file")))
    call_count = sum(1 for d in dependents if d["kind"] == "call")

    impact_score = "low"
    if unique_files >= 5 or call_count >= 10:
        impact_score = "medium"
    if unique_files >= 10 or call_count >= 20:
        impact_score = "high"
    if unique_files >= 20 or call_count >= 50:
        impact_score = "critical"

    return {
        "ok": True,
        "action": "impact_analysis",
        "symbol": symbol,
        "definition": definition,
        "dependents": len(dependents),
        "unique_files": unique_files,
        "external_files": external_files,
        "total_calls": call_count,
        "impact_score": impact_score,
        "dependents_list": dependents[:100],
        "_truncated": len(dependents) > 100,
    }


def _find_enclosing_function(content: str, line_no: int) -> str | None:
    """Find the function/class that contains a given line."""
    lines = content.split("\n")
    func_pat = re.compile(r'^\s*(?:def|class|async def)\s+(\w+)')
    current = None
    for i, line in enumerate(lines[:line_no]):
        m = func_pat.match(line)
        if m:
            current = m.group(1)
    return current

def do_index(params: dict) -> dict:
    """强制重新索引"""
    return _run_cbm(["index", "--project", str(SANDBOX.parent), "--force"], timeout=300)

def do_graph(params: dict) -> dict:
    """打开3D可视化"""
    port = params.get("port", 9749)
    proc = subprocess.Popen([CBM_BIN, "--ui=true", f"--port={port}"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    _tracked_procs.append(proc)
    return {"ok": True, "graph_ui": f"http://localhost:{port}", "port": port, "pid": proc.pid}

handlers = {
    "search": do_search, "trace": do_trace, "analyze": do_analyze,
    "deadcode": do_deadcode, "info": do_info,
    "architecture": do_architecture, "semantic": do_semantic,
    "changes": do_changes, "cypher": do_cypher, "snippet": do_snippet,
    "routes": do_routes, "index": do_index, "graph": do_graph,
    "auto_index": do_auto_index, "find_pattern": do_find_pattern, "impact_analysis": do_impact_analysis,
}


if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else 'info'
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    h = handlers.get(action, lambda p: {'ok': False})
    print(json.dumps(h(params), ensure_ascii=False))