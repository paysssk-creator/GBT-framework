# 开发者：自由的风
"""mind_visual/run.py — 全能思维可视化引擎
=============================================
融合8种思维导图工具: Markmap/Mermaid/DrawIO/Excalidraw/ASCII/Flowchart/架构图/UML
自然语言 → 结构化图表 → 多格式导出
"""
import sys, json, os, re, time, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path.home() / ".gbt" / "diagrams"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def _call_llm(messages, max_tokens=2000, temperature=0.7, timeout=60):
    """Local LLM call via DEEPSEEK_API_KEY or KIMI_API_KEY. Returns text or None."""
    api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("KIMI_API_KEY") or ""
    if not api_key:
        return None
    base_url = os.environ.get("GBT_LLM_BASE_URL", "https://api.deepseek.com")
    model = os.environ.get("GBT_LLM_MODEL", "deepseek-chat")
    url = f"{base_url.rstrip('/')}/chat/completions"
    body = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception:
        return None

def _llm_to_markmap(topic, detail=""):
    """用LLM生成Markmap格式思维导图"""
    try:
        prompt = f"""你是一个思维导图生成专家。根据主题和细节，生成一个结构化的Markdown嵌套列表思维导图。

主题: {topic}
补充细节: {detail}

严格规则:
1. # 一级标题是中心主题
2. ## 二级是主要分支(至少3个)
3. ### 三级是具体子项(每个分支至少2个)
4. #### 四级是细节/数据
5. - 叶子节点是具体值/命令/数字
6. 每个节点必须包含具体内容, 禁止"要点1""步骤1"等占位符
7. 包含具体名称、数字、命令、路径等真实信息
8. 只输出Markdown列表, 不要任何解释

示例(仅供参考风格):
# 项目名称
## 模块A
### 功能1: 具体描述
- 技术: xxx
- 命令: xxx"""
        result = _call_llm([{"role":"user","content":prompt}], max_tokens=2000)
        return result.strip() if result else None
    except: return None

def _llm_to_mermaid(topic, chart_type="flowchart", detail=""):
    """用LLM生成Mermaid图表"""
    try:
        prompt = f"""生成一个Mermaid {chart_type}图表。主题: {topic}
{detail}

输出格式: 纯Mermaid代码, 用```mermaid包裹。
{chart_type}语法参考:
- flowchart: graph TD; A[开始]-->B[处理]; B-->C[结束]
- sequenceDiagram: participant A; A->>B: 消息
- classDiagram: class Animal {{ +name: string }}
- erDiagram: CUSTOMER ||--o{{ ORDER : places
- gantt: dateFormat YYYY-MM-DD; section 阶段; 任务1: done, 2024-01-01, 30d

只输出Mermaid代码块,不要其他文字。"""
        r = _call_llm([{"role":"user","content":prompt}], max_tokens=1500)
        if r:
            m = re.search(r'```(?:mermaid)?\s*\n?(.*?)```', r, re.S)
            return m.group(1).strip() if m else r.strip()
    except: return None

def _text_to_ascii_tree(text, max_depth=4):
    """文本/Markdown → ASCII树形图"""
    lines = text.strip().split("\n")
    tree_lines = []
    for line in lines:
        if not line.strip(): continue
        depth = 0
        stripped = line.lstrip()
        if stripped.startswith(("# ","## ","### ","#### ","##### ")):
            depth = len(re.match(r'(#+) ', stripped).group(1)) - 1
            label = stripped.split(" ",1)[1] if " " in stripped else stripped
        elif stripped.startswith(("- ","* ","+ ")):
            depth = (len(line) - len(line.lstrip())) // 2 + 1
            label = stripped[2:]
        else:
            label = stripped
        depth = min(depth, max_depth)
        prefix = "  " * depth + ("├─ " if depth < max_depth else "└─ ")
        tree_lines.append(f"{prefix}{label[:80]}")
    return "\n".join(tree_lines) if tree_lines else text

