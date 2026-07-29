# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""coder/run.py — 代码工具集：格式化/压缩/统计/检查/AST打印，零外部依赖"""
import sys, json, os, re, ast, tokenize, io, textwrap, collections, itertools


# ═══════════════════════════════════════════
# 0. 工具函数
# ═══════════════════════════════════════════

_LANG_ALIASES = {
    "javascript": "js", "ecmascript": "js", "node": "js",
    "python3": "py", "py": "py", "python": "py",
    "json": "json",
    "html": "html", "htm": "html",
}

_BRACKET_PAIRS = {"(": ")", "[": "]", "{": "}", "<": ">"}
_CLOSE_TO_OPEN = {v: k for k, v in _BRACKET_PAIRS.items()}
_Q = {r'"', r"'", "`"}  # quote-like chars
_Q2 = {"'''", '"""'}
_RQ = {r"\"", r"\'"}

def _detect_lang(lang: str) -> str:
    return _LANG_ALIASES.get((lang or "").strip().lower(), "py")

_PY_BLOCK_RE = re.compile(r"^(def |class |async def |if |elif |else:|for |while |with |try:|except |finally:|match |case )")

# ─── bracket balance check ───
def _check_brackets(code: str) -> dict:
    """Check bracket balance, return issues if any."""
    issues = []
    stack = []
    line_starts = [0]
    for i, ch in enumerate(code):
        if ch == "\n":
            line_starts.append(i + 1)
    line_starts.append(len(code))

    def _line_of(pos):
        for idx in range(len(line_starts) - 1, -1, -1):
            if line_starts[idx] <= pos:
                return idx + 1
        return 1

    i = 0
    n = len(code)
    while i < n:
        ch = code[i]
        if ch in _BRACKET_PAIRS:
            stack.append((ch, i))
        elif ch in _CLOSE_TO_OPEN:
            if not stack:
                issues.append(f"行{_line_of(i)}: 意外的 '{ch}' (缺少开括号)")
            else:
                opener, pos = stack.pop()
                expected_close = _BRACKET_PAIRS[opener]
                if ch != expected_close:
                    issues.append(f"行{_line_of(i)}: 期望 '{expected_close}' 但遇到 '{ch}' (对应开括号行{_line_of(pos)}的 '{opener}')")
        # skip strings
        if ch in _Q:
            q = ch
            i += 1
            while i < n and code[i] != q:
                if code[i] == "\\":
                    i += 1
                i += 1
        i += 1
    if stack:
        for opener, pos in stack:
            issues.append(f"行{_line_of(pos)}: 未闭合的 '{opener}'")
    return {"balanced": len(issues) == 0, "issues": issues}


# ═══════════════════════════════════════════
# 1. format — 代码缩进美化
# ═══════════════════════════════════════════

def _fmt_json(code: str) -> dict:
    try:
        obj = json.loads(code)
        return {"ok": True, "result": json.dumps(obj, indent=2, ensure_ascii=False)}
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"JSON解析失败: {e}"}

def _fmt_python(code: str) -> dict:
    try:
        tree = ast.parse(code)
        return {"ok": True, "result": ast.unparse(tree)}
    except SyntaxError as e:
        # Fallback: basic indent
        return {"ok": True, "result": _fallback_indent_py(code), "warning": f"ast解析失败({e})，使用基础格式化"}

def _fallback_indent_py(code: str) -> str:
    """Basic indentation heuristic for invalid-yet partially-valid Python."""
    lines = code.split("\n")
    result = []
    indent = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append("")
            continue
        # De-indent before dedent-trigger lines
        if any(stripped.startswith(kw) for kw in ("else:", "elif ", "except ", "except:", "finally:", "case ")):
            indent = max(indent - 1, 0)
        result.append("    " * indent + stripped)
        # Increase indent after block-start lines
        if stripped.endswith(":") and not stripped.startswith(("#", "import ", "from ")):
            # Don't indent for single-line suites
            indent += 1
    return "\n".join(result)

