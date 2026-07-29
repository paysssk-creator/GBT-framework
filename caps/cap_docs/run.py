# 开发者：自由的风
"""cap_docs/run.py — API文档生成器
=================================
扫描所有 caps/*/capability.json，生成 Markdown / HTML 文档，支持关键字搜索。
"""
import sys, json, os, re
from pathlib import Path
from datetime import datetime

SANDBOX = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CAPS_DIR = Path(SANDBOX) / "caps"
DOCS_DIR = Path(SANDBOX) / "docs"
MD_PATH = DOCS_DIR / "caps_api.md"
HTML_PATH = DOCS_DIR / "caps_api.html"

def _scan_caps():
    """扫描所有 capability.json，返回按 id 排序的列表。"""
    caps = []
    for cap_dir in sorted(CAPS_DIR.iterdir()):
        if not cap_dir.is_dir():
            continue
        cap_json = cap_dir / "capability.json"
        if not cap_json.exists():
            continue
        try:
            data = json.loads(cap_json.read_text(encoding="utf-8"))
        except Exception:
            continue
        data["_dir"] = cap_dir.name
        caps.append(data)
    return caps


def _name(cap):
    """提取 cap 名称：优先 name → id → _dir"""
    return cap.get("name") or cap.get("id") or cap.get("_dir", "unknown")


def _version(cap):
    return cap.get("version", "")


def _risk(cap):
    return cap.get("risk") or cap.get("risk_level", "")


def _category(cap):
    return cap.get("category") or cap.get("domain", "")


def _description(cap):
    return cap.get("description", "")


def _actions(cap):
    """归一化 actions：返回 [(name, desc), ...]"""
    actions = cap.get("actions", {})
    if isinstance(actions, list):
        return [(a.get("name", "?"), a.get("description", "")) for a in actions]
    result = []
    for k, v in actions.items():
        if isinstance(v, dict):
            result.append((k, v.get("description", "")))
        else:
            result.append((k, str(v)))
    return result


def _triggers(cap):
    t = cap.get("triggers", {})
    if not t:
        return None
    keywords = t.get("keywords", [])
    intent = t.get("intent", "")
    examples = t.get("examples", [])
    return {"keywords": keywords, "intent": intent, "examples": examples}


def _generate_md(caps):
    """生成 Markdown 文档字符串。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Caps API 文档",
        "",
        f"> 自动生成于 {now}  ·  共 {len(caps)} 个能力模块",
        "",
        "---",
        "",
    ]

    for cap in caps:
        n = _name(cap)
        ver = _version(cap)
        risk = _risk(cap)
        cat = _category(cap)
        desc = _description(cap)
        acts = _actions(cap)
        trig = _triggers(cap)

        # header
        lines.append(f"## {n}")
        lines.append("")
        meta = []
        if ver:
            meta.append(f"**版本**: {ver}")
        if risk:
            meta.append(f"**风险**: `{risk}`")
        if cat:
            meta.append(f"**分类**: {cat}")
        if meta:
            lines.append(" | ".join(meta))
            lines.append("")
        if desc:
            lines.append(f"> {desc}")
            lines.append("")

        # actions table
        if acts:
            lines.append("### Actions")
            lines.append("")
            lines.append("| Action | Description |")
            lines.append("|--------|-------------|")
            for aname, adesc in acts:
                lines.append(f"| `{aname}` | {adesc} |")
            lines.append("")

        # triggers
        if trig:
            lines.append("### Triggers")
            lines.append("")
            if trig["intent"]:
                lines.append(f"- **Intent**: `{trig['intent']}`")
            if trig["keywords"]:
                kws = ", ".join(f"`{k}`" for k in trig["keywords"])
                lines.append(f"- **Keywords**: {kws}")
            if trig["examples"]:
                lines.append("- **Examples**:")
                for ex in trig["examples"]:
                    lines.append(f"  - {ex}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _md_to_html(md_text):
    """简易 Markdown → HTML 转换。"""
    # escape
    md_text = md_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    out = []
    in_table = False
    in_code = False

    for raw in md_text.split("\n"):
        line = raw.rstrip()

        # fenced code blocks (not used much here but be safe)
        if line.startswith("```"):
            in_code = not in_code
            out.append("</code></pre>" if not in_code else "<pre><code>")
            continue
        if in_code:
            out.append(line)
            continue

        # horizontal rule
        if line.strip() == "---":
            if in_table:
                out.append("</tbody></table>")
                in_table = False
            out.append("<hr>")
            continue

        # heading
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            if in_table:
                out.append("</tbody></table>")
                in_table = False
            level = len(m.group(1))
            txt = _inline_html(m.group(2))
            out.append(f"<h{level}>{txt}</h{level}>")
            continue

        # table row
        if "|" in line and line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().split("|")[1:-1]]
            if all(re.match(r"^[-:]+$", c) for c in cells):
                continue  # separator row
            if not in_table:
                out.append("<table><thead><tr>")
                out.append("".join(f"<th>{_inline_html(c)}</th>" for c in cells))
                out.append("</tr></thead><tbody>")
                in_table = True
            else:
                out.append("<tr>" + "".join(f"<td>{_inline_html(c)}</td>" for c in cells) + "</tr>")
            continue

        # blockquote
        if line.startswith("> "):
            txt = _inline_html(line[2:])
            out.append(f"<blockquote>{txt}</blockquote>")
            continue

        # list item
        m = re.match(r"^(\s*)(-|\d+\.)\s+(.+)$", line)
        if m:
            indent = len(m.group(1))
            tag = "ul" if m.group(2) == "-" else "ol"
            txt = _inline_html(m.group(3))
            out.append(f"{'  ' * indent}<li>{txt}</li>")
            continue

        # paragraph (non-empty)
        if line.strip():
            out.append(f"<p>{_inline_html(line)}</p>")
        else:
            out.append("")

    if in_table:
        out.append("</tbody></table>")

    body = "\n".join(out)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Caps API 文档</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
       max-width: 960px; margin: 0 auto; padding: 2rem; line-height: 1.6;
       color: #1a1a2e; background: #f8f9fa; }}
h1 {{ border-bottom: 2px solid #4a90d9; padding-bottom: 0.5rem; }}
h2 {{ color: #2c3e50; margin-top: 2rem; border-bottom: 1px solid #ddd; }}
h3 {{ color: #555; }}
table {{ border-collapse: collapse; width: 100%; margin: 0.5rem 0 1rem; }}
th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
th {{ background: #4a90d9; color: white; }}
tr:nth-child(even) {{ background: #f2f2f2; }}
code {{ background: #e8e8e8; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }}
blockquote {{ border-left: 4px solid #4a90d9; padding-left: 1rem; color: #666; margin: 0.5rem 0; }}
hr {{ border: none; border-top: 1px solid #ddd; margin: 1.5rem 0; }}
</style>
</head>
<body>
{body}
</body>
</html>"""