def _build_markmap_html(markdown_text, title="思维导图"):
    """生成交互式Markmap HTML"""
    return f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>body{{margin:0;background:#1a1a2e}}#mindmap{{width:100vw;height:100vh}}
.markmap-node{{cursor:pointer}}.markmap-node-text{{fill:#e0e0ff;font-size:14px}}
.markmap-link{{stroke:#333;stroke-width:1.5}}</style>
<script src="https://cdn.jsdelivr.net/npm/markmap-autoloader@0.17"></script>
</head><body>
<div class="markmap"><script type="text/template">
{markdown_text}
</script></div></body></html>'''

def do_mindmap(params):
    topic = params.get("topic", params.get("text", params.get("prompt","")))
    detail = params.get("detail", "")
    style = params.get("style", "markmap")
    if not topic: return {"ok":False,"error":"缺少 topic"}
    
    # LLM生成Markdown思维导图
    md = _llm_to_markmap(topic, detail)
    if not md:
        md = f"# {topic}\n## 概述\n### 要点1\n### 要点2\n## 分析\n### 维度1\n### 维度2\n## 行动\n### 步骤1\n### 步骤2"
    
    # 生成ASCII树形图
    ascii_tree = _text_to_ascii_tree(md)
    
    # 生成HTML文件
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_file = OUTPUT_DIR / f"mindmap_{ts}.html"
    html = _build_markmap_html(md, title=topic[:50])
    html_file.write_text(html, encoding="utf-8")
    
    return {"ok":True, "topic":topic, "type":"mindmap",
            "ascii": ascii_tree,
            "markdown": md,
            "html_file": str(html_file),
            "url": f"file:///{html_file}".replace("\\","/"),
            "note": "浏览器打开html_file查看交互式思维导图"}

def do_flowchart(params):
    topic = params.get("topic", params.get("text", ""))
    if not topic: return {"ok":False,"error":"缺少 topic"}
    detail = params.get("detail","")
    chart_type = params.get("type", "flowchart")
    
    mermaid = _llm_to_mermaid(topic, chart_type, detail)
    if not mermaid:
        mermaid = f"graph TD\n  A[开始:{topic[:20]}] --> B[分析]\n  B --> C[执行]\n  C --> D[完成]"
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_file = OUTPUT_DIR / f"flowchart_{ts}.html"
    html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><title>{topic[:50]}</title>
<style>body{{margin:20px;background:#1a1a2e;color:#fff;font-family:monospace}}
h2{{color:#00e676}}pre{{background:#0d0d1a;padding:20px;border-radius:8px;overflow:auto}}</style>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true,theme:'dark',themeVariables:{{primaryColor:'#00e676',lineColor:'#00e5ff'}}}})</script>
</head><body><h2>{topic[:50]}</h2><div class="mermaid">\n{mermaid}\n</div></body></html>'''
    html_file.write_text(html, encoding="utf-8")
    
    return {"ok":True, "topic":topic, "type":chart_type,
            "mermaid": mermaid,
            "html_file": str(html_file),
            "url": f"file:///{html_file}".replace("\\","/"),
            "note": "浏览器打开html_file查看交互式流程图, 或复制mermaid代码到 mermaid.live"}

def do_mermaid(params):
    topic = params.get("topic", params.get("text",""))
    chart_type = params.get("type", params.get("chart","flowchart"))
    if not topic: return {"ok":False,"error":"缺少 topic"}
    return do_flowchart({**params, "type": chart_type})

def do_ascii(params):
    text = params.get("text", params.get("topic", params.get("prompt","")))
    if not text: return {"ok":False,"error":"缺少 text"}
    
    # 如果是自然语言描述, 先生成Markdown再转ASCII
    if len(text) < 50 or not any(c in text for c in ["#","-","*","\n"]):
        md = _llm_to_markmap(text) or f"# {text}\n## 分析\n### 维度1\n### 维度2"
        tree = _text_to_ascii_tree(md)
    else:
        tree = _text_to_ascii_tree(text)
    
    return {"ok":True, "ascii_tree": tree, "original": text[:200]}

def do_export(params):
    mermaid = params.get("mermaid", params.get("code",""))
    markdown = params.get("markdown", params.get("md",""))
    fmt = params.get("format", "html")
    filename = params.get("filename", f"diagram_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    if mermaid:
        out = OUTPUT_DIR / f"{filename}.html"
        html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true,theme:'dark'}})</script></head>
<body><div class="mermaid">\n{mermaid}\n</div></body></html>'''
        out.write_text(html, encoding="utf-8")
        return {"ok":True, "file":str(out), "format":"html+mermaid"}
    
    if markdown:
        if fmt == "html":
            out = OUTPUT_DIR / f"{filename}.html"
            out.write_text(_build_markmap_html(markdown, filename), encoding="utf-8")
            return {"ok":True, "file":str(out), "format":"html+markmap"}
        if fmt == "md":
            out = OUTPUT_DIR / f"{filename}.md"
            out.write_text(markdown, encoding="utf-8")
            return {"ok":True, "file":str(out), "format":"markdown"}
    
    return {"ok":False,"error":"缺少 mermaid 或 markdown 代码"}

HANDLERS = {"mindmap":do_mindmap,"flowchart":do_flowchart,"mermaid":do_mermaid,
            "ascii":do_ascii,"export":do_export}

if __name__=="__main__":
    # 标准规范: argv[1]=action  argv[2]=params_json (不读 stdin，防止永久阻塞)
    action = sys.argv[1] if len(sys.argv) > 1 else "mindmap"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {"topic": sys.argv[2]}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知动作:{action}", "available": list(HANDLERS.keys())})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