def _fmt_js(code: str) -> dict:
    try:
        lines = code.split("\n")
        result_lines = []
        indent = 0
        for raw_line in lines:
            stripped = raw_line.strip()
            if not stripped:
                result_lines.append("")
                continue
            # closing brace dedent
            close_count = stripped.count("}")
            if close_count > 0 and indent > 0:
                indent = max(indent - close_count, 0)
            result_lines.append("  " * indent + stripped)
            # opening brace indent (approximate)
            open_count = stripped.count("{")
            indent += open_count
            # Adjust for single-line blocks like `{ key: val }`
            # Closing brace on same line as open
            close_on_same = stripped.count("}")
            if close_on_same > 0 and open_count > 0:
                indent = indent - open_count + max(open_count - close_on_same, 0)
        return {"ok": True, "result": "\n".join(result_lines)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _fmt_html(code: str) -> dict:
    try:
        # Very basic HTML indent based on tags
        lines = code.split("\n")
        result = []
        indent = 0
        # self-closing tags
        void_tags = {"br", "hr", "img", "input", "meta", "link", "area", "base", "col",
                     "embed", "source", "track", "wbr", "!doctype"}
        tag_re = re.compile(r"</?\s*(\w+)")
        for raw_line in lines:
            stripped = raw_line.strip()
            if not stripped:
                result.append("")
                continue
            tags = tag_re.findall(stripped.lower())
            # Count closing tags before opening
            closing = sum(1 for t in tags if stripped.lower().count(f"</{t}") > 0)
            # Adjust indent
            if closing > 0:
                indent = max(indent - closing, 0)
            result.append("  " * indent + stripped)
            # Opening tags (non-void, non-closing)
            openings = []
            for m in re.finditer(r"<\s*(\w+)", stripped.lower()):
                tag = m.group(1)
                if tag not in void_tags and not stripped[m.start():].startswith(f"</"):
                    openings.append(tag)
            indent += len(openings)
        return {"ok": True, "result": "\n".join(result)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

_FORMATTERS = {
    "json": _fmt_json,
    "py": _fmt_python,
    "js": _fmt_js,
    "html": _fmt_html,
}

def do_format(params: dict) -> dict:
    code = params.get("code", "")
    lang = _detect_lang(params.get("lang", "py"))
    fn = _FORMATTERS.get(lang)
    if not fn:
        return {"ok": False, "error": f"不支持的语言: {lang}", "supported": list(_FORMATTERS.keys())}
    return fn(code)


# ═══════════════════════════════════════════
# 2. minify — 代码压缩
# ═══════════════════════════════════════════

def _minify_json(code: str) -> dict:
    try:
        obj = json.loads(code)
        return {"ok": True, "result": json.dumps(obj, separators=(",", ":"), ensure_ascii=False)}
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"JSON解析失败: {e}"}

def _minify_python(code: str) -> dict:
    """Remove comments and docstrings using tokenize, collapse blank lines."""
    try:
        result = []
        prev_type = None
        prev_end = (0, 0)
        for tok in tokenize.generate_tokens(io.StringIO(code).readline):
            ttype, tstr, start, end, _line = tok
            if ttype in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE):
                # Keep NEWLINE but compress consecutive
                if ttype == tokenize.NEWLINE:
                    if prev_type == tokenize.NEWLINE:
                        continue
                elif ttype == tokenize.NL:
                    continue
                if ttype != tokenize.NEWLINE:
                    prev_type = ttype
                    continue
            # Remove docstrings (standalone string expressions)
            if ttype == tokenize.STRING and (prev_type in (None, tokenize.NEWLINE, tokenize.INDENT, tokenize.NL)):
                prev_type = ttype
                continue
            # Remove indentation whitespace
            if ttype == tokenize.INDENT or ttype == tokenize.DEDENT:
                prev_type = ttype
                continue
            # Add needed space
            if result and prev_type not in (None, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT):
                # Check if we need a space separator
                prev_str = result[-1]
                if prev_str and not prev_str[-1].isspace() and tstr and not tstr[0].isspace():
                    if not (prev_str[-1] in "([{" or tstr[0] in ")]},:;." or prev_str[-1] in ",:;."):
                        result.append(" ")
            result.append(tstr)
            prev_type = ttype
        return {"ok": True, "result": "".join(result).strip()}
    except Exception as e:
        return {"ok": False, "error": f"Python压缩失败: {e}"}