def _inline_html(text):
    """行内 Markdown → HTML：处理 **bold** `code` 等。"""
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    return text


def do_generate(params):
    """扫描所有 caps 并生成 docs/caps_api.md"""
    caps = _scan_caps()
    if not caps:
        return {"ok": False, "error": "未找到任何 capability.json"}
    md = _generate_md(caps)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    MD_PATH.write_text(md, encoding="utf-8")
    return {"ok": True, "path": str(MD_PATH), "caps_count": len(caps), "size_bytes": len(md)}


def do_generate_html(params):
    """从生成的 md 生成 docs/caps_api.html；若 md 不存在则先生成。"""
    if not MD_PATH.exists():
        gen = do_generate(params)
        if not gen["ok"]:
            return gen
    md_text = MD_PATH.read_text(encoding="utf-8")
    html = _md_to_html(md_text)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    HTML_PATH.write_text(html, encoding="utf-8")
    return {"ok": True, "path": str(HTML_PATH), "size_bytes": len(html)}


def do_search(params):
    """按关键字搜索已生成的文档。"""
    keyword = params.get("keyword") or params.get("query") or params.get("q", "")
    if not keyword:
        return {"ok": False, "error": "缺少 keyword/query/q 参数"}
    limit = int(params.get("limit", params.get("n", 20)))

    if not MD_PATH.exists():
        gen = do_generate(params)
        if not gen["ok"]:
            return gen

    md_text = MD_PATH.read_text(encoding="utf-8")
    sections = re.split(r"\n(?=## )", md_text)
    matches = []

    kw_lower = keyword.lower()
    for sec in sections:
        if kw_lower in sec.lower():
            # extract heading line
            head_m = re.match(r"^## (.+)$", sec.strip(), re.MULTILINE)
            heading = head_m.group(1).strip() if head_m else "(unknown)"
            # extract description (blockquote)
            desc_m = re.search(r"^> (.+)$", sec, re.MULTILINE)
            desc = desc_m.group(1).strip() if desc_m else ""
            # find context lines around keyword match
            lines = sec.split("\n")
            ctx_lines = []
            for i, ln in enumerate(lines):
                if kw_lower in ln.lower():
                    ctx_lines.append(f"  L{i+1}: {ln.strip()[:120]}")
            matches.append({
                "cap": heading,
                "description": desc[:200],
                "matches": ctx_lines[:5],
                "match_count": len(ctx_lines),
            })
            if len(matches) >= limit:
                break

    return {
        "ok": True,
        "keyword": keyword,
        "total": len(matches),
        "results": matches,
    }


HANDLERS = {
    "generate": do_generate,
    "generate_html": do_generate_html,
    "search": do_search,
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "缺少 action",
                          "available": list(HANDLERS.keys())}, ensure_ascii=False, default=str))
        sys.exit(1)
    action = sys.argv[1]
    params = {}
    for a in sys.argv[2:]:
        if "=" in a:
            k, v = a.split("=", 1)
            params[k] = v
    handler = HANDLERS.get(action)
    if not handler:
        print(json.dumps({"ok": False, "error": f"未知动作: {action}",
                          "available": list(HANDLERS.keys())}, ensure_ascii=False, default=str))
        sys.exit(1)
    result = handler(params)
    print(json.dumps(result, ensure_ascii=False, default=str))