_SL_COMMENT_RE = re.compile(r"//.*$", re.MULTILINE)
_ML_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)

def _minify_js(code: str) -> dict:
    try:
        # Remove comments
        code = _ML_COMMENT_RE.sub("", code)
        code = _SL_COMMENT_RE.sub("", code)
        # Collapse whitespace while preserving string content
        result = []
        in_str = False
        str_char = ""
        in_single_comment = False
        i = 0
        n = len(code)
        while i < n:
            ch = code[i]
            if in_str:
                result.append(ch)
                if ch == "\\":
                    if i + 1 < n:
                        result.append(code[i + 1])
                        i += 1
                elif ch == str_char:
                    in_str = False
            elif ch in _Q:
                in_str = True
                str_char = ch
                result.append(ch)
            elif ch.isspace():
                # Collapse multiple spaces to single space
                if result and not result[-1].isspace():
                    result.append(" ")
            else:
                result.append(ch)
            i += 1
        compressed = "".join(result).strip()
        # Remove unnecessary spaces around brackets
        compressed = re.sub(r"\s*([{}();,:])\s*", r"\1", compressed)
        compressed = re.sub(r"([+\-*/<>=!&|?])\s+", r"\1", compressed)
        compressed = re.sub(r"\s+([+\-*/<>=!&|?])", r"\1", compressed)
        return {"ok": True, "result": compressed}
    except Exception as e:
        return {"ok": False, "error": f"JS压缩失败: {e}"}

_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

def _minify_html(code: str) -> dict:
    try:
        code = _HTML_COMMENT_RE.sub("", code)
        # Collapse whitespace, preserve pre tags
        # Simple approach: remove newlines and collapse spaces
        result = []
        in_tag = False
        in_pre = False
        i = 0
        n = len(code)
        while i < n:
            ch = code[i]
            if code[i:i+5].lower() == "<pre>" or code[i:i+5].lower() == "<pre ":
                in_pre = True
            elif code[i:i+6].lower() == "</pre>":
                in_pre = False
            if in_pre:
                result.append(ch)
            elif ch == "<":
                in_tag = True
                result.append(ch)
            elif ch == ">":
                in_tag = False
                result.append(ch)
            elif in_tag:
                result.append(ch)
            elif ch.isspace():
                if result and not result[-1].isspace():
                    result.append(" ")
            else:
                result.append(ch)
            i += 1
        compressed = "".join(result).strip()
        # Remove spaces between tags
        compressed = re.sub(r">\s+<", "><", compressed)
        return {"ok": True, "result": compressed}
    except Exception as e:
        return {"ok": False, "error": f"HTML压缩失败: {e}"}

_MINIFIERS = {
    "json": _minify_json,
    "py": _minify_python,
    "js": _minify_js,
    "html": _minify_html,
}

def do_minify(params: dict) -> dict:
    code = params.get("code", "")
    lang = _detect_lang(params.get("lang", "py"))
    fn = _MINIFIERS.get(lang)
    if not fn:
        return {"ok": False, "error": f"不支持的语言: {lang}", "supported": list(_MINIFIERS.keys())}
    return fn(code)


# ═══════════════════════════════════════════
# 3. count — 代码统计
# ═══════════════════════════════════════════

def _count_json(code: str) -> dict:
    try:
        obj = json.loads(code)
        lines = len(code.split("\n"))
        chars = len(code)

        def _count_keys(o, depth=0):
            if isinstance(o, dict):
                return len(o) + sum(_count_keys(v, depth + 1) for v in o.values())
            if isinstance(o, list):
                return sum(_count_keys(v, depth + 1) for v in o)
            return 0

        def _count_items(o):
            if isinstance(o, dict):
                return 1 + sum(_count_items(v) for v in o.values())
            if isinstance(o, list):
                return 1 + sum(_count_items(v) for v in o)
            return 1

        keys = _count_keys(obj)
        items = _count_items(obj)
        return {"ok": True, "stats": {"lines": lines, "chars": chars, "keys": keys, "nodes": items}}
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"JSON解析失败: {e}"}

def _count_python(code: str) -> dict:
    try:
        tree = ast.parse(code)
        lines = len(code.split("\n"))
        chars = len(code)
        funcs = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
        classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
        imports = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)))
        # blank lines
        blank = sum(1 for ln in code.split("\n") if ln.strip() == "")
        comment_lines = sum(1 for ln in code.split("\n") if ln.strip().startswith("#"))
        return {"ok": True, "stats": {
            "lines": lines, "chars": chars, "functions": funcs, "classes": classes,
            "imports": imports, "blank_lines": blank, "comment_lines": comment_lines,
        }}
    except SyntaxError as e:
        lines = len(code.split("\n"))
        chars = len(code)
        blank = sum(1 for ln in code.split("\n") if ln.strip() == "")
        comment_lines = sum(1 for ln in code.split("\n") if ln.strip().startswith("#"))
        funcs = len(re.findall(r"^\s*def\s+\w+", code, re.MULTILINE))
        classes = len(re.findall(r"^\s*class\s+\w+", code, re.MULTILINE))
        return {"ok": True, "stats": {
            "lines": lines, "chars": chars, "functions": funcs, "classes": classes,
            "blank_lines": blank, "comment_lines": comment_lines,
        }, "warning": f"AST解析失败({e})，使用正则近似统计"}

def _count_js(code: str) -> dict:
    lines = len(code.split("\n"))
    chars = len(code)
    blank = sum(1 for ln in code.split("\n") if ln.strip() == "")
    comment_lines = len(_SL_COMMENT_RE.findall(code)) + sum(len(m.split("\n")) for m in _ML_COMMENT_RE.findall(code))
    # Function declarations: function name(, name = function, name = (args) =>, name(args) {
    funcs = len(re.findall(r"(?:function\s+\w+|(?:\w+\s*[:=]\s*)?function\s*\(|\w+\s*[:=]\s*(?:\([^)]*\)|[^=]\S+)\s*=>|\b\w+\s*\([^)]*\)\s*\{)", code))
    classes_decl = len(re.findall(r"class\s+\w+", code))
    return {"ok": True, "stats": {
        "lines": lines, "chars": chars, "functions": funcs, "classes": classes_decl,
        "blank_lines": blank, "comment_lines": comment_lines,
    }}

def _count_html(code: str) -> dict:
    lines = len(code.split("\n"))
    chars = len(code)
    blank = sum(1 for ln in code.split("\n") if ln.strip() == "")
    comments = len(_HTML_COMMENT_RE.findall(code))
    tags = len(re.findall(r"<\s*(\w+)", code))
    scripts = len(re.findall(r"<\s*script\b", code, re.IGNORECASE))
    styles = len(re.findall(r"<\s*style\b", code, re.IGNORECASE))
    return {"ok": True, "stats": {
        "lines": lines, "chars": chars, "tags": tags,
        "scripts": scripts, "styles": styles,
        "blank_lines": blank, "html_comments": comments,
    }}

_COUNTERS = {
    "json": _count_json,
    "py": _count_python,
    "js": _count_js,
    "html": _count_html,
}

def do_count(params: dict) -> dict:
    code = params.get("code", "")
    lang = _detect_lang(params.get("lang", "py"))
    fn = _COUNTERS.get(lang)
    if not fn:
        return {"ok": False, "error": f"不支持的语言: {lang}", "supported": list(_COUNTERS.keys())}
    return fn(code)


# ═══════════════════════════════════════════
# 4. lint — 基础代码检查
# ═══════════════════════════════════════════

def _lint_generic(code: str, lang: str = "py") -> dict:
    """Common lint checks across all languages."""
    issues = []
    warnings = []
    lines = code.split("\n")

    # Check trailing whitespace
    for i, line in enumerate(lines, 1):
        if line.rstrip() != line and line.strip():
            issues.append(f"行{i}: 行尾空白")
            if len(issues) >= 10:
                issues.append("... (超过10条，已截断)")
                break

    # Check mixed tabs and spaces
    has_tabs = any("\t" in ln for ln in lines)
    has_spaces = any(ln.startswith(" ") for ln in lines if ln.strip())
    if has_tabs and has_spaces:
        warnings.append("文件混用了Tab和空格缩进")

    # Check very long lines
    long_lines = [(i, len(ln)) for i, ln in enumerate(lines, 1) if len(ln) > 120]
    if long_lines:
        top3 = long_lines[:3]
        for ln_num, ln_len in top3:
            warnings.append(f"行{ln_num}: 超长行 ({ln_len}字符)")
        if len(long_lines) > 3:
            warnings.append(f"... 还有 {len(long_lines)-3} 行超过120字符")

    # Check no trailing newline
    if code and not code.endswith("\n"):
        warnings.append("文件末尾缺少换行符")

    # Check bracket balance
    bk = _check_brackets(code)
    if not bk["balanced"]:
        issues.extend(bk["issues"])

    return issues, warnings

def _lint_json(code: str) -> dict:
    issues, warnings = _lint_generic(code, "json")
    try:
        json.loads(code)
    except json.JSONDecodeError as e:
        issues.append(f"JSON语法错误: {e}")
    # Check for duplicate keys
    try:
        obj = json.loads(code)
        # Use a custom decoder to catch duplicates
        def _dup_check(pairs):
            seen = {}
            for k, v in pairs:
                if k in seen:
                    issues.append(f"重复的键: '{k}'")
                seen[k] = v
            return seen
        json.loads(code, object_pairs_hook=_dup_check)
    except Exception:
        pass
    return {"ok": True, "issues": issues, "warnings": warnings, "passed": len(issues) == 0}

def _lint_python(code: str) -> dict:
    issues, warnings = _lint_generic(code, "py")
    try:
        ast.parse(code)
    except SyntaxError as e:
        issues.append(f"Python语法错误: 行{e.lineno or '?'}: {e.msg}")
    # Check bare except
    if re.search(r"\bexcept\s*:", code):
        warnings.append("使用了裸 except: (建议指定异常类型)")
    # Check mutable default args
    for m in re.finditer(r"def\s+\w+\s*\([^)]*\)", code):
        sig = m.group()
        if re.search(r"=\s*(\[\]|\{\}|set\(\))", sig):
            warnings.append(f"函数默认参数使用了可变对象: {sig[:60]}")
    # Check for print statements (Python 2 style? no, just info)
    return {"ok": True, "issues": issues, "warnings": warnings, "passed": len(issues) == 0}

def _lint_js(code: str) -> dict:
    issues, warnings = _lint_generic(code, "js")
    # Check missing semicolons (heuristic: lines ending without ; { } or comment)
    for i, ln in enumerate(code.split("\n"), 1):
        stripped = ln.strip()
        if stripped and not stripped.startswith("//") and not stripped.startswith("/*"):
            if not stripped.endswith((";", "{", "}", "*/")) and not stripped.endswith(",") and not stripped.endswith(":"):
                # Heuristic: if next line starts with ( or [ it's likely ASI
                pass  # too many false positives with ASI, just skip this
    # Check var usage (suggest let/const)
    if re.search(r"\bvar\s+\w", code):
        warnings.append("使用了 'var' (建议使用 'let' 或 'const')")
    # Check == vs ===
    eqs = re.findall(r"[^=!<>]==(?!=)", code)
    if eqs:
        warnings.append(f"使用了 '==' 而非 '===' ({len(eqs)}处)")
    return {"ok": True, "issues": issues, "warnings": warnings, "passed": len(issues) == 0}

def _lint_html(code: str) -> dict:
    issues, warnings = _lint_generic(code, "html")
    # Check unclosed tags (simple heuristic)
    void_tags = {"br", "hr", "img", "input", "meta", "link", "area", "base", "col",
                 "embed", "source", "track", "wbr"}
    open_tags = re.findall(r"<\s*(\w+)", code.lower())
    close_tags = re.findall(r"</\s*(\w+)", code.lower())
    open_count = collections.Counter(t for t in open_tags if t not in void_tags)
    close_count = collections.Counter(close_tags)
    for tag in open_count:
        if open_count[tag] > close_count.get(tag, 0):
            warnings.append(f"标签 '<{tag}>' 可能未闭合 (打开{open_count[tag]}次, 关闭{close_count.get(tag,0)}次)")
    # Missing alt on img
    if re.search(r"<img\b(?![^>]*\balt\s*=)[^>]*>", code, re.IGNORECASE):
        warnings.append("img 标签缺少 alt 属性")
    return {"ok": True, "issues": issues, "warnings": warnings, "passed": len(issues) == 0}

_LINTERS = {
    "json": _lint_json,
    "py": _lint_python,
    "js": _lint_js,
    "html": _lint_html,
}

def do_lint(params: dict) -> dict:
    code = params.get("code", "")
    lang = _detect_lang(params.get("lang", "py"))
    fn = _LINTERS.get(lang)
    if not fn:
        return {"ok": False, "error": f"不支持的语言: {lang}", "supported": list(_LINTERS.keys())}
    return fn(code)


# ═══════════════════════════════════════════
# 5. ast — 打印 AST 结构
# ═══════════════════════════════════════════

def _ast_json(code: str) -> dict:
    try:
        obj = json.loads(code)
        def _describe(o, depth=0):
            if isinstance(o, dict):
                children = {k: _describe(v, depth + 1) for k, v in o.items()}
                return {"type": "Object", "keys": len(o), "children": children}
            if isinstance(o, list):
                children = [_describe(v, depth + 1) for v in o]
                return {"type": "Array", "length": len(o), "children": children}
            if isinstance(o, str):
                return {"type": "String", "value": o[:80] + ("..." if len(o) > 80 else "")}
            if isinstance(o, bool):
                return {"type": "Boolean", "value": o}
            if o is None:
                return {"type": "Null"}
            if isinstance(o, (int, float)):
                return {"type": "Number", "value": o}
            return {"type": type(o).__name__}
        return {"ok": True, "ast": _describe(obj)}
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"JSON解析失败: {e}"}

def _ast_python(code: str) -> dict:
    try:
        tree = ast.parse(code)
        # Use ast.dump for full structure, but also provide a friendlier version
        full_dump = ast.dump(tree, indent=2)

        def _simple_node(node, depth=0):
            kind = type(node).__name__
            info = {"kind": kind}
            if isinstance(node, ast.Module):
                info["body"] = [_simple_node(n, depth + 1) for n in node.body]
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                info["name"] = node.name
                info["args"] = [a.arg for a in node.args.args]
                info["body_len"] = len(node.body)
            elif isinstance(node, ast.ClassDef):
                info["name"] = node.name
                info["bases"] = [ast.unparse(b) for b in node.bases]
                info["body_len"] = len(node.body)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                info["names"] = [n.name for n in node.names]
            elif isinstance(node, ast.Assign):
                info["targets"] = [ast.unparse(t) for t in node.targets]
            elif isinstance(node, ast.Expr):
                info["value"] = ast.unparse(node.value)[:100]
            elif isinstance(node, ast.Call):
                info["func"] = ast.unparse(node.func)
            elif isinstance(node, ast.Constant):
                info["value"] = repr(node.value)[:100]
            elif isinstance(node, ast.Name):
                info["id"] = node.id
            elif isinstance(node, ast.Return):
                if node.value:
                    info["value"] = ast.unparse(node.value)[:100]
            elif isinstance(node, ast.If):
                info["test"] = ast.unparse(node.test)[:100]
                info["body_len"] = len(node.body)
                info["orelse_len"] = len(node.orelse)
            elif isinstance(node, ast.For):
                info["target"] = ast.unparse(node.target)
                info["iter"] = ast.unparse(node.iter)[:100]
                info["body_len"] = len(node.body)
            elif isinstance(node, ast.While):
                info["test"] = ast.unparse(node.test)[:100]
                info["body_len"] = len(node.body)
            elif isinstance(node, ast.ImportFrom):
                info["module"] = node.module
                info["names"] = [n.name for n in node.names]
            return info

        return {"ok": True, "raw": full_dump, "simple": _simple_node(tree)}
    except SyntaxError as e:
        return {"ok": False, "error": f"Python语法错误: 行{e.lineno or '?'}: {e.msg}"}

def _ast_js(code: str) -> dict:
    """Best-effort JS AST via regex-based structure analysis."""
    try:
        tree = {"type": "Program", "body": []}
        # Extract top-level constructs
        # Functions
        for m in re.finditer(r"(?:function\s+(\w+)\s*\(([^)]*)\)|(?:const|let|var)\s+(\w+)\s*=\s*(?:function\s*\(([^)]*)\)|\(([^)]*)\)\s*=>))", code):
            if m.group(1):
                tree["body"].append({"type": "FunctionDeclaration", "name": m.group(1), "params": m.group(2)})
            else:
                name = m.group(3)
                params = m.group(4) or m.group(5)
                tree["body"].append({"type": "FunctionExpression", "name": name, "params": params})
        # Classes
        for m in re.finditer(r"class\s+(\w+)(?:\s+extends\s+(\w+))?", code):
            tree["body"].append({"type": "ClassDeclaration", "name": m.group(1), "extends": m.group(2)})
        # Imports
        for m in re.finditer(r"import\s+(?:{[^}]*}|\*\s+as\s+\w+|\w+)\s+from\s+['\"]([^'\"]+)['\"]", code):
            tree["body"].append({"type": "ImportDeclaration", "source": m.group(1)})
        # Exports
        for m in re.finditer(r"export\s+(?:default\s+)?(?:function|class|const|let|var)\s+(\w+)", code):
            tree["body"].append({"type": "ExportDeclaration", "name": m.group(1)})
        return {"ok": True, "simple": tree, "note": "JS AST为近似解析（Python标准库无JS解析器）"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _ast_html(code: str) -> dict:
    """Best-effort HTML DOM tree."""
    try:
        tree = {"type": "Document", "children": []}
        tag_re = re.compile(r"<(/?)(\w+)([^>]*)>", re.IGNORECASE)
        void_tags = {"br", "hr", "img", "input", "meta", "link", "area", "base", "col",
                     "embed", "source", "track", "wbr"}
        stack = [tree]
        for m in tag_re.finditer(code):
            is_close = bool(m.group(1))
            tag = m.group(2).lower()
            attrs_raw = m.group(3).strip()
            if is_close:
                # Find matching open in stack
                for i in range(len(stack) - 1, -1, -1):
                    if stack[i].get("tag") == tag:
                        stack = stack[:i]
                        break
            else:
                node = {"type": "Element", "tag": tag}
                if attrs_raw:
                    attrs = re.findall(r'(\w[\w-]*)\s*=\s*"([^"]*)"', attrs_raw)
                    node["attrs"] = {k: v for k, v in attrs}
                node["children"] = []
                stack[-1]["children"].append(node)
                if tag not in void_tags:
                    stack.append(node)
        return {"ok": True, "simple": tree, "note": "HTML AST为近似解析（Python标准库无HTML解析器）"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

_ASTERS = {
    "json": _ast_json,
    "py": _ast_python,
    "js": _ast_js,
    "html": _ast_html,
}

def do_ast(params: dict) -> dict:
    code = params.get("code", "")
    lang = _detect_lang(params.get("lang", "py"))
    fn = _ASTERS.get(lang)
    if not fn:
        return {"ok": False, "error": f"不支持的语言: {lang}", "supported": list(_ASTERS.keys())}
    return fn(code)


# ═══════════════════════════════════════════
# Handler 注册
# ═══════════════════════════════════════════

HANDLERS = {
    "format": do_format,
    "minify": do_minify,
    "count":  do_count,
    "lint":   do_lint,
    "ast":    do_ast,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else ""
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except Exception:
            pass
    handler = HANDLERS.get(action)
    if handler:
        result = handler(params)
    else:
        result = {
            "ok": False,
            "error": f"未知工具: {action}",
            "available": list(HANDLERS.keys()),
        }
    print(json.dumps(result, ensure_ascii=False, default=str))
